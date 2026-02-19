'use client'

import { useMemo, useState, useCallback, useRef } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColorForMode } from '@/lib/drivers'
import { formatLapTime } from '@/lib/formatters'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { DriverDegradationData } from '@/../../packages/models/src/types'

interface DegradationScatterProps {
  compound: string
  drivers: DriverDegradationData[]
  mode: 'driver' | 'team'
}

/**
 * Dual-chart component for a single compound:
 * - Left: Scatter plot of fuel-adjusted times vs tyre age with regression lines
 * - Right: Horizontal bar chart of wear rates (highest at top, lowest at bottom)
 */
export default function DegradationScatter({
  compound,
  drivers,
  mode,
}: DegradationScatterProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [tooltip, setTooltip] = useState<{
    x: number
    y: number
    content: { driver: string; team: string; tyreAge: number; fuelAdj: number; raw: number; lap: number; stint: number }
  } | null>(null)

  // Build scatter + regression traces
  const scatterTraces = useMemo(() => {
    return drivers.flatMap((d) => {
      const color = getTeamColorForMode(d.identifier, mode)

      const scatter: Record<string, unknown> = {
        type: 'scatter',
        mode: 'markers',
        name: d.identifier,
        x: d.dataPoints.map((p) => p.tyreAge),
        y: d.dataPoints.map((p) => p.fuelAdjustedTime),
        marker: {
          color,
          size: 5,
          opacity: 0.7,
        },
        hoverinfo: 'none',
        showlegend: true,
        legendgroup: d.identifier,
        // Store custom data for tooltip
        customdata: d.dataPoints.map((p) => [
          p.driver,
          p.team,
          p.tyreAge,
          p.fuelAdjustedTime,
          p.rawTime,
          p.lapNumber,
          p.stintNumber,
        ]),
      }

      const traces = [scatter]

      if (d.regression) {
        traces.push({
          type: 'scatter',
          mode: 'lines',
          name: `${d.identifier} trend`,
          x: [d.regression.startX, d.regression.endX],
          y: [d.regression.startY, d.regression.endY],
          line: {
            color,
            width: 2,
            dash: 'solid',
          },
          hoverinfo: 'none',
          showlegend: false,
          legendgroup: d.identifier,
        })
      }

      return traces
    })
  }, [drivers, mode])

  const scatterLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      showlegend: true,
      xaxis: {
        ...BASE_AXIS,
        title: { text: 'Tyre Age (Laps)', font: { size: 12, color: '#9CA3AF' } },
      },
      yaxis: {
        ...BASE_AXIS,
        title: { text: 'Fuel-Adjusted Lap Time (s)', font: { size: 12, color: '#9CA3AF' } },
        autorange: true,
      },
      legend: {
        orientation: 'h' as const,
        yanchor: 'bottom' as const,
        y: 1.02,
        xanchor: 'right' as const,
        x: 1,
        font: { size: 10, color: '#9CA3AF' },
      },
      margin: { l: 65, r: 15, t: 30, b: 55 },
      dragmode: 'zoom',
      height: 400,
    }),
    []
  )

  // Wear rate bar chart traces
  const barData = useMemo(() => {
    const withWearRate = drivers
      .filter((d) => d.wearRate !== null)
      .sort((a, b) => (a.wearRate ?? 0) - (b.wearRate ?? 0))

    if (withWearRate.length === 0) return null

    return {
      traces: [
        {
          type: 'bar',
          orientation: 'h',
          x: withWearRate.map((d) => d.wearRate),
          y: withWearRate.map((d) => d.identifier),
          marker: {
            color: withWearRate.map((d) =>
              getTeamColorForMode(d.identifier, mode)
            ),
          },
          hoverinfo: 'none',
          showlegend: false,
          text: withWearRate.map((d) =>
            d.wearRate !== null ? `${d.wearRate.toFixed(3)} s/lap` : ''
          ),
          textposition: 'outside',
          textfont: { size: 10, color: '#9CA3AF' },
        } as Record<string, unknown>,
      ],
      count: withWearRate.length,
    }
  }, [drivers, mode])

  const barLayout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
      xaxis: {
        ...BASE_AXIS,
        title: { text: 'Wear Rate (s/lap)', font: { size: 11, color: '#9CA3AF' } },
      },
      yaxis: {
        automargin: true,
      },
      margin: { l: 80, r: 60, t: 10, b: 45 },
      height: barData ? Math.min(400, Math.max(200, barData.count * 30 + 80)) : 200,
    }),
    [barData]
  )

  const plotConfig = useMemo(() => BASE_CONFIG, [])

  // Custom tooltip on hover
  const handleHover = useCallback((event: Record<string, unknown>) => {
    const points = event.points as Array<Record<string, unknown>> | undefined
    if (!points || points.length === 0) return
    const point = points[0]
    const customdata = point.customdata as
      | [string, string, number, number, number, number, number]
      | undefined
    if (!customdata) return

    const bbox = (event.event as MouseEvent) ?? null
    if (!bbox) return

    // Convert viewport coordinates to container-relative
    const containerRect = containerRef.current?.getBoundingClientRect()
    if (!containerRect) return
    const cursorX = (bbox as unknown as { clientX: number }).clientX - containerRect.left
    const cursorY = (bbox as unknown as { clientY: number }).clientY - containerRect.top

    setTooltip({
      x: cursorX,
      y: cursorY,
      content: {
        driver: customdata[0],
        team: customdata[1],
        tyreAge: customdata[2],
        fuelAdj: customdata[3],
        raw: customdata[4],
        lap: customdata[5],
        stint: customdata[6],
      },
    })
  }, [])

  const handleUnhover = useCallback(() => {
    setTooltip(null)
  }, [])

  if (drivers.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
        No data available for this compound
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Main layout: scatter (left) + bar (right) on desktop, stacked on mobile */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Scatter plot — 70% on desktop */}
        <div ref={containerRef} className="flex-1 lg:flex-[7] min-w-0 relative">
          <div className="overflow-hidden">
            <PlotlyLazy
              data={scatterTraces}
              layout={scatterLayout}
              config={plotConfig}
              style={{ ...CHART_CONTAIN_STYLE, height: '400px' }}
              useResizeHandler
              onHover={handleHover}
              onUnhover={handleUnhover}
            />
          </div>

          {/* Custom tooltip — container-relative with edge detection (outside overflow-hidden) */}
          {tooltip && (
            <DegradationTooltip
              tooltip={tooltip}
              containerRef={containerRef}
              formatLapTime={formatLapTime}
            />
          )}
        </div>

        {/* Wear rate bar chart — 30% on desktop */}
        <div className="lg:flex-[3] min-w-0 overflow-hidden">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2 text-center">
            Tyre Wear (Lower = Better)
          </h4>
          {barData ? (
            <PlotlyLazy
              data={barData.traces}
              layout={barLayout}
              config={plotConfig}
              style={CHART_CONTAIN_STYLE}
              useResizeHandler
            />
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              Insufficient data for wear rate comparison
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Tooltip Sub-Component — container-relative with edge detection
// =============================================================================

function DegradationTooltip({
  tooltip,
  containerRef,
  formatLapTime: fmt,
}: {
  tooltip: { x: number; y: number; content: { driver: string; team: string; tyreAge: number; fuelAdj: number; raw: number; lap: number; stint: number } }
  containerRef: React.RefObject<HTMLDivElement | null>
  formatLapTime: (t: number) => string
}) {
  const tooltipW = 220
  const tooltipH = 130
  const offset = 14
  const cW = containerRef.current?.offsetWidth ?? 800
  const cH = containerRef.current?.offsetHeight ?? 500

  let left = tooltip.x + offset
  let top = tooltip.y - offset

  // Flip horizontally if near right edge
  if (left + tooltipW > cW) {
    left = tooltip.x - tooltipW - offset
  }
  // Clamp vertically
  if (top + tooltipH > cH) {
    top = cH - tooltipH - 8
  }
  if (top < 0) top = 8

  const t = tooltip.content

  return (
    <div
      className="absolute z-50 pointer-events-none"
      style={{ left: `${left}px`, top: `${top}px` }}
    >
      <div className="bg-gray-900/95 border border-white/10 rounded-lg px-3 py-2 text-xs shadow-xl backdrop-blur-sm">
        <div className="font-semibold text-white mb-1">
          {t.driver}{' '}
          <span className="text-gray-400 font-normal">({t.team})</span>
        </div>
        <div className="space-y-0.5 text-gray-300">
          <div>Tyre Age: {t.tyreAge} laps</div>
          <div>Fuel-Adjusted: {fmt(t.fuelAdj)}</div>
          <div>Raw Time: {fmt(t.raw)}</div>
          <div className="text-gray-500">
            Lap {t.lap} &middot; Stint {t.stint}
          </div>
        </div>
      </div>
    </div>
  )
}
