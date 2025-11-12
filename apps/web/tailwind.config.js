/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    '../../packages/ui/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // F1 brand colors
        f1red: '#E10600',
        f1dark: '#15151E',
        f1gray: '#38383F',
        // Driver team colors (2024 season)
        redbull: '#3671C6',
        ferrari: '#E8002D',
        mercedes: '#27F4D2',
        mclaren: '#FF8000',
        astonmartin: '#229971',
        alpine: '#FF87BC',
        williams: '#64C4FF',
        rb: '#6692FF',
        sauber: '#52E252',
        haas: '#B6BABD',
      },
      fontFamily: {
        formula: ['var(--font-formula)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

