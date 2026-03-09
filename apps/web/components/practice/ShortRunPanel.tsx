'use client'

import { useMemo, useState } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import {
  BASE_LAYOUT,
  BASE_AXIS,
  BASE_CONFIG,
  CHART_CONTAIN_STYLE,
} from '@/lib/plotlyTheme'
import { getTeamColorForMode } from '@/lib/drivers'
import { getCompoundColor } from '@/lib/compounds'
import { formatLapTime, formatDelta } from '@/lib/formatters'
import { useShortRunQuery } from '@/lib/hooks/useShortRunQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'

interface ShortRunPanelProps {
  sessionId: string
  fuelEffect: number
}

/**
 * Short Run / Best Lap Comparison panel.
 *
 * Renders a ranked horizontal bar chart showing each driver's official
 * session-best lap time (raw FIA timing, never fuel-corrected).
 * Team-coloured bars with compound badges and gap-to-P1 annotations.
 */
export default function ShortRunPanel({
  sessionId,
  fuelEffect,
}: ShortRunPanelProps) {
  const { containerRef, isVisible } = useVisibility()

  const {
    data,
    isLoading,
    isError,
  } = useShortRunQuery(
    sessionId,
    fuelEffect > 0 ? fuelEffect : undefined,
    isVisible,
  )

  // How-to-read guide toggle
  const [showGuide, setShowGuide] = useState(false)

  const hasData = data && data.drivers.length > 0

  // Determine if any driver's session best came from a long run
  const hasLongRunSessionBest = hasData && data.verificationAvailable
    && data.drivers.some((d) => d.sessionBestFromShortRun === false)

  // Verification source (session-wide: use first driver's source)
  const verificationSource = hasData && data.verificationAvailable
    ? data.drivers[0]?.sessionBestSource
    : null

  // ── Plotly traces and layout ──────────────────────────────────────────
  const { traces, layout } = useMemo(() => {
    if (!hasData) return { traces: [], layout: {} }

    // Plotly renders horizontal bars bottom-to-top: reverse so P1 is at top
    const sorted = [...data.drivers].reverse()

    const barCount = sorted.length
    const chartHeight = Math.min(480, Math.max(220, barCount * 38 + 80))

    // Text labels: lap time for P1, lap time + gap for others
    // Append verification indicator when available
    const textLabels = sorted.map((d) => {
      const base = d.position === 1
        ? formatLapTime(d.bestLapTime)
        : `${formatLapTime(d.bestLapTime)}  ${formatDelta(d.gapToP1)}s`

      if (!data.verificationAvailable || d.sessionBestFromShortRun === null) {
        return base
      }
      return d.sessionBestFromShortRun ? `${base} ✓` : `${base} *`
    })

    const barTrace = {
      type: 'bar' as const,
      orientation: 'h' as const,
      x: sorted.map((d) => d.bestLapTime),
      y: sorted.map((d) => d.driver),
      text: textLabels,
      textposition: 'outside' as const,
      textfont: { color: '#9CA3AF', size: 10 },
      hoverinfo: 'none' as const,
      marker: {
        color: sorted.map((d) => getTeamColorForMode(d.team, 'team')),
        opacity: 0.9,
      },
      showlegend: false,
    } as Record<string, unknown>

    // Compound indicator: coloured circle with compound initial
    const compoundTrace = {
      type: 'scatter' as const,
      mode: 'markers+text' as const,
      x: sorted.map(() =>
        data.sessionBestLap ? data.sessionBestLap - 0.4 : null,
      ),
      y: sorted.map((d) => d.driver),
      text: sorted.map((d) => d.compound.charAt(0)),
      textposition: 'middle center' as const,
      textfont: { size: 10, color: '#000000' },
      marker: {
        size: 18,
        color: sorted.map((d) => getCompoundColor(d.compound)),
        symbol: 'circle',
      },
      hoverinfo: 'none' as const,
      showlegend: false,
    } as Record<string, unknown>

    // Tight x-axis: start near the fastest lap to magnify spread
    const axisMin = data.sessionBestLap
      ? data.sessionBestLap - 0.6
      : undefined

    const chartLayout = {
      ...BASE_LAYOUT,
      height: chartHeight,
      margin: { l: 60, r: 90, t: 16, b: 40 },
      xaxis: {
        ...BASE_AXIS,
        title: {
          text: 'Lap Time (s)',
          font: { size: 11, color: '#6B7280' },
        },
        range: axisMin ? [axisMin, undefined] : undefined,
        tickformat: '.2f',
      },
      yaxis: {
        ...BASE_AXIS,
        automargin: true,
        tickfont: { size: 12 },
      },
      showlegend: false,
    }

    return { traces: [barTrace, compoundTrace], layout: chartLayout }
  }, [data, hasData])

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div ref={containerRef} className="card-panel space-y-3 content-defer">
      {/* Panel Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="card-panel-header !mb-0">
            Short Run / Best Lap
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Each driver&apos;s fastest lap in the session, verified against
            official timing. Fuel load and engine mode unknown.
          </p>
          {verificationSource && (
            <p className="text-xs text-gray-500 mt-0.5">
              {verificationSource === 'fastf1_flag'
                ? 'Verified against official session data'
                : 'Cross-referenced with session lap times'}
            </p>
          )}
        </div>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="animate-pulse space-y-2">
          {[85, 79, 72, 65, 58, 51].map((w, i) => (
            <div
              key={i}
              className="h-8 rounded bg-gray-700/50"
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
          Unable to load short run data for this session.
        </div>
      )}

      {/* Empty state — common for FP2 which is predominantly long run work */}
      {!isLoading && !isError && !hasData && (
        <div className="flex flex-col items-center justify-center h-36 text-center space-y-2">
          <p className="text-gray-300 text-sm font-medium">
            No short run stints detected
          </p>
          <p className="text-gray-500 text-xs max-w-xs">
            This session appears to be focused on race simulation long runs.
            Try FP1 or FP3 which typically include qualifying simulations.
          </p>
        </div>
      )}

      {/* Chart */}
      {!isLoading && !isError && hasData && (
        <div style={CHART_CONTAIN_STYLE}>
          <PlotlyLazy
            data={traces}
            layout={layout}
            config={BASE_CONFIG}
            style={{ width: '100%' }}
          />
        </div>
      )}

      {/* Session verification footnote */}
      {!isLoading && !isError && hasLongRunSessionBest && (
        <p className="text-xs text-gray-500 mt-1">
          * Driver&apos;s overall session best set during a long run stint
        </p>
      )}

      {/* How to read this chart guide */}
      {!isLoading && !isError && hasData && (
        <div className="mt-2">
          <button
            onClick={() => setShowGuide(!showGuide)}
            className="text-xs text-gray-500 hover:text-gray-400 transition-colors flex items-center gap-1"
          >
            <span
              className="inline-block transition-transform duration-200"
              style={{ transform: showGuide ? 'rotate(90deg)' : 'rotate(0deg)' }}
            >
              &#9656;
            </span>
            How to read this chart
          </button>
          {showGuide && (
            <div className="mt-2 p-3 rounded border border-white/10 bg-white/[0.02] text-sm text-gray-500 space-y-2">
              <div>
                <span className="text-gray-400 font-medium">What this chart shows: </span>
                Each bar represents a driver&apos;s official session-best lap time,
                sourced from FIA timing data. Times are raw (not fuel-corrected)
                to match the official session classification. Bars are coloured by
                team. The fastest driver (P1) appears at the top, with the
                slowest at the bottom.
              </div>
              <div>
                <span className="text-gray-400 font-medium">How to read the bars: </span>
                The x-axis is zoomed in to start near the fastest lap time rather
                than at zero. This magnifies the differences between drivers, making
                the competitive spread visible. Start at the top bar (P1) to see the
                benchmark lap time, then compare how each bar below extends further
                to the right — a longer bar means a slower lap.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Gap to P1: </span>
                The fastest driver&apos;s bar shows only the absolute lap time.
                Every other driver shows their lap time followed by the gap to
                P1 (e.g. +0.667s). This gap is the key comparison metric — it
                tells you how far behind each driver was from the fastest on
                pure single-lap pace. A smaller gap indicates closer competitive
                pace.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Compound badges: </span>
                The coloured circle to the left of each bar indicates the tyre
                compound used on the best lap: S = Soft (fastest tyre, least
                durable), M = Medium (balanced), H = Hard (slowest tyre, most
                durable). Compare drivers on the same compound for a fairer
                comparison — a driver fastest on Medium tyres may have more
                potential than one fastest on Softs.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Session verification: </span>
                Times and ranking are anchored to the official session classification.
                A ✓ indicates the driver&apos;s session best came from a short run
                stint (qualifying simulation — the expected scenario). A * indicates
                the session best was set during a long run stint (race simulation),
                meaning the driver may not have attempted a dedicated qualifying
                simulation run.
              </div>
              <div>
                <span className="text-gray-400 font-medium">What to look for: </span>
                Focus on the gaps rather than absolute times. Look for clusters of
                drivers with similar gaps — these groups are likely to be closely
                matched in qualifying. A driver with a large gap may be running a
                different programme (high fuel, conservative engine mode) rather
                than genuinely lacking pace.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Important caveat: </span>
                Practice short run times should be interpreted with caution.
                Teams run varying fuel loads and engine modes during practice,
                so the true single-lap competitive picture is only fully revealed
                in qualifying. Use this chart as an indicator of potential pace,
                not a definitive prediction.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
