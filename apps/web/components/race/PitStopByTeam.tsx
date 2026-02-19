'use client'

import { useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { TeamPitStopAggregate } from '@/../../packages/models/src/types'

interface PitStopByTeamProps {
  teamAggregates: TeamPitStopAggregate[]
}

/**
 * Horizontal bar chart showing team-averaged pit lane times.
 * Data arrives pre-sorted ascending (fastest first).
 * Array is reversed so the fastest team appears at the top
 * (Plotly renders horizontal bars bottom-to-top).
 */
export default function PitStopByTeam({ teamAggregates }: PitStopByTeamProps) {
  const { traces, layout, config } = useMemo(() => {
    // Reverse for horizontal bar rendering (fastest at top)
    const sorted = [...teamAggregates].reverse()

    const traces = [
      {
        type: 'bar' as const,
        orientation: 'h' as const,
        y: sorted.map((t) => t.team),
        x: sorted.map((t) => t.averagePitLaneTime),
        marker: {
          color: sorted.map((t) => getTeamColorForMode(t.team, 'team')),
        },
        text: sorted.map((t) => `${t.averagePitLaneTime.toFixed(2)}s`),
        textposition: 'outside' as const,
        textfont: { color: '#9CA3AF', size: 10 },
        hoverinfo: 'none' as const,
        showlegend: false,
      } as Record<string, unknown>,
    ]

    const barCount = sorted.length
    const dynamicHeight = Math.min(400, Math.max(200, barCount * 35 + 80))

    const layout = {
      ...BASE_LAYOUT,
      height: dynamicHeight,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      margin: { l: 120, r: 60, t: 10, b: 30 },
      xaxis: {
        ...BASE_AXIS,
        title: {
          text: 'Average Pit Lane Time (s)',
          font: { size: 10, color: '#6B7280' },
        },
      },
      yaxis: {
        automargin: true,
      },
    }

    const config = BASE_CONFIG

    return { traces, layout, config }
  }, [teamAggregates])

  return (
    <PlotlyLazy
      data={traces}
      layout={layout}
      config={config}
      style={CHART_CONTAIN_STYLE}
    />
  )
}
