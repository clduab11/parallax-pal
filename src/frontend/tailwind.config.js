/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          black: '#0C0C0C',
          green: '#00FF00',
          'green-dark': '#006600',
          amber: '#FFB000',
          gray: '#808080',
          'gray-dark': '#1A1A1A',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Courier New', 'monospace']
      },
      animation: {
        'cursor-blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        }
      },
      backgroundImage: {
        'scanline': 'linear-gradient(transparent 50%, rgba(0, 255, 0, 0.05) 50%)',
      }
    },
  },
  plugins: [],
}