// Tailwind CSS configuration.
// Theme token customization (colors, spacing) beyond dark-mode support is
// left to later milestones, per docs/System_Architecture.md Section 3
// (Styling: TailwindCSS, utility-first, no design system overhead).

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
