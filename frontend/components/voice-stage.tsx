"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

class VoiceLoop extends THREE.Curve<THREE.Vector3> {
  constructor(private strand: number) {
    super();
  }
  getPoint(t: number, target = new THREE.Vector3()) {
    const a = t * Math.PI * 2;
    const radial =
      1.03 + this.strand * 0.012 + 0.16 * Math.cos(3 * a + this.strand * 0.02);
    return target.set(
      Math.sin(a) * radial,
      Math.cos(a) * radial,
      0.29 * Math.sin(3 * a + this.strand * 0.045),
    );
  }
}

export default function VoiceStage({
  paused,
  rotation,
  resetKey,
  onFailure,
  lowPower,
}: {
  paused: boolean;
  rotation: number;
  resetKey: number;
  onFailure: () => void;
  lowPower: boolean;
}) {
  const mount = useRef<HTMLDivElement>(null);
  const inputs = useRef({ paused, rotation });
  const redraw = useRef<(() => void) | null>(null);
  const reset = useRef<(() => void) | null>(null);
  useEffect(() => {
    reset.current?.();
  }, [resetKey]);
  useEffect(() => {
    inputs.current = { paused, rotation };
    redraw.current?.();
  }, [paused, rotation]);
  useEffect(() => {
    const host = mount.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "low-power",
      });
    } catch {
      onFailure();
      return;
    }
    renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, lowPower ? 1 : 1.5),
    );
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    const canvas = renderer.domElement;
    canvas.setAttribute(
      "aria-label",
      "Interactive 3D voice sculpture. Drag or use arrow keys to rotate.",
    );
    canvas.setAttribute("role", "img");
    canvas.tabIndex = 0;
    host.appendChild(canvas);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 50);
    camera.position.set(0, 0, 4.9);
    scene.add(new THREE.HemisphereLight(0xcdefff, 0x151525, 1.8));
    const light = new THREE.DirectionalLight(0xffffff, 5);
    light.position.set(-2, 4, 3);
    scene.add(light);
    const rim = new THREE.DirectionalLight(0x59c8ff, 5);
    rim.position.set(3, -1, -1);
    scene.add(rim);
    const warm = new THREE.DirectionalLight(0xffba81, 2);
    warm.position.set(-3, -2, 2);
    scene.add(warm);
    const sculpture = new THREE.Group();
    scene.add(sculpture);
    const material = new THREE.MeshStandardMaterial({
      color: 0xa9cbdc,
      roughness: 0.24,
      metalness: 0.58,
    });
    const geometries: THREE.BufferGeometry[] = [];
    const count = lowPower ? 22 : 38;
    for (let i = 0; i < count; i++) {
      const geometry = new THREE.TubeGeometry(
        new VoiceLoop(i - count / 2),
        lowPower ? 100 : 160,
        0.009,
        6,
        true,
      );
      geometries.push(geometry);
      sculpture.add(new THREE.Mesh(geometry, material));
    }
    const haloGeo = new THREE.TorusGeometry(1.65, 0.003, 3, 120);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0x476078,
      transparent: true,
      opacity: 0.42,
    });
    const halo = new THREE.Mesh(haloGeo, haloMat);
    halo.rotation.x = 0.2;
    scene.add(halo);
    let frame = 0,
      last = 0,
      phase = 0,
      visible = true,
      force = true,
      dragX = 0,
      dragY = 0;
    let pointer: { x: number; y: number; id: number } | null = null;
    function wake() {
      force = true;
      if (!frame) frame = requestAnimationFrame(tick);
    }
    function tick(now: number) {
      frame = 0;
      if (!visible || document.hidden) return;
      const moving = !inputs.current.paused;
      if (force || now - last >= 1000 / 30) {
        if (moving) phase += Math.min(now - (last || now), 60) * 0.00014;
        last = now;
        force = false;
        sculpture.rotation.set(
          0.45 + dragY,
          0.35 + phase + inputs.current.rotation + dragX,
          -0.24,
        );
        try {
          renderer.render(scene, camera);
          canvas.dataset.rendered = "true";
        } catch {
          onFailure();
          return;
        }
      }
      if (moving) frame = requestAnimationFrame(tick);
    }
    const resize = new ResizeObserver(() => {
      const width = host.clientWidth,
        height = host.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      wake();
    });
    resize.observe(host);
    const visibility = new IntersectionObserver((entries) => {
      visible = entries[0].isIntersecting;
      if (visible) {
        last = 0;
        wake();
      }
    });
    visibility.observe(host);
    const onVisibility = () => {
      if (!document.hidden) {
        last = 0;
        wake();
      }
    };
    const down = (e: PointerEvent) => {
      if (e.button !== 0) return;
      pointer = { x: e.clientX, y: e.clientY, id: e.pointerId };
      canvas.setPointerCapture(e.pointerId);
    };
    const move = (e: PointerEvent) => {
      if (!pointer) return;
      dragX += (e.clientX - pointer.x) * 0.008;
      dragY += (e.clientY - pointer.y) * 0.005;
      pointer.x = e.clientX;
      pointer.y = e.clientY;
      wake();
    };
    const up = () => {
      pointer = null;
    };
    const key = (e: KeyboardEvent) => {
      if (
        !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home"].includes(
          e.key,
        )
      )
        return;
      e.preventDefault();
      if (e.key === "Home") {
        dragX = 0;
        dragY = 0;
      } else if (e.key === "ArrowLeft") dragX -= 0.2;
      else if (e.key === "ArrowRight") dragX += 0.2;
      else if (e.key === "ArrowUp") dragY -= 0.2;
      else dragY += 0.2;
      wake();
    };
    const lost = (e: Event) => {
      e.preventDefault();
      onFailure();
    };
    canvas.addEventListener("pointerdown", down);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
    canvas.addEventListener("keydown", key);
    canvas.addEventListener("webglcontextlost", lost);
    document.addEventListener("visibilitychange", onVisibility);
    redraw.current = wake;
    reset.current = () => {
      dragX = 0;
      dragY = 0;
      phase = 0;
      wake();
    };
    wake();
    return () => {
      redraw.current = null;
      reset.current = null;
      cancelAnimationFrame(frame);
      resize.disconnect();
      visibility.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", up);
      canvas.removeEventListener("keydown", key);
      canvas.removeEventListener("webglcontextlost", lost);
      geometries.forEach((g) => g.dispose());
      material.dispose();
      haloGeo.dispose();
      haloMat.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    };
  }, [lowPower, onFailure]);
  return <div ref={mount} className="voice-webgl" />;
}
