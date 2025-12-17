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
        // Driver team colors (2025 season)
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
        // Semantic colors for deltas
        'delta-positive': '#EF4444', // Slower (red)
        'delta-negative': '#22C55E', // Faster (green)
        // Chart annotation colors
        'drs-zone': '#22C55E',
        'sector-line': '#6B7280',
        // Purple for fastest sector
        'purple-sector': '#A855F7',
      },
      fontFamily: {
        // Montserrat for headings, Inter for body text
        heading: ['Montserrat', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        formula: ['var(--font-formula)', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        // Red glow for active elements
        'glow-red': '0 0 10px rgba(225, 6, 0, 0.5)',
        'glow-red-sm': '0 0 5px rgba(225, 6, 0, 0.3)',
        // Team color glows
        'glow-team': '0 0 8px currentColor',
      },
      backgroundImage: {
        // Subtle carbon fiber pattern
        'carbon-fiber': `url("data:image/svg+xml,%3Csvg width='6' height='6' viewBox='0 0 6 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%2338383F' fill-opacity='0.15'%3E%3Cpath d='M5 0h1L0 5v1h1L6 1V0H5z'/%3E%3C/g%3E%3C/svg%3E")`,
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

