/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        lagoon: "#34d399",
        mint: "#dcfce7",
        skyline: "#38bdf8"
      },
      boxShadow: {
        glow: "0 22px 48px rgba(56, 189, 248, 0.18)"
      }
    }
  },
  plugins: []
};
