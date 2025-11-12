# Design Theme & Style Guide

## Color Palette

### Brand Colors
```css
--f1-red: #E10600       /* Primary brand color */
--f1-dark: #15151E      /* Background dark */
--f1-gray: #38383F      /* Secondary background */
```

### Team Colors (2024 Season)
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

### Tyre Compound Colors
```css
--soft: #FF3333
--medium: #FFEB3B
--hard: #F5F5F5
--intermediate: #43A047
--wet: #1976D2
```

### Semantic Colors
```css
--success: #10B981
--warning: #F59E0B
--error: #EF4444
--info: #3B82F6
```

## Typography

### Font Stack
- Primary: System UI fonts for performance
- Fallback: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- Monospace: 'JetBrains Mono', 'Fira Code', monospace (for timing data)

### Font Sizes
- Heading 1: 2.5rem (40px)
- Heading 2: 2rem (32px)
- Heading 3: 1.5rem (24px)
- Body: 1rem (16px)
- Small: 0.875rem (14px)
- Tiny: 0.75rem (12px)

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

## Spacing

Use Tailwind's spacing scale:
- xs: 0.25rem (4px)
- sm: 0.5rem (8px)
- md: 1rem (16px)
- lg: 1.5rem (24px)
- xl: 2rem (32px)
- 2xl: 3rem (48px)

## Components

### Cards
```tsx
<div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
  {/* content */}
</div>
```

### Buttons
- Primary: Red background (#E10600)
- Secondary: Gray background with hover states
- Ghost: Transparent with border

### Navigation
- Fixed top navigation bar
- Dark background with slight transparency
- Active page indicator with red underline

### Charts
- Dark backgrounds to match theme
- Team colors for driver data
- White/light gray for axes and labels
- Subtle grid lines

## Layout

### Grid System
- Max width: 1280px (max-w-7xl)
- Padding: 1rem mobile, 1.5rem tablet, 2rem desktop
- Grid columns: 1 (mobile), 2 (tablet), 3 (desktop)

### Responsive Breakpoints
```css
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */
```

## Animation

### Transitions
- Default duration: 150ms
- Hover effects: 200ms
- Page transitions: 300ms
- Easing: ease-in-out

### Loading States
- Skeleton screens for content loading
- Spinner for action feedback
- Progress bars for data fetching

## Accessibility

### Contrast Ratios
- Text on dark background: ≥4.5:1
- Large text: ≥3:1
- Interactive elements: ≥3:1

### Focus States
- Visible focus ring on all interactive elements
- Blue outline: 2px solid #3B82F6

### Keyboard Navigation
- Tab order follows visual order
- Skip links for main content
- Esc key closes modals/dropdowns

## Icons

### Icon Library
- Use Heroicons for UI icons
- SVG format for scalability
- 20px or 24px standard sizes

### Usage
- Pair with text labels when possible
- Use aria-labels for icon-only buttons
- Consistent stroke width (1.5px or 2px)

## Data Visualization

### Chart Colors
1. Use team colors for driver-specific data
2. Use sequential color scale for numeric data
3. Use diverging scale for delta/comparison data
4. Maintain sufficient contrast against dark background

### Chart Types
- Line charts: Telemetry traces, lap times
- Scatter plots: Lap time distribution
- Bar charts: Sector comparisons
- Area charts: Stint pace evolution
- Heatmaps: Session overview

### Best Practices
- Always include axis labels
- Show units (km/h, seconds, meters)
- Use legends for multi-series data
- Enable tooltips for detail views
- Support zoom/pan on dense data

## Motion & Interaction

### Hover Effects
- Subtle scale (1.02) or opacity (0.9) changes
- Color transitions for buttons
- Underline for text links

### Click Feedback
- Brief scale down (0.98) on click
- Loading indicator if action takes >300ms
- Success feedback (green checkmark, message)

### Scroll Behavior
- Smooth scrolling within page
- Sticky navigation header
- Parallax effects (subtle, if any)

## Dark Mode

This app uses a dark theme by default for:
- Reduced eye strain during extended analysis
- Better contrast for colorful telemetry data
- Professional, technical aesthetic
- Battery savings on OLED devices

## Responsive Design

### Mobile (< 768px)
- Single column layout
- Collapsible filters
- Simplified charts
- Bottom navigation (optional)

### Tablet (768px - 1024px)
- Two column layout
- Side-by-side comparisons
- Full chart functionality

### Desktop (> 1024px)
- Three column layout
- Multi-panel views
- Advanced filtering options
- Multiple simultaneous charts

