/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#080b12',
          deep: '#050810',
        },
        surface: {
          DEFAULT: '#0f1318',
          light: '#151b24',
          hover: '#1a2030',
          border: 'rgba(200, 164, 92, 0.12)',
        },
        gold: {
          DEFAULT: '#c8a45c',
          dim: '#8b7340',
          bright: '#e0c67a',
          muted: '#5c4d30',
          glow: 'rgba(200, 164, 92, 0.15)',
        },
        copper: {
          DEFAULT: '#b87333',
          dim: '#7a4d22',
        },
        text: {
          DEFAULT: '#e8e2d6',
          muted: '#7a7569',
          dim: '#4d4940',
        },
        status: {
          success: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#3b82f6',
          processing: '#c8a45c',
        },
        teal: {
          DEFAULT: '#2dd4bf',
          dim: '#134e4a',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'blink': 'blink 1.5s ease-in-out infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
      },
      boxShadow: {
        'gold-sm': '0 0 10px rgba(200, 164, 92, 0.08)',
        'gold-md': '0 0 20px rgba(200, 164, 92, 0.12)',
        'gold-lg': '0 0 40px rgba(200, 164, 92, 0.15)',
        'inner-gold': 'inset 0 1px 0 rgba(200, 164, 92, 0.05)',
      },
    },
  },
  plugins: [],
}
