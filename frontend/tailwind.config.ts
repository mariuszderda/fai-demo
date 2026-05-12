import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "bg-base": "var(--bg-base)",
        "bg-surface": "var(--bg-surface)",
        "bg-surface-2": "var(--bg-surface-2)",
        "bg-elevated": "var(--bg-elevated)",
        "border-subtle": "var(--border-subtle)",
        "border-strong": "var(--border-strong)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-muted": "var(--text-muted)",
        accent: "var(--accent)",
        "accent-dim": "var(--accent-dim)",
        severity: {
          critical: "var(--severity-critical)",
          high: "var(--severity-high)",
          medium: "var(--severity-medium)",
          low: "var(--severity-low)",
          info: "var(--severity-info)",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        body: ['"Inter Tight"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "2px",
        DEFAULT: "4px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;

