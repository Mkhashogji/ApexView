'use client'

import { useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { TeamPerformanceData } from '@/../../packages/models/src/types'

interface MeanSpeedDivergenceProps {
  teams: TeamPerformanceData[]
}

/**
 * Horizontal divergence bar chart for mean speed deltas.
 * Bars extend left (slower than field average) or right (faster).
 * Zero line represents the field average.
 * Sorted by delta ascending, reversed for Plotly bottom-to-top rendering.
 */
export default function MeanSpeedDivergence({ teams }: MeanSpeedDivergenceProps) {
  const { traces, layout, config } = useMemo(() => {
    // Sort by delta ascending, then reverse for Plotly (fastest at top)
    const sorted = [...teams]
      .sort((a, b) => a.meanSpeedDelta - b.meanSpeedDelta)
      .reverse()

    const traces = [
      {
        type: 'bar' as const,
        orientation: 'h' as const,
        y: sorted.map((t) => t.team),
        x: sorted.map((t) => t.meanSpeedDelta),
        marker: {
          color: sorted.map((t) => getTeamColorForMode(t.team, 'team')),
        },
        text: sorted.map((t) => {
          const sign = t.meanSpeedDelta >= 0 ? '+' : ''
          return `${sign}${t.meanSpeedDelta.toFixed(2)} km/h`
        }),
        textposition: 'outside' as const,
        textfont: { color: '#9CA3AF', size: 10 },
        hovertemplate: sorted.map(
          (t) =>
            `<b>${t.team}</b><br>Mean Speed: ${t.meanSpeed.toFixed(2)} km/h<br>Delta: ${t.meanSpeedDelta >= 0 ? '+' : ''}${t.meanSpeedDelta.toFixed(2)} km/h<extra></extra>`
        ),
        showlegend: false,
      } as Record<string, unknown>,
    ]

    const barCount = sorted.length
    const dynamicHeight = Math.min(400, Math.max(200, barCount * 35 + 80))

    const layout = {
      ...BASE_LAYOUT,
      height: dynamicHeight,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      margin: { l: 120, r: 80, t: 10, b: 30 },
      xaxis: {
        ...BASE_AXIS,
        title: {
          text: 'Delta vs Field Average (km/h)',
          font: { size: 10, color: '#6B7280' },
        },
        zeroline: true,
        zerolinecolor: 'rgba(255,255,255,0.3)',
        zerolinewidth: 1.5,
      },
      yaxis: {
        automargin: true,
      },
    }

    const config = BASE_CONFIG

    return { traces, layout, config }
  }, [teams])

  return (
    <PlotlyLazy
      data={traces}
      layout={layout}
      config={config}
      style={CHART_CONTAIN_STYLE}
    />
  )
}
