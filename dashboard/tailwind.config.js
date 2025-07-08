/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'crypto-green': '#00D4AA',
        'crypto-red': '#FF6B6B',
        'crypto-blue': '#4ECDC4',
        'dark-bg': '#1A1A2E',
        'dark-card': '#16213E',
        'dark-accent': '#0F3460',
      },
      fontFamily: {
        'mono': ['Monaco', 'Menlo', 'Ubuntu Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
