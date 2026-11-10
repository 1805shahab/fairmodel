"use client";

import {
  Component,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

type Props = { children: ReactNode; fallback: ReactNode };
const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

class SceneBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

export default function SceneGuard({ children, fallback }: Props) {
  // Hydrate the same fallback as the server before enabling browser-only graphics.
  const hydrated = useSyncExternalStore(
    subscribe,
    clientSnapshot,
    serverSnapshot,
  );
  const [enabled] = useState(() => {
    if (typeof window === "undefined") return false;
    if (
      window.matchMedia(
        "(max-width: 760px), (pointer: coarse), (prefers-reduced-motion: reduce)",
      ).matches
    )
      return false;
    if (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency < 4)
      return false;
    try {
      const context = document.createElement("canvas").getContext("webgl2");
      context?.getExtension("WEBGL_lose_context")?.loseContext();
      return Boolean(context);
    } catch {
      return false;
    }
  });
  return hydrated && enabled ? (
    <SceneBoundary fallback={fallback}>{children}</SceneBoundary>
  ) : (
    fallback
  );
}
