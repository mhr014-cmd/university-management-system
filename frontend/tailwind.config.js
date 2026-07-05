// Tailwind CSS configuration.
// Theme token customization (colors, spacing) beyond dark-mode support is
// left to later milestones, per docs/System_Architecture.md Section 3
// (Styling: TailwindCSS, utility-first, no design system overhead).

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // Toast enter animation (final UI polish pass) — the only custom
      // keyframe in the project; everything else uses Tailwind's
      // built-in transition utilities.
      keyframes: {
        "toast-in": {
          "0%": { opacity: "0", transform: "translateY(0.5rem)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "toast-in": "toast-in 0.15s ease-out",
      },
    },
  },
  plugins: [],
};
