"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, ContactShadows, useGLTF, Center, Bounds } from "@react-three/drei";
import { Component, Suspense, useMemo, useRef, useState, type ReactNode } from "react";
import * as THREE from "three";

interface Room {
  type: string;
  area_sqft?: number;
}

interface Viewer3DProps {
  spec?: { bhk: number; total_area_sqft: number; rooms: Room[] } | null;
  imageUrl?: string;
  modelUrl?: string;
}

/** Build a simple house layout from spec rooms - rooms arranged in a grid */
function HouseModel({ spec }: { spec: Viewer3DProps["spec"] }) {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  // Compute layout
  const rooms = useMemo(() => {
    if (!spec || spec.rooms.length === 0) {
      return [
        { type: "Living Room", x: 0, z: 0, w: 4, d: 4, color: "#fbbf24" },
        { type: "Bedroom", x: 4, z: 0, w: 4, d: 4, color: "#34d399" },
      ];
    }

    const list = spec.rooms.slice(0, 9);
    const cols = Math.ceil(Math.sqrt(list.length));
    const cellSize = 2.4;
    const palette = [
      "#fbbf24", "#34d399", "#60a5fa", "#f472b6",
      "#a78bfa", "#fb923c", "#22d3ee", "#facc15", "#4ade80",
    ];
    return list.map((r, i) => {
      const c = i % cols;
      const row = Math.floor(i / cols);
      const w = cellSize + (r.area_sqft ? Math.min(1.2, r.area_sqft / 200) : 0);
      const d = cellSize;
      return {
        type: r.type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        x: c * cellSize - (cols * cellSize) / 2 + cellSize / 2,
        z: row * cellSize - (cols * cellSize) / 2 + cellSize / 2,
        w,
        d,
        color: palette[i % palette.length],
      };
    });
  }, [spec]);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y =
        Math.sin(state.clock.elapsedTime * 0.15) * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Ground / plot */}
      <mesh receiveShadow position={[0, -0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color="#f3f0ea" />
      </mesh>

      {/* Plot border */}
      <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[9.5, 9.8, 64]} />
        <meshBasicMaterial color="#f59e0b" />
      </mesh>

      {/* Rooms as boxes */}
      {rooms.map((room, i) => (
        <group
          key={i}
          position={[room.x, 0, room.z]}
          onPointerOver={() => setHovered(room.type)}
          onPointerOut={() => setHovered(null)}
        >
          {/* Floor pad */}
          <mesh receiveShadow position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[room.w, room.d]} />
            <meshStandardMaterial color={room.color} opacity={0.4} transparent />
          </mesh>
          {/* Walls */}
          <mesh castShadow receiveShadow position={[0, 0.9, 0]}>
            <boxGeometry args={[room.w, 1.8, room.d]} />
            <meshStandardMaterial
              color={room.color}
              opacity={hovered === room.type ? 0.9 : 0.7}
              transparent
              roughness={0.6}
            />
          </mesh>
          {/* Roof outline */}
          <mesh position={[0, 1.81, 0]}>
            <boxGeometry args={[room.w + 0.05, 0.05, room.d + 0.05]} />
            <meshStandardMaterial color="#cfc8bb" />
          </mesh>
        </group>
      ))}

      {/* Trees / context */}
      <mesh position={[-7, 0.6, -7]} castShadow>
        <coneGeometry args={[0.5, 1.2, 8]} />
        <meshStandardMaterial color="#16a34a" />
      </mesh>
      <mesh position={[7, 0.6, -7]} castShadow>
        <coneGeometry args={[0.5, 1.2, 8]} />
        <meshStandardMaterial color="#16a34a" />
      </mesh>
    </group>
  );
}

function GlbModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return (
    <Bounds fit clip observe margin={1.3}>
      <Center>
        <primitive object={scene} />
      </Center>
    </Bounds>
  );
}

class Boundary extends Component<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

export default function Viewer3D({ spec, imageUrl, modelUrl }: Viewer3DProps) {
  return (
    <div className="relative w-full h-full bg-white overflow-hidden">
      <Canvas
        shadows
        camera={{ position: [10, 10, 12], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
      >
        <color attach="background" args={["#ffffff"]} />
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[10, 15, 8]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <Environment preset="sunset" />

        {modelUrl ? (
          <Boundary fallback={<HouseModel spec={spec ?? null} />}>
            <Suspense fallback={null}>
              <GlbModel url={modelUrl} />
            </Suspense>
          </Boundary>
        ) : (
          <HouseModel spec={spec ?? null} />
        )}

        <ContactShadows
          position={[0, 0, 0]}
          opacity={0.5}
          scale={20}
          blur={2}
          far={10}
        />

        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={1}
          maxDistance={60}
          maxPolarAngle={Math.PI / 2.1}
          autoRotate
          autoRotateSpeed={0.4}
        />

        {/* Ground grid */}
        <gridHelper args={[20, 20, "#d9d3c7", "#ece7dd"]} position={[0, 0, 0]} />
      </Canvas>

      {/* Overlay controls hint */}
      <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg bg-white/90 backdrop-blur text-xs text-ink/70 border border-line">
        🖱️ Drag to rotate · Scroll to zoom · Right-click to pan
      </div>
      {modelUrl ? (
        <div className="absolute top-4 right-4 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 backdrop-blur">
          ✓ 3D model generated from your plan
        </div>
      ) : imageUrl ? (
        <div className="absolute top-4 right-4 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 backdrop-blur">
          Showing layout from spec (AI 3D model unavailable)
        </div>
      ) : null}
    </div>
  );
}
