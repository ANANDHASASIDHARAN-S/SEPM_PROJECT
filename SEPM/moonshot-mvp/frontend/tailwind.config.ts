import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#06080c",
          panel: "#0e131c",
          panel2: "#111826",
          border: "#1f2b3d",
          text: "#e2e8f0",
          muted: "#8aa0bd",
          danger: "#ef4444",
          warn: "#f59e0b",
          ok: "#10b981"
        }
      }
    },
  },
  plugins: [],
};

export default config;
