# Design Theme & Style Guide

**Updated:** December 2025 - Montserrat/Inter typography, chart standards, glow effects

## Color Palette

### Brand Colors
```css
--f1-red: #E10600       /* Primary brand color, accents */
--f1-dark: #15151E      /* Background dark */
--f1-gray: #38383F      /* Secondary background, borders */
```

### Team Colors (2025 Season)
```css
--redbull: #3671C6
--ferrari: #E8002D
--mercedes: #27F4D2
--mclaren: #FF8000
--astonmartin: #229971
--alpine: #FF87BC
--williams: #64C4FF
--rb: #6692FF
--sauber: #52E252
--haas: #B6BABD
```

### Semantic Colors
```css
--delta-positive: #EF4444  /* Slower (red) */
--delta-negative: #22C55E  /* Faster (green) */
--purple-sector: #A855F7   /* Fastest sector */
--drs-zone: #22C55E        /* DRS zone shading */
--sector-line: #6B7280     /* Sector boundaries */
```

### Tyre Compound Colors
```css
--soft: #FF3333
--medium: #FFEB3B
--hard: #F5F5F5
--intermediate: #43A047
--wet: #1976D2
```

## Typography

### Font Stack

**Headings:** Montserrat (Google Fonts)
- Weight: 500-800
- Style: Bold, uppercase for page titles
- Tracking: Tight (-0.025em)

**Body:** Inter (Google Fonts)
- Weight: 400-700
- Style: Regular for readable content
- Line height: 1.5-1.75

**Monospace:** JetBrains Mono (for timing data)
- Tabular numbers enabled
- Used for lap times, deltas, distances

### Usage

```css
/* Headings - Montserrat */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Montserrat', system-ui, sans-serif;
  font-weight: 700;
  letter-spacing: -0.025em;
}

/* Body - Inter */
body, p, span {
  font-family: 'Inter', system-ui, sans-serif;
}

/* Timing data - JetBrains Mono */
.font-timing, .font-mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-variant-numeric: tabular-nums;
}
```

### Font Sizes (Tailwind)
- Page title (h1): `text-3xl md:text-4xl`
- Section header (h2): `text-lg uppercase tracking-wide`
- Body: `text-sm` (14px)
- Small: `text-xs` (12px)

## Spacing

Use Tailwind's spacing scale consistently:
- `gap-2` (8px) - Tight groupings
- `gap-4` (16px) - Related items
- `gap-6` (24px) - Section spacing
- `p-4` (16px) - Compact panels
- `p-6` (24px) - Standard panels

## Components

### Card Panel
```css
.card-panel {
  @apply rounded-lg border border-f1gray bg-f1dark/80 backdrop-blur-sm p-6;
}

.card-panel-header {
  @apply text-lg font-heading font-semibold uppercase tracking-wide mb-4;
}
```

### Session Tab
```css
.session-tab {
  @apply px-4 py-2 text-sm font-medium transition-all duration-200 
         border-b-2 border-transparent;
}

.session-tab-active {
  @apply text-white border-f1red shadow-glow-red-sm;
}
```

### Driver Chip
```css
.driver-chip {
  @apply inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md 
         text-sm font-medium text-white transition-all duration-150;
  background-color: [team-color];
}
```

### Delta Values
```css
.delta-positive { @apply text-delta-positive; }  /* Red - slower */
.delta-negative { @apply text-delta-negative; }  /* Green - faster */
```

### Purple Sector Badge
```css
.purple-sector {
  @apply bg-purple-sector/20 text-purple-sector border border-purple-sector/50;
}
```

## Glow Effects

### Red Glow (Active Elements)
```css
--glow-red: 0 0 10px rgba(225, 6, 0, 0.5);
--glow-red-sm: 0 0 5px rgba(225, 6, 0, 0.3);
```

Used for:
- Active navigation items
- Selected session tabs
- Primary action buttons

### Team Color Glow
```css
--glow-team: 0 0 8px currentColor;
```

Used for driver-specific highlights.

## Charts (Plotly)

### Standard Configuration

```javascript
const plotlyLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { 
    color: '#9CA3AF', 
    family: 'Inter, sans-serif',
    size: 12 
  },
  xaxis: {
    gridcolor: '#374151',
    zeroline: false,
    title: { standoff: 20 }
  },
  yaxis: {
    gridcolor: '#374151',
    zeroline: false,
    title: { standoff: 10 }
  },
  margin: { l: 65, r: 20, t: 20, b: 70 },
  hovermode: 'x unified',
  legend: {
    orientation: 'h',
    y: -0.25,
    x: 0.5,
    xanchor: 'center',
    bgcolor: 'rgba(0,0,0,0)',
    font: { size: 11 }
  }
}

const plotlyConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
  displaylogo: false,
  toImageButtonOptions: {
    format: 'png',
    scale: 2
  }
}
```

### Chart-Specific Styling

**Telemetry Traces:**
- Line width: 2px
- Team colors for drivers
- DRS zones: `rgba(34, 197, 94, 0.1)` fill

**Delta Plot:**
- Positive (slower): `rgba(239, 68, 68, 0.15)` fill
- Negative (faster): `rgba(34, 197, 94, 0.15)` fill
- Zero line: `#9CA3AF` dashed

**Sector Boundaries:**
- Vertical lines: `#4B5563` dotted
- Labels: 10px gray text above chart

## Responsive Breakpoints

```css
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet - 2-column layout starts */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop - max-w-7xl */
```

### Layout Patterns

**Qualifying Page Grid:**
```css
.grid.gap-6.md:grid-cols-2  /* 2x2 on desktop, stack on mobile */
```

**Sector Cards:**
```css
.grid.gap-4.md:grid-cols-3  /* 3 columns on desktop */
```

## Animation

### Transitions
- Default duration: 150ms
- Hover effects: 200ms
- Tab transitions: `transition-all duration-200`
- Easing: ease-in-out (default)

### Loading States
- Skeleton: `@apply animate-pulse bg-f1gray/30 rounded;`
- ML analyzing: Subtle text pulse

## Accessibility

### Focus States
```css
.focus-ring {
  @apply focus:outline-none focus-visible:ring-2 
         focus-visible:ring-f1red focus-visible:ring-offset-2 
         focus-visible:ring-offset-f1dark;
}
```

### Contrast Requirements
- Body text on dark: ≥4.5:1 (#9CA3AF on #15151E = 5.2:1 ✓)
- Delta colors: Supplemented with +/- signs
- Interactive elements: ≥3:1

### ARIA Patterns
- Tabs: `role="tablist"`, `role="tab"`, `aria-selected`
- Charts: `aria-label` describing content
- Dropdowns: `aria-expanded`, `aria-haspopup`

## Background Pattern

Subtle carbon fiber texture:
```css
background-image: url("data:image/svg+xml,%3Csvg width='6' height='6' 
  viewBox='0 0 6 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cg 
  fill='%2338383F' fill-opacity='0.08'%3E%3Cpath 
  d='M5 0h1L0 5v1h1L6 1V0H5z'/%3E%3C/g%3E%3C/svg%3E");
```

Applied to `body` for subtle depth.

## Dark Theme

The app uses dark theme exclusively:
- Reduces eye strain during analysis
- Better contrast for colorful telemetry
- Professional, technical aesthetic
- Battery savings on OLED

No light mode toggle - design optimized for dark.
