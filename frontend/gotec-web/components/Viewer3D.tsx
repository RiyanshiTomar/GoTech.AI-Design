"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF, Center, Bounds } from "@react-three/drei";
import { Component, Suspense, useEffect, useRef, type ReactNode } from "react";

interface Viewer3DProps {
  modelUrl?: string;
  /** names of floor nodes to hide, e.g. "floor-first-floor" */
  hiddenFloors?: string[];
  resetKey?: number;
}

function GlbModel({ url, hiddenFloors }: { url: string; hiddenFloors: string[] }) {
  const { scene } = useGLTF(url);
  useEffect(() => {
    scene.traverse((n) => {
      if (n.name.startsWith("floor-")) n.visible = !hiddenFloors.includes(n.name);
    });
  }, [scene, hiddenFloors]);
  return (
    <Bounds fit clip observe margin={1.3}>
      <Center>
        <primitive object={scene} />
      </Center>
    </Bounds>
  );
}

class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed
      ? <div className="absolute inset-0 flex items-center justify-center text-sm text-ink/60">Could not load the 3D model.</div>
      : this.props.children;
  }
}

export default function Viewer3D({ modelUrl, hiddenFloors = [], resetKey = 0 }: Viewer3DProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const controls = useRef<any>(null);
  useEffect(() => { controls.current?.reset(); }, [resetKey]);

  return (
    <div className="relative w-full h-full bg-white overflow-hidden">
      {modelUrl ? (
        <Canvas camera={{ position: [10, 10, 12], fov: 45 }} gl={{ antialias: true }}>
          <color attach="background" args={["#ffffff"]} />
          <hemisphereLight args={["#ffffff", "#b8b8b0", 1.0]} />
          <directionalLight position={[30, 60, 20]} intensity={1.4} />
          <Boundary>
            <Suspense fallback={null}>
              <GlbModel url={modelUrl} hiddenFloors={hiddenFloors} />
            </Suspense>
          </Boundary>
          <OrbitControls ref={controls} makeDefault enablePan enableZoom enableRotate maxPolarAngle={Math.PI / 2.05} />
        </Canvas>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-ink/50 px-6 text-center">
          No 3D model yet. It is built only after the design passes validation.
        </div>
      )}
      <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg bg-white/90 text-xs text-ink/70 border border-line">
        Drag to rotate · Scroll to zoom · Right-click to pan
      </div>
    </div>
  );
}
