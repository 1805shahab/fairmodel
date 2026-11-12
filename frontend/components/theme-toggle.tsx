"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";

const subscribe = (notify: () => void) => {
  window.addEventListener("fairmodel-theme", notify);
  return () => window.removeEventListener("fairmodel-theme", notify);
};
const snapshot = () => document.documentElement.dataset.theme === "dark";
export const useDarkTheme = () =>
  useSyncExternalStore(subscribe, snapshot, () => false);

export default function ThemeToggle() {
  const dark = useDarkTheme();
  function toggle() {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("fairmodel-theme", next);
    } catch {
      /* Theme still works without storage. */
    }
    window.dispatchEvent(new Event("fairmodel-theme"));
  }
  return (
    <button
      className="icon-button theme-toggle"
      type="button"
      onClick={toggle}
      aria-label={dark ? "Use light theme" : "Use dark theme"}
      title={dark ? "Use light theme" : "Use dark theme"}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
