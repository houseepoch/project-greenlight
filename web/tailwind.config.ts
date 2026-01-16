import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  // Safelist dynamic grid column classes for entity zoom control
  safelist: [
    "grid-cols-2",
    "grid-cols-3",
    "grid-cols-4",
    "grid-cols-5",
    "grid-cols-6",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f0f0f",
        foreground: "#e5e5e5",
        card: {
          DEFAULT: "#1a1a1a",
          foreground: "#e5e5e5",
        },
        primary: {
          DEFAULT: "#22c55e",
          foreground: "#0f0f0f",
        },
        secondary: {
          DEFAULT: "#262626",
          foreground: "#e5e5e5",
        },
        muted: {
          DEFAULT: "#262626",
          foreground: "#a3a3a3",
        },
        accent: {
          DEFAULT: "#22c55e",
          foreground: "#0f0f0f",
        },
        border: "#333333",
        input: "#262626",
        ring: "#22c55e",
        success: "#22c55e",
        warning: "#f59e0b",
        error: "#ef4444",
        destructive: {
          DEFAULT: "#ef4444",
          foreground: "#ffffff",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

