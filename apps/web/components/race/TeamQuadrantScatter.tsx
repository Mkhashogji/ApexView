'use client'

import { useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { BASE_LAYOUT, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type {
  TeamPerformanceData,
  TeamPerformanceFieldAverages,
} from '@/../../packages/models/src/types'

interface TeamQuadrantScatterProps {
  teams: TeamPerformanceData[]
  fieldAverages: TeamPerformanceFieldAverages
}

/**
 * Team abbreviation map for scatter labels.
 * 3-letter codes prevent label overlap on the quadrant chart.
 */
const TEAM_ABBR: Record<string, string> = {
  'Red Bull Racing': 'RBR',
  'Mercedes': 'MER',
  'Ferrari': 'FER',
  'McLaren': 'MCL',
  'Aston Martin': 'AMR',
  'Alpine': 'ALP',
  'Williams': 'WIL',
  'RB': 'RBS',
  'Kick Sauber': 'SAU',
  'Haas F1 Team': 'HAS',
  // Fallback handled in getAbbr()
}

function getAbbr(team: string): string {
  return TEAM_ABBR[team] || team.slice(0, 3).toUpperCase()
}

/**
 * Scatter plot with 10 team dots positioned by mean speed (x) and top speed (y).
 * Crosshair reference lines at field averages divide the plot into four quadrants:
 *   - Top-right: High Efficiency (fast everywhere)
 *   - Bottom-right: High Downforce (fast in corners, slow on straights)
 *   - Top-left: Low Downforce (fast on straights, slow in corners)
 *   - Bottom-left: Low Efficiency (struggling across the board)
 *
 * Crosshair lines use layout.shapes (not traces) to avoid hover/legend artifacts.
 * Quadrant labels use layout.annotations with xref/yref: 'paper'.
 */
export default function TeamQuadrantScatter({
  teams,
  fieldAverages,
}: TeamQuadrantScatterProps) {
  const { traces, layout, config } = useMemo(() => {
    const traces = [
      {
        type: 'scatter' as const,
        mode: 'markers+text' as const,
        x: teams.map((t) => t.meanSpeed),
        y: teams.map((t) => t.topSpeed),
        text: teams.map((t) => getAbbr(t.team)),
        textposition: 'top center' as const,
        textfont: { size: 10, color: '#D1D5DB' },
        marker: {
          size: 12,
          color: teams.map((t) => getTeamColorForMode(t.team, 'team')),
          line: { width: 1, color: 'rgba(255,255,255,0.2)' },
        },
        hovertemplate: teams.map(
          (t) =>
            `<b>${t.team}</b><br>Mean Speed: ${t.meanSpeed.toFixed(2)} km/h<br>Top Speed: ${t.topSpeed.toFixed(1)} km/h<extra></extra>`
        ),
        showlegend: false,
      } as Record<string, unknown>,
    ]

    // Crosshair reference lines at field averages (layout.shapes pattern)
    const shapes = [
      // Vertical line at field mean speed
      {
        type: 'line' as const,
        xref: 'x' as const,
        yref: 'paper' as const,
        x0: fieldAverages.meanSpeed,
        x1: fieldAverages.meanSpeed,
        y0: 0,
        y1: 1,
        line: {
          color: 'rgba(255,255,255,0.2)',
          width: 1,
          dash: 'dash' as const,
        },
      },
      // Horizontal line at field top speed
      {
        type: 'line' as const,
        xref: 'paper' as const,
        yref: 'y' as const,
        x0: 0,
        x1: 1,
        y0: fieldAverages.topSpeed,
        y1: fieldAverages.topSpeed,
        line: {
          color: 'rgba(255,255,255,0.2)',
          width: 1,
          dash: 'dash' as const,
        },
      },
    ]

    // Quadrant labels (layout.annotations with paper coordinates)
    const annotations = [
      {
        x: 0.98,
        y: 0.98,
        xref: 'paper' as const,
        yref: 'paper' as const,
        text: 'High Efficiency',
        showarrow: false,
        font: { size: 10, color: 'rgba(34, 197, 94, 0.6)' },
        xanchor: 'right' as const,
        yanchor: 'top' as const,
      },
      {
        x: 0.02,
        y: 0.98,
        xref: 'paper' as const,
        yref: 'paper' as const,
        text: 'Low Downforce',
        showarrow: false,
        font: { size: 10, color: 'rgba(250, 204, 21, 0.6)' },
        xanchor: 'left' as const,
        yanchor: 'top' as const,
      },
      {
        x: 0.98,
        y: 0.02,
        xref: 'paper' as const,
        yref: 'paper' as const,
        text: 'High Downforce',
        showarrow: false,
        font: { size: 10, color: 'rgba(96, 165, 250, 0.6)' },
        xanchor: 'right' as const,
        yanchor: 'bottom' as const,
      },
      {
        x: 0.02,
        y: 0.02,
        xref: 'paper' as const,
        yref: 'paper' as const,
        text: 'Low Efficiency',
        showarrow: false,
        font: { size: 10, color: 'rgba(239, 68, 68, 0.5)' },
        xanchor: 'left' as const,
        yanchor: 'bottom' as const,
      },
    ]

    const layout = {
      ...BASE_LAYOUT,
      height: 420,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      margin: { l: 65, r: 20, t: 20, b: 55 },
      xaxis: {
        gridcolor: 'rgba(255,255,255,0.06)',
        zeroline: false,
        title: {
          text: 'Mean Speed (km/h)',
          font: { size: 12, color: '#9CA3AF' },
        },
      },
      yaxis: {
        gridcolor: 'rgba(255,255,255,0.06)',
        zeroline: false,
        title: {
          text: 'Top Speed (km/h)',
          font: { size: 12, color: '#9CA3AF' },
        },
      },
      shapes,
      annotations,
      dragmode: 'zoom' as const,
    }

    const config = BASE_CONFIG

    return { traces, layout, config }
  }, [teams, fieldAverages])

  return (
    <PlotlyLazy
      data={traces}
      layout={layout}
      config={config}
      style={{ ...CHART_CONTAIN_STYLE, height: '420px' }}
      useResizeHandler
    />
  )
}
