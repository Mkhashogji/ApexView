'use client'

import { useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { GapToFastest } from '@/../../packages/models/src/types'

interface PitStopGapToFastestProps {
  gapData: GapToFastest[]
  fastestTeam: string | null
}

/**
 * Vertical bar chart: teams on x-axis, gap to fastest on y-axis.
 * The fastest team shows 0.000s; all others show positive values.
 * Fixed height — Plotly responsive mode handles width.
 */
export default function PitStopGapToFastest({
  gapData,
  fastestTeam,
}: PitStopGapToFastestProps) {
  const { traces, layout, config } = useMemo(() => {
    const traces = [
      {
        type: 'bar' as const,
        x: gapData.map((g) => g.team),
        y: gapData.map((g) => g.gapToFastest),
        marker: {
          color: gapData.map((g) => getTeamColorForMode(g.team, 'team')),
        },
        text: gapData.map((g) =>
          g.gapToFastest === 0 ? 'Fastest' : `+${g.gapToFastest.toFixed(3)}s`
        ),
        textposition: 'outside' as const,
        textfont: { color: '#9CA3AF', size: 10 },
        hoverinfo: 'none' as const,
        showlegend: false,
      } as Record<string, unknown>,
    ]

    const layout = {
      ...BASE_LAYOUT,
      height: 350,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      margin: { l: 50, r: 20, t: 20, b: 80 },
      xaxis: {
        tickangle: -45,
        automargin: true,
      },
      yaxis: {
        ...BASE_AXIS,
        title: {
          text: 'Gap to Fastest (s)',
          font: { size: 10, color: '#6B7280' },
        },
        zeroline: true,
        zerolinecolor: 'rgba(255,255,255,0.2)',
      },
    }

    const config = BASE_CONFIG

    return { traces, layout, config }
  }, [gapData, fastestTeam])

  return (
    <PlotlyLazy
      data={traces}
      layout={layout}
      config={config}
      style={CHART_CONTAIN_STYLE}
    />
  )
}
