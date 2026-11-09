"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Bloom, ChromaticAberration, EffectComposer, Vignette } from "@react-three/postprocessing";
import { OrbitControls, Sparkles } from "@react-three/drei";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useFairModel } from "@/store/fairmodel-store";

const vertexShader = `
  uniform float uTime;
  uniform float uAudio;
  uniform float uPulse;
  varying float vEnergy;
  varying vec3 vNormal;
  void main() {
    vec3 p = position;
    float wave = sin(position.x * 8.0 + uTime * 1.4)
      * cos(position.y * 7.0 - uTime * 1.1)
      * sin(position.z * 6.0 + uTime * 0.8);
    float breath = sin(uTime * 1.1) * 0.025;
    float displacement = wave * (0.025 + uAudio * 0.18 + uPulse * 0.11) + breath;
    p += normal * displacement;
    vEnergy = clamp(abs(wave) + uAudio * 1.4 + uPulse * 0.6, 0.0, 1.4);
    vNormal = normal;
    vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
    gl_PointSize = (0.85 + vEnergy * 1.1) * (11.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fragmentShader = `
  uniform float uBreach;
  varying float vEnergy;
  varying vec3 vNormal;
  void main() {
    vec2 centered = gl_PointCoord - 0.5;
    float circle = 1.0 - smoothstep(0.23, 0.5, length(centered));
    if (circle < 0.08) discard;
    vec3 violet = vec3(0.55, 0.31, 1.0);
    vec3 cyan = vec3(0.13, 0.87, 1.0);
    vec3 red = vec3(1.0, 0.17, 0.34);
    vec3 color = mix(violet, cyan, clamp(vEnergy * 0.82, 0.0, 1.0));
    color = mix(color, red, uBreach);
    gl_FragColor = vec4(color, circle * (0.24 + min(vEnergy, 1.0) * 0.28));
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

function VoicePoints() {
  const pointsRef = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const positions = useMemo(() => {
    const count = 20_000;
    const array = new Float32Array(count * 3);
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < count; i += 1) {
      const y = 1 - (i / (count - 1)) * 2;
      const radius = Math.sqrt(1 - y * y);
      const theta = goldenAngle * i;
      array[i * 3] = Math.cos(theta) * radius;
      array[i * 3 + 1] = y;
      array[i * 3 + 2] = Math.sin(theta) * radius;
    }
    return array;
  }, []);

  useFrame(({ clock }) => {
    const state = useFairModel.getState();
    const material = materialRef.current;
    if (!material) return;
    material.uniforms.uTime.value = clock.elapsedTime;
    material.uniforms.uAudio.value = state.audioLevel;
    material.uniforms.uBreach.value = state.breachActive ? 1 : 0;
    material.uniforms.uPulse.value = Math.max(0, 1 - ((Date.now() % 1100) / 1100)) * (state.eventPulse ? 0.18 : 0);
    if (pointsRef.current) {
      const target = state.breachActive ? 0.72 : 0;
      pointsRef.current.rotation.y += 0.002 + state.audioLevel * 0.008;
      pointsRef.current.rotation.x = THREE.MathUtils.damp(
        pointsRef.current.rotation.x,
        target,
        1.2,
        1 / 60,
      );
      const scale = state.breachActive ? 0.92 : 1 + Math.sin(clock.elapsedTime * 1.1) * 0.018;
      pointsRef.current.scale.setScalar(scale);
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={positions.length / 3}
          itemSize={3}
        />
      </bufferGeometry>
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={{
          uTime: { value: 0 },
          uAudio: { value: 0 },
          uPulse: { value: 0 },
          uBreach: { value: 0 },
        }}
      />
    </points>
  );
}

function LicenseShell() {
  const shell = useRef<THREE.Mesh>(null);
  const verified = useFairModel((state) => state.contractVerified);
  const breach = useFairModel((state) => state.breachActive);
  useFrame((_, delta) => {
    if (shell.current) {
      shell.current.rotation.y -= delta * 0.06;
      shell.current.rotation.x += delta * 0.025;
    }
  });
  return (
    <group>
      <mesh ref={shell} scale={1.31}>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial
          color={breach ? "#ff3b5c" : verified ? "#22e5ff" : "#8b5cff"}
          wireframe
          transparent
          opacity={breach ? 0.75 : verified ? 0.21 : 0.12}
        />
      </mesh>
      <mesh scale={1.27}>
        <sphereGeometry args={[1, 28, 28]} />
        <meshBasicMaterial
          color={breach ? "#ff3b5c" : "#8b5cff"}
          transparent
          opacity={breach ? 0.035 : 0.018}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}

function OrbWorld() {
  const breach = useFairModel((state) => state.breachActive);
  return (
    <>
      <fog attach="fog" args={["#090711", 4, 9]} />
      <ambientLight intensity={0.28} />
      <pointLight position={[2, 1.2, 2]} color={breach ? "#ff3155" : "#a483ff"} intensity={breach ? 4 : 2.4} />
      <pointLight position={[-2, -1, 1]} color="#22e5ff" intensity={1.5} />
      <group>
        <LicenseShell />
        <VoicePoints />
      </group>
      <Sparkles count={70} scale={4.5} size={1.6} speed={0.15} color={breach ? "#ff536b" : "#8b5cff"} />
      <OrbitControls enablePan={false} minDistance={3.7} maxDistance={5.5} minPolarAngle={1.1} maxPolarAngle={2.1} rotateSpeed={0.25} />
      <EffectComposer multisampling={0}>
        <Bloom intensity={breach ? 2.2 : 1.15} luminanceThreshold={0.1} luminanceSmoothing={0.8} mipmapBlur />
        <ChromaticAberration offset={new THREE.Vector2(breach ? 0.003 : 0.00045, breach ? 0.003 : 0.00045)} />
        <Vignette eskil={false} offset={0.16} darkness={0.76} />
      </EffectComposer>
    </>
  );
}

export default function OrbScene({
  className = "",
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  const setAudioLevel = useFairModel((state) => state.setAudioLevel);
  const setScreen = useFairModel((state) => state.setScreen);
  const audioLevel = useFairModel((state) => state.audioLevel);
  const [canvasEnabled] = useState(() => {
    if (typeof window === "undefined") return false;
    const mobile = window.matchMedia("(max-width: 760px), (pointer: coarse)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const lowPower = navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency < 4;
    return !mobile && !reduced && !lowPower;
  });
  return (
    <div
      className={`orb-scene ${compact ? "orb-scene-compact" : ""} ${className}`}
      style={{ "--audio-level": audioLevel } as React.CSSProperties}
      onPointerEnter={() => setAudioLevel(Math.max(useFairModel.getState().audioLevel, 0.08))}
      onPointerLeave={() => setAudioLevel(0)}
    >
      <div className="orb-static-fallback" aria-hidden="true" />
      {canvasEnabled ? (
        <Canvas
          camera={{ position: [0, 0, 4.4], fov: 42 }}
          dpr={[1, 1.7]}
          gl={{ alpha: true, antialias: false, powerPreference: "low-power" }}
          aria-label="Interactive 3D voice orb and translucent license shell"
          onDoubleClick={() => setScreen("audit")}
        >
          <OrbWorld />
        </Canvas>
      ) : null}
      <span className="orb-tag orb-tag-top">VOICEPRINT · 99.2%</span>
      <span className="orb-tag orb-tag-bottom">
        {useFairModel.getState().contractVerified ? "LICENSE · ACTIVE" : "VOICE SIGNATURE · LIVE"}
      </span>
    </div>
  );
}
