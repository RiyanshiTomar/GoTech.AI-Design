import { api } from "./api.js";
import { store } from "./store.js";

export function initPlan() {
  const tabs = document.getElementById("floor-tabs");
  const canvas = document.getElementById("plan-canvas");
  const info = document.getElementById("plan-info");
  const dl = document.getElementById("plan-download");
  let floor = null, zoom = 1, key = "";

  const show = (text) => { canvas.innerHTML = `<div class="empty">${text}</div>`; };

  async function load(path) {
    const text = await fetch(api.fileUrl(path)).then((r) => r.text());
    canvas.innerHTML = text; zoom = 1; applyZoom();
    const svg = canvas.querySelector("svg");
    if (!svg) return;
    svg.addEventListener("click", (e) => {
      const g = e.target.closest('[id^="room-"]');
      canvas.querySelectorAll(".selected").forEach((n) => n.classList.remove("selected"));
      if (!g) { info.textContent = "Click a room for details."; return; }
      g.classList.add("selected");
      const name = g.querySelector(".room-name"), dim = g.querySelector(".room-dim");
      info.textContent = `${name ? name.textContent : g.id} - ${dim ? dim.textContent : ""} - ${g.dataset.kind}`;
    });
    dl.href = api.fileUrl(path);
    dl.download = path.split("/").pop();
  }

  function applyZoom() {
    const svg = canvas.querySelector("svg");
    if (svg) { svg.removeAttribute("width"); svg.removeAttribute("height"); svg.style.width = `${zoom * 100}%`; svg.style.height = `${zoom * 100}%`; }
  }

  store.subscribe((s) => {
    const files = (s.status && s.status.artifacts && s.status.artifacts.svg) || [];
    const stale = document.getElementById("stale-note");
    stale.hidden = !(s.status && s.status.stale && files.length);
    if (!files.length) { tabs.innerHTML = ""; show("No plan yet.<br>Describe a building in the chat. Invalid designs are never drawn."); return; }
    const sig = JSON.stringify(files) + (s.status.built_at || "");
    const ids = files.map((f) => f.match(/floorplan-(.+)\.svg$/)[1]);
    if (!floor || !ids.includes(floor)) floor = ids[0];
    tabs.innerHTML = "";
    ids.forEach((id) => {
      const b = document.createElement("button"); b.className = "seg-btn" + (id === floor ? " active" : "");
      b.textContent = (s.model && (s.model.floors.find((f) => f.id === id) || {}).name) || id;
      b.onclick = () => { floor = id; key = ""; store.set({}); };
      tabs.appendChild(b);
    });
    const k = sig + floor;
    if (k !== key) { key = k; load(files[ids.indexOf(floor)]); }
  });

  document.getElementById("plan-zoom-in").onclick = () => { zoom = Math.min(4, zoom * 1.25); applyZoom(); };
  document.getElementById("plan-zoom-out").onclick = () => { zoom = Math.max(0.3, zoom / 1.25); applyZoom(); };
  document.getElementById("plan-fit").onclick = () => { zoom = 1; applyZoom(); };
}
