/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { ink: '#17345f', muted: '#7083a2', brand: '#2563eb', canvas: '#f6f9ff' }, boxShadow: { soft: '0 10px 35px rgba(33, 73, 130, 0.07)' } } },
  plugins: [],
}
