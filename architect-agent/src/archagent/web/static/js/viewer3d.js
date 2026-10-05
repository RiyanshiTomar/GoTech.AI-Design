import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { api } from "./api.js";
import { store } from "./store.js";

export function initViewer() {
  const host = document.getElementById("viewer");
  const vis = document.getElementById("floor-vis");
  const glbA = document.getElementById("glb-download"), ifcA = document.getElementById("ifc-download");

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  host.appendChild(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0xb8b8b0, 1.0));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4); sun.position.set(30, 60, 20); scene.add(sun);

  let model = null, home = null, key = "", floors = [];

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(host);

  function fit() {
    if (!model) return;
    const box = new THREE.Box3().setFromObject(model);
    const c = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
    const r = Math.max(size.x, size.y, size.z) * 1.1 || 10;
    camera.position.set(c.x + r, c.y + r * 0.9, c.z + r);
    camera.near = r / 100; camera.far = r * 50; camera.updateProjectionMatrix();
    controls.target.copy(c); controls.update();
    home = { pos: camera.position.clone(), target: c.clone() };
  }

  function buildVisibility() {
    vis.innerHTML = "";
    floors.forEach((f) => {
      const b = document.createElement("button"); b.className = "seg-btn active"; b.textContent = f.userData.floor_name || f.name;
      b.onclick = () => { f.visible = !f.visible; b.classList.toggle("active", f.visible); b.classList.toggle("off", !f.visible); };
      vis.appendChild(b);
    });
  }

  async function load(path) {
    const gltf = await new GLTFLoader().loadAsync(api.fileUrl(path));
    if (model) scene.remove(model);
    model = gltf.scene; scene.add(model);
    floors = [];
    model.traverse((n) => { if (n.name && n.name.startsWith("floor-")) floors.push(n); });
    floors.sort((a, b) => (a.userData.elevation || 0) - (b.userData.elevation || 0));
    const site = (model.getObjectByName("building") || {}).userData || {};
    addGround(site.site_width, site.site_depth);
    buildVisibility(); fit(); resize();
  }

  let ground = null;
  function addGround(w, d) {
    if (ground) scene.remove(ground);
    if (!w || !d) return;
    // plan (x, y) -> three (x, -y); site rectangle outline at z=0
    const pts = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]].map(([x, y]) => new THREE.Vector3(x, 0.01, -y));
    ground = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x9a9a92 }));
    scene.add(ground);
  }

  function showEmpty(on) {
    let e = host.querySelector(".empty");
    if (on && !e) { e = document.createElement("div"); e.className = "empty"; e.textContent = "No 3D model yet. It is generated only after the design validates."; host.appendChild(e); }
    if (!on && e) e.remove();
  }

  store.subscribe((s) => {
    const glb = s.status && s.status.artifacts && s.status.artifacts.glb;
    const ifc = s.status && s.status.artifacts && s.status.artifacts.ifc;
    if (glb) { glbA.href = api.fileUrl(glb); ifcA.href = ifc ? api.fileUrl(ifc) : "#"; glbA.download = "building.glb"; ifcA.download = "building.ifc"; }
    if (!glb) { showEmpty(true); if (model) { scene.remove(model); model = null; } return; }
    showEmpty(false);
    const k = glb + (s.status.built_at || "");
    if (k !== key) { key = k; load(glb).catch((e) => { host.insertAdjacentHTML("beforeend", `<div class="empty">Could not load 3D model: ${e.message}</div>`); }); }
  });

  document.getElementById("view-reset").onclick = () => { if (home) { camera.position.copy(home.pos); controls.target.copy(home.target); controls.update(); } };
  (function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
  return { resize };
}
