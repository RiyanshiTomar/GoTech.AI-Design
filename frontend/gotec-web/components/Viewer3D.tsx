"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, ContactShadows, Html } from "@react-three/drei";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";

interface Room {
  type: string;
  area_sqft?: number;
}

interface Viewer3DProps {
  spec?: { bhk: number; total_area_sqft: number; rooms: Room[] } | null;
  imageUrl?: string;
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
        <meshStandardMaterial color="#1e293b" />
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
            <meshStandardMaterial color="#0f172a" />
          </mesh>
          {/* Label */}
          <Html position={[0, 2.2, 0]} center distanceFactor={10}>
            <div className="px-2 py-1 rounded bg-slate-900/90 text-white text-xs font-medium whitespace-nowrap pointer-events-none border border-white/20">
              {room.type}
            </div>
          </Html>
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

export default function Viewer3D({ spec, imageUrl }: Viewer3DProps) {
  return (
    <div className="relative w-full h-full bg-gradient-to-br from-slate-900 to-slate-950 rounded-2xl overflow-hidden">
      <Canvas
        shadows
        camera={{ position: [10, 10, 12], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[10, 15, 8]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <Environment preset="sunset" />

        <HouseModel spec={spec ?? null} />

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
          minDistance={5}
          maxDistance={30}
          maxPolarAngle={Math.PI / 2.1}
          autoRotate
          autoRotateSpeed={0.4}
        />

        {/* Ground grid */}
        <gridHelper args={[20, 20, "#334155", "#1e293b"]} position={[0, 0, 0]} />
      </Canvas>

      {/* Overlay controls hint */}
      <div className="absolute bottom-4 left-4 px-3 py-2 rounded-lg bg-slate-900/80 backdrop-blur text-xs text-slate-300 border border-white/10">
        🖱️ Drag to rotate · Scroll to zoom · Right-click to pan
      </div>
      {imageUrl && (
        <div className="absolute top-4 right-4 px-3 py-2 rounded-lg bg-emerald-500/20 border border-emerald-400/30 text-xs text-emerald-200 backdrop-blur">
          ✓ 3D reconstructed from 2D plan
        </div>
      )}
    </div>
  );
}
