import { type Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans", "system-ui", "sans-serif"],
        display: ["Plus Jakarta Sans", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          550: "#2563eb",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        surface: {
          light: "#f8fafc",
          DEFAULT: "#ffffff",
          dark: "#0f172a",
          "dark-elevated": "#1e293b",
        },
      },
      borderRadius: {
        card: "1rem",
        panel: "0.75rem",
        input: "0.5rem",
        button: "0.5rem",
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "card-hover":
          "0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)",
        "card-dark":
          "0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.2)",
        modal:
          "0 25px 50px -12px rgb(0 0 0 / 0.15), 0 0 0 1px rgb(0 0 0 / 0.05)",
        "modal-dark":
          "0 25px 50px -12px rgb(0 0 0 / 0.5), 0 0 0 1px rgb(255 255 255 / 0.06)",
        focus: "0 0 0 3px rgba(37, 99, 235, 0.35)",
        "focus-dark": "0 0 0 3px rgba(96, 165, 250, 0.4)",
      },
      transitionDuration: {
        smooth: "200ms",
      },
      ringOffsetColor: {
        DEFAULT: "#fff",
        dark: "#0f172a",
      },
    },
  },
  plugins: [],
} satisfies Config;
