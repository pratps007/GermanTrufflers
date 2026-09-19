/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0A0F1D',
          card: '#131B2E',
          accent: '#00F0FF',
          warning: '#FF3366',
        }
      }
    },
  },
  plugins: [],
}
