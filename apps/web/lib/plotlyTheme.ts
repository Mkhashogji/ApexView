/**
 * Shared Plotly theme for ApexView dark-mode charts.
 *
 * All values typed as Record<string, unknown> to match PlotlyLazy's
 * prop interface. Individual chart components spread these bases
 * inside useMemo and override specific properties (height, margins,
 * axis titles, etc.).
 *
 * Usage:
 *   const layout = useMemo(() => ({
 *     ...BASE_LAYOUT,
 *     height: 450,
 *     margin: { l: 50, r: 30, t: 10, b: 30 },
 *     xaxis: { ...BASE_AXIS, title: { text: '...', font: AXIS_TITLE_FONT } },
 *   }), [deps])
 *
 *   const config = BASE_CONFIG
 */

/** Base layout properties shared by ALL race page charts */
export const BASE_LAYOUT: Record<string, unknown> = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#9CA3AF', family: 'Inter, sans-serif' },
  showlegend: false,
}

/** Common axis styling — spread into xaxis/yaxis, override per chart */
export const BASE_AXIS: Record<string, unknown> = {
  gridcolor: 'rgba(255,255,255,0.08)',
  zeroline: false,
}

/**
 * Shared Plotly config for all race page charts.
 * Immutable — safe to pass directly without useMemo wrapping.
 */
export const BASE_CONFIG: Record<string, unknown> = {
  displayModeBar: 'hover',
  responsive: true,
  scrollZoom: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
}

/**
 * CSS style for chart container divs.
 * contain: layout paint prevents forced reflow cascades by isolating
 * Plotly's dimension queries to the chart's own subtree.
 */
export const CHART_CONTAIN_STYLE: React.CSSProperties = {
  contain: 'layout paint',
  width: '100%',
}
