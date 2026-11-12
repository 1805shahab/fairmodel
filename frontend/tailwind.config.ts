// Tailwind v4 loads this configuration through @config in globals.css.
const config = {
  theme: {
    extend: {
      colors: {
        paper: "var(--canvas)",
        ink: "var(--ink)",
        surface: "var(--surface)",
        vermilion: "var(--accent)",
        line: "var(--border)",
        muted: "var(--muted)",
        approved: "var(--positive)",
        pending: "var(--pending)",
        violation: "var(--negative)",
      },
      fontFamily: {
        sans: ["Geist", "Arial", "sans-serif"],
        display: ["Instrument Serif", "Georgia", "serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        caption: "0.75rem",
        body: "0.875rem",
        title: "3rem",
        display: "5.5rem",
      },
      spacing: { unit: "8px", section: "48px", gutter: "32px" },
      borderRadius: { panel: "4px", control: "4px" },
      transitionDuration: { ui: "180ms", panel: "220ms" },
      transitionTimingFunction: { ui: "cubic-bezier(.2,.8,.2,1)" },
    },
  },
};
export default config;
