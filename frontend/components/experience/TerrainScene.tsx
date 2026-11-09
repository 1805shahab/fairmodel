"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function Terrain() {
  const mesh = useRef<THREE.Mesh>(null);
  const playhead = useRef<THREE.Mesh>(null);
  const geometry = useMemo(() => {
    const columns = 84;
    const rows = 30;
    const positions: number[] = [];
    const colors: number[] = [];
    const indices: number[] = [];
    for (let row = 0; row <= rows; row += 1) {
      for (let col = 0; col <= columns; col += 1) {
        const x = (col / columns - 0.5) * 5.4;
        const z = (row / rows - 0.5) * 2.2;
        const pulse = Math.sin(col * 0.22) * Math.cos(row * 0.4) * 0.18;
        const ridge = Math.sin(col * 0.1 + row * 0.16) * 0.09;
        const y = Math.max(0.015, Math.abs(pulse + ridge));
        positions.push(x, y, z);
        const intensity = Math.min(1, y * 4.5);
        colors.push(0.24 + intensity * 0.28, 0.15 + intensity * 0.52, 0.48 + intensity * 0.44);
        if (row < rows && col < columns) {
          const current = row * (columns + 1) + col;
          indices.push(current, current + 1, current + columns + 1);
          indices.push(current + 1, current + columns + 2, current + columns + 1);
        }
      }
    }
    const result = new THREE.BufferGeometry();
    result.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    result.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    result.setIndex(indices);
    result.computeVertexNormals();
    return result;
  }, []);
  useFrame(({ clock }) => {
    if (playhead.current) {
      playhead.current.position.x = Math.sin(clock.elapsedTime * 0.24) * 2.5;
    }
  });
  return (
    <group rotation={[-0.18, 0, 0]}>
      <mesh ref={mesh} geometry={geometry}>
        <meshStandardMaterial vertexColors wireframe roughness={0.38} metalness={0.42} emissive="#482d8d" emissiveIntensity={0.18} />
      </mesh>
      <mesh ref={playhead} position={[0, 0.18, 0]}>
        <boxGeometry args={[0.012, 0.38, 2.5]} />
        <meshBasicMaterial color="#22e5ff" toneMapped={false} />
      </mesh>
      <gridHelper args={[5.4, 27, "#8b5cff", "#302640"]} position={[0, 0, 0]} />
    </group>
  );
}

export default function TerrainScene() {
  return (
    <div className="terrain-scene" aria-label="Rotatable 3D frequency terrain with moving audio playhead">
      <Canvas camera={{ position: [0, 2.8, 4.4], fov: 42 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: false, powerPreference: "low-power" }}>
        <ambientLight intensity={1.2} />
        <pointLight position={[1, 3, 2]} color="#22e5ff" intensity={20} />
        <Terrain />
        <OrbitControls enablePan={false} minDistance={3} maxDistance={7} minPolarAngle={0.45} maxPolarAngle={1.65} />
      </Canvas>
    </div>
  );
}
