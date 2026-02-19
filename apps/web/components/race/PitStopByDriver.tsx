'use client'

import { useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { DriverPitStopAggregate } from '@/../../packages/models/src/types'

interface PitStopByDriverProps {
  driverAggregates: DriverPitStopAggregate[]
}

/**
 * Horizontal bar chart showing per-driver pit lane time averages.
 * Colour-coded by team. Array reversed for bottom-to-top rendering.
 * Height dynamically clamped to 600px for ~20 driver grids.
 */
export default function PitStopByDriver({
  driverAggregates,
}: PitStopByDriverProps) {
  const { traces, layout, config } = useMemo(() => {
    // Reverse for horizontal bar rendering (fastest at top)
    const sorted = [...driverAggregates].reverse()

    const traces = [
      {
        type: 'bar' as const,
        orientation: 'h' as const,
        y: sorted.map((d) => d.driver),
        x: sorted.map((d) => d.averagePitLaneTime),
        marker: {
          color: sorted.map((d) => getTeamColorForMode(d.team, 'team')),
        },
        text: sorted.map((d) => `${d.averagePitLaneTime.toFixed(2)}s`),
        textposition: 'outside' as const,
        textfont: { color: '#9CA3AF', size: 10 },
        hoverinfo: 'none' as const,
        showlegend: false,
      } as Record<string, unknown>,
    ]

    const barCount = sorted.length
    const dynamicHeight = Math.min(600, Math.max(200, barCount * 28 + 80))

    const layout = {
      ...BASE_LAYOUT,
      height: dynamicHeight,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      margin: { l: 80, r: 60, t: 10, b: 30 },
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
  }, [driverAggregates])

  return (
    <PlotlyLazy
      data={traces}
      layout={layout}
      config={config}
      style={CHART_CONTAIN_STYLE}
    />
  )
}
