/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0E14',
        surface: '#151A24',
        surface_hover: '#1E2532',
        primary: '#38BDF8',
        accent: '#818CF8',
        success: '#34D399',
        warning: '#FBBF24',
        danger: '#F87171',
        text_main: '#F3F4F6',
        text_muted: '#9CA3AF'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}
