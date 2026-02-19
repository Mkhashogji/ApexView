'use client'

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import { getTeamColor } from '@/lib/drivers'
import { formatLapTime } from '@/lib/formatters'
import { getRaceCircuitName } from '@/data/tracks/race-lookup'
import { COMPOUND_SHORT, COMPOUND_COLOR } from '@/lib/compounds'
import { BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE } from '@/lib/plotlyTheme'
import type { RacePaceResponse, DriverPaceData } from '@/../../packages/models/src/types'

// =============================================================================
// Constants
// =============================================================================

/** Abbreviate tyre compound names for compact display */
function shortCompound(c: string): string {
  return COMPOUND_SHORT[c.toUpperCase()] ?? c.charAt(0)
}

/**
 * Metrics available from DriverPaceData for tooltip display.
 *
 * Available and used:
 *   minTime, q1, median, mean, q3, maxTime, outliers, gapToFastest,
 *   tyreStrategy, consistencyScore, lapsInTraffic, totalRacingLaps,
 *   finishingPosition, team, driver
 *
 * NOT available (omitted from tooltips):
 *   lowerFence / upperFence — not stored separately; minTime/maxTime serve
 *   as whisker bounds (server filters outliers beyond 1.5×IQR).
 *   IQR — not stored; derivable as q3 - q1 but not pre-computed.
 */

// =============================================================================
// Helpers
// =============================================================================

/** Extract unique team→colour pairs preserving driver order */
function deduplicateTeams(drivers: DriverPaceData[]): { team: string; color: string }[] {
  const seen = new Map<string, string>()
  for (const d of drivers) {
    const team = d.team ?? 'Unknown'
    if (!seen.has(team)) {
      seen.set(team, getTeamColor(d.driver))
    }
  }
  return Array.from(seen.entries()).map(([team, color]) => ({ team, color }))
}

/** Format session ID into readable GP title using lightweight lookup */
function formatGPTitle(sessionId: string): string {
  const parts = sessionId.split('_')
  if (parts.length >= 2) {
    const season = parts[0]
    const round = parseInt(parts[1])
    const circuitName = getRaceCircuitName(round)
    if (circuitName) return `${season} ${circuitName}`
    return `${season} Round ${round}`
  }
  return sessionId
}

// =============================================================================
// Tooltip types and state
// =============================================================================

type TooltipTier = 'summary' | 'detailed' | 'outlier'

interface TooltipState {
  visible: boolean
  x: number
  y: number
  driver: DriverPaceData | null
  tier: TooltipTier
  outlierValue?: number
}

const INITIAL_TOOLTIP: TooltipState = {
  visible: false,
  x: 0,
  y: 0,
  driver: null,
  tier: 'summary',
}

// =============================================================================
// Component
// =============================================================================

interface RacePaceBoxPlotProps {
  data: RacePaceResponse
  fuelCorrected: boolean
}

/**
 * Race pace distribution box plot with two-tier hover tooltips,
 * zoom controls, and enhanced "How to read this chart" guide.
 *
 * Layout: React header + team legend → Plotly chart → driver summary strip → guide.
 * One box trace per driver for individual team colouring. Pre-computed server-side statistics.
 *
 * CRITICAL: Box traces must NOT include a `y` array alongside pre-computed stats.
 * Plotly's dimension detection (case '11' in box/defaults.js) treats flat x + flat y
 * as "ill-defined" and sets the trace to visible=false. Using `x` alone with pre-computed
 * q1/median/q3/lowerfence/upperfence hits case '10' which correctly renders one box.
 */
export function RacePaceBoxPlot({ data, fuelCorrected }: RacePaceBoxPlotProps) {
  const drivers = data.drivers
  const [showGuide, setShowGuide] = useState(false)
  const [tooltip, setTooltip] = useState<TooltipState>(INITIAL_TOOLTIP)
  const containerRef = useRef<HTMLDivElement>(null)
  const hideTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current)
    }
  }, [])

  // ── Tooltip handlers ──

  /**
   * Determine tooltip tier based on hover y-value relative to box geometry.
   * - If y is between q1 and q3 → summary (middle region)
   * - If y is outside q1..q3 but within whiskers → detailed
   * - Outlier scatter trace → outlier tier
   */
  const determineTooltipTier = useCallback(
    (yVal: number, driverData: DriverPaceData): TooltipTier => {
      if (yVal >= driverData.q1 && yVal <= driverData.q3) {
        return 'summary'
      }
      return 'detailed'
    },
    []
  )

  const handleHover = useCallback(
    (event: Record<string, unknown>) => {
      // Cancel any pending hide
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current)
        hideTimeoutRef.current = null
      }

      const points = event.points as Array<Record<string, unknown>> | undefined
      if (!points || points.length === 0) return

      const point = points[0]
      const curveNumber = point.curveNumber as number
      const xOnDisplay = (point.xaxis as Record<string, unknown>)?.l2p as
        | ((v: unknown) => number)
        | undefined
      const yOnDisplay = (point.yaxis as Record<string, unknown>)?.l2p as
        | ((v: unknown) => number)
        | undefined

      // Get cursor position from the plotly event
      const evt = event.event as MouseEvent | undefined

      // Determine which driver was hovered
      const isOutlierTrace = curveNumber === drivers.length // outlier is the last trace
      let driverData: DriverPaceData | null = null
      let tier: TooltipTier = 'summary'
      let outlierValue: number | undefined

      if (isOutlierTrace) {
        // Outlier scatter — find matching driver
        const xVal = point.x as string
        driverData = drivers.find((d) => d.driver === xVal) ?? null
        tier = 'outlier'
        outlierValue = point.y as number
      } else if (curveNumber < drivers.length) {
        driverData = drivers[curveNumber]
        const yVal = point.y as number | undefined
        if (driverData && yVal != null) {
          tier = determineTooltipTier(yVal, driverData)
        }
      }

      if (!driverData || !evt) return

      // Position tooltip relative to container
      const containerRect = containerRef.current?.getBoundingClientRect()
      if (!containerRect) return

      const cursorX = evt.clientX - containerRect.left
      const cursorY = evt.clientY - containerRect.top

      setTooltip({
        visible: true,
        x: cursorX,
        y: cursorY,
        driver: driverData,
        tier,
        outlierValue,
      })
    },
    [drivers, determineTooltipTier]
  )

  const handleUnhover = useCallback(() => {
    // Debounced hide — prevents flicker when moving between box elements
    hideTimeoutRef.current = setTimeout(() => {
      setTooltip((prev) => ({ ...prev, visible: false }))
    }, 80)
  }, [])

  // ── Memoised Plotly data ──
  // CRITICAL: traces, layout, and config must be referentially stable across
  // tooltip state changes. Without memoisation, every hover fires setTooltip →
  // React re-render → new layout object with autorange → Plotly resets zoom.
  // By memoising on [drivers, fuelCorrected] only, tooltip state changes
  // do NOT recreate these objects, so Plotly preserves the user's zoom state.

  const teamEntries = useMemo(() => deduplicateTeams(drivers), [drivers])

  const traces = useMemo(() => {
    // ── Box traces: one per driver for individual team colouring ──
    const boxTraces = drivers.map((d: DriverPaceData) => {
      const teamColor = getTeamColor(d.driver)
      return {
        type: 'box' as const,
        name: d.team ?? d.driver,
        x: [d.driver],
        // y intentionally omitted — including it triggers Plotly case '11' (visible=false)
        lowerfence: [d.minTime],
        upperfence: [d.maxTime],
        q1: [d.q1],
        median: [d.median],
        q3: [d.q3],
        mean: [d.mean],
        boxmean: true as const,
        boxpoints: false as const,
        marker: { color: teamColor },
        line: { color: teamColor, width: 1.5 },
        fillcolor: teamColor + '4D',
        // Disable Plotly's built-in tooltip — we render our own
        hoverinfo: 'none' as const,
        showlegend: false,
      }
    })

    // ── Outlier scatter trace ──
    const outlierX: string[] = []
    const outlierY: number[] = []
    const outlierColors: string[] = []

    for (const d of drivers) {
      if (d.outliers && d.outliers.length > 0) {
        for (const t of d.outliers) {
          outlierX.push(d.driver)
          outlierY.push(t)
          outlierColors.push(getTeamColor(d.driver))
        }
      }
    }

    const outlierTrace = {
      type: 'scatter' as const,
      mode: 'markers' as const,
      name: 'Outliers',
      x: outlierX,
      y: outlierY,
      marker: {
        color: outlierColors,
        size: 6,
        symbol: 'circle-open' as const,
        line: { width: 1.5, color: outlierColors },
      },
      hoverinfo: 'none' as const,
      showlegend: false,
    }

    return outlierX.length > 0 ? [...boxTraces, outlierTrace] : boxTraces
  }, [drivers])

  const layout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      height: 450,
      margin: { t: 10, r: 20, b: 50, l: 70 },
      // No size on font — uses Plotly default 12 (box plots need the extra space)
      font: { color: '#9CA3AF', family: 'Inter, sans-serif' },
      xaxis: {
        title: '',
        tickangle: 0,
        ticktext: drivers.map((d) => d.driver),
        tickvals: drivers.map((d) => d.driver),
        tickfont: { size: 12, color: 'rgba(255,255,255,0.85)' },
        showgrid: false,
        automargin: true,
        // Both axes unlocked so brush-to-zoom rectangle works freely.
        // Users drag a rectangle over any region; double-click resets.
        fixedrange: false,
      },
      yaxis: {
        ...BASE_AXIS,
        title: {
          text: fuelCorrected ? 'Fuel-Corrected Lap Time (s)' : 'Lap Time (s)',
          font: { size: 12, color: '#9CA3AF' },
        },
        // NOTE: autorange is intentionally OMITTED here.
        // If present, every React re-render (e.g. tooltip state change) would
        // pass a new layout with autorange:true → Plotly resets the zoom.
        // Plotly auto-ranges on first render when no range is specified.
        // After that, the user's zoom state is preserved until they double-click
        // to reset or the data/session changes (which recreates this memo).
        fixedrange: false,
      },
      boxgap: 0.25,
      boxgroupgap: 0.05,
      // Suppress default hoverlabel since we render custom tooltips
      hoverlabel: {
        bgcolor: 'rgba(0,0,0,0)',
        bordercolor: 'rgba(0,0,0,0)',
        font: { size: 1, color: 'rgba(0,0,0,0)' },
      },
      dragmode: 'zoom' as const,
    }),
    [drivers, fuelCorrected]
  )

  const config = useMemo(() => BASE_CONFIG, [])

  if (!drivers || drivers.length === 0) {
    return (
      <div className="h-[450px] flex items-center justify-center text-gray-500">
        No pace data available
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative">
      {/* ── Header: Title + Subtitle + Team Legend ── */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
        <div>
          <h3 className="text-lg font-bold text-white">
            Race Pace Distribution by Driver
          </h3>
          <p className="text-sm text-gray-400">{formatGPTitle(data.sessionId)}</p>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {teamEntries.map(({ team, color }) => (
            <div key={team} className="flex items-center gap-1.5">
              <span
                className="inline-block w-3 h-3 rounded-sm flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-400 whitespace-nowrap">
                {team}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Plotly Box Plot ── */}
      <PlotlyLazy
        data={traces}
        layout={layout}
        config={config}
        style={CHART_CONTAIN_STYLE}
        onHover={handleHover}
        onUnhover={handleUnhover}
      />

      {/* ── Custom Tooltip Overlay ── */}
      {tooltip.visible && tooltip.driver && (
        <CustomTooltip
          tooltip={tooltip}
          fuelCorrected={fuelCorrected}
          containerRef={containerRef}
        />
      )}

      {/* ── Driver Summary Strip ── */}
      <div className="mt-4 -mx-1 overflow-x-auto">
        <div
          className="flex gap-2 px-1 pb-2"
          style={{ minWidth: 'max-content' }}
        >
          {drivers.map((d) => {
            const teamColor = getTeamColor(d.driver)
            const gap =
              d.gapToFastest < 0.001
                ? '\u2014'
                : `+${d.gapToFastest.toFixed(3)}s`
            const compoundLetters = (d.tyreStrategy || []).map(shortCompound)
            const pos =
              d.finishingPosition != null ? `P${d.finishingPosition}` : ''

            return (
              <div
                key={d.driver}
                className="flex-shrink-0 rounded-md text-center border border-white/10 overflow-hidden"
                style={{
                  borderTopColor: teamColor,
                  borderTopWidth: '3px',
                  minWidth: '72px',
                }}
              >
                <div
                  className="px-2 py-1.5 font-bold text-sm text-white"
                  style={{ backgroundColor: teamColor + '30' }}
                >
                  {d.driver}
                </div>
                <div className="px-2 py-1.5 space-y-0.5 bg-white/[0.03]">
                  <div className="text-[11px] text-gray-400">{gap}</div>
                  <div className="text-[11px] font-semibold tracking-wide">
                    {compoundLetters.map((letter, i) => (
                      <span key={i}>
                        {i > 0 && <span className="text-gray-600">-</span>}
                        <span style={{ color: COMPOUND_COLOR[letter] ?? '#9CA3AF' }}>
                          {letter}
                        </span>
                      </span>
                    ))}
                  </div>
                  <div className="text-[11px] text-gray-500">{pos}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── How to Read Guide (collapsible) ── */}
      <button
        onClick={() => setShowGuide(!showGuide)}
        className="flex items-center gap-2 mt-4 text-sm text-gray-500 hover:text-gray-300 transition-colors"
        type="button"
        aria-expanded={showGuide}
      >
        <span
          className={`inline-block transition-transform duration-200 ${showGuide ? 'rotate-90' : ''}`}
        >
          &#9656;
        </span>
        How to read this chart
      </button>
      {showGuide && (
        <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] p-4 space-y-4">
          {/* Box plot anatomy */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">
              Understanding the Box Plot
            </h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                <span className="text-gray-400 font-medium">Box</span> — The
                middle 50% of racing laps (interquartile range, Q1 to Q3). A
                narrow box means consistent pace; a wide box signals variation.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Solid line</span> — Median
                lap time. This is the most representative measure of a
                driver&apos;s typical race pace because it is not skewed by
                unusually fast or slow laps.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Dashed line / diamond</span> — Mean
                (average) lap time. When the mean is noticeably slower than the
                median, it indicates the driver had some slow outlier laps
                (traffic, mistakes, or safety car restarts).
              </p>
              <p>
                <span className="text-gray-400 font-medium">Whiskers</span> — Extend
                to the fastest and slowest non-outlier laps within 1.5&times;
                IQR from Q1/Q3. This captures the normal operating range.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Circles above box</span> — Outlier
                laps that fall outside the whisker range. Typically caused by
                safety car restarts, heavy traffic, pit in/out effects, or
                driver errors.
              </p>
              <p className="text-gray-500/80">
                Drivers are sorted left to right by mean pace — fastest first.
              </p>
            </div>
          </div>

          {/* Hover guide */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">
              Hover Tooltips
            </h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                <span className="text-gray-400 font-medium">Hover inside the box</span> — Shows
                a compact summary: driver name, median, mean, and gap to the
                leader.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Hover on
                whiskers or outside the box</span> — Shows a detailed breakdown
                with all distribution statistics (min, Q1, median, Q3, max,
                mean), strategy, consistency, and traffic information.
              </p>
            </div>
          </div>

          {/* Zoom guide */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">
              Zoom and Pan
            </h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                <span className="text-gray-400 font-medium">Brush-to-zoom</span> — Click
                and drag a rectangle over any area of the chart to zoom into
                that region. This is the most direct way to focus on a group of
                drivers or a narrow lap-time band.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Scroll wheel</span> — Scroll
                up/down over the chart to zoom in and out smoothly.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Double-click</span> — Resets
                the view back to the full chart showing all drivers and the
                complete lap-time range.
              </p>
              <p>
                The toolbar (top-right on hover) provides additional controls
                including zoom, pan, auto-scale, and reset buttons.
              </p>
            </div>
          </div>

          {/* Fuel correction explanation */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">
              Fuel-Corrected Lap Times
            </h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                F1 cars start a race with approximately 110 kg of fuel,
                consuming around 2 kg per lap. Each kilogram of fuel adds a
                circuit-specific time penalty (typically 0.028&ndash;0.036
                seconds per kg) due to the extra mass the car must carry through
                corners and acceleration zones.
              </p>
              <p>
                <span className="text-gray-400 font-medium">When enabled</span>,
                fuel correction adjusts each lap time by subtracting the
                estimated fuel-mass penalty, normalising all laps to an
                equivalent empty-tank condition. This isolates the tyre
                degradation trend and reveals the driver&apos;s true pace
                trajectory through the race.
              </p>
              <p>
                <span className="text-gray-400 font-medium">When disabled</span>,
                raw lap times are shown as recorded on track. Early-race laps
                will appear slower (heavier fuel load) and later laps faster
                (lighter car), making it harder to compare pace across the race
                distance.
              </p>
              <p className="text-gray-500/80 italic">
                The correction uses a linear fuel-burn model with
                circuit-specific fuel-effect values from our track database.
                It does not account for non-linear effects such as fuel
                flow rate changes or engine mode variations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Custom Tooltip Component
// =============================================================================

function CustomTooltip({
  tooltip,
  fuelCorrected,
  containerRef,
}: {
  tooltip: TooltipState
  fuelCorrected: boolean
  containerRef: React.RefObject<HTMLDivElement | null>
}) {
  const d = tooltip.driver!
  const teamColor = getTeamColor(d.driver)
  const gap =
    d.gapToFastest < 0.001
      ? 'Leader'
      : `+${d.gapToFastest.toFixed(3)}s`
  const strat = (d.tyreStrategy || []).map(shortCompound).join('-')
  // IQR derivable from existing fields
  const iqr = d.q3 - d.q1

  // ── Position tooltip to avoid clipping container edges ──
  const containerWidth = containerRef.current?.offsetWidth ?? 800
  const containerHeight = containerRef.current?.offsetHeight ?? 600
  const tooltipOffset = 16

  // Default: tooltip to the right and slightly below cursor
  let left = tooltip.x + tooltipOffset
  let top = tooltip.y - tooltipOffset

  // Flip horizontally if near right edge (estimated tooltip width ~260px)
  const tooltipWidth = tooltip.tier === 'summary' ? 220 : 260
  if (left + tooltipWidth > containerWidth) {
    left = tooltip.x - tooltipWidth - tooltipOffset
  }

  // Clamp vertically (estimated max tooltip height ~320px)
  const maxTooltipHeight = tooltip.tier === 'summary' ? 120 : 320
  if (top + maxTooltipHeight > containerHeight) {
    top = containerHeight - maxTooltipHeight - 8
  }
  if (top < 0) top = 8

  if (tooltip.tier === 'outlier') {
    return (
      <div
        className="absolute z-50 pointer-events-none rounded-md shadow-xl border overflow-hidden"
        style={{
          left: `${left}px`,
          top: `${top}px`,
          borderColor: teamColor + '60',
          backgroundColor: '#111827',
        }}
      >
        <div className="px-3 py-2" style={{ borderLeft: `3px solid ${teamColor}` }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-white text-sm">{d.driver}</span>
            <span className="text-xs text-gray-500">{d.team ?? ''}</span>
          </div>
          <div className="text-xs text-gray-300">
            {formatLapTime(tooltip.outlierValue!)}
            <span className="text-gray-500 ml-1">(outlier)</span>
          </div>
        </div>
      </div>
    )
  }

  if (tooltip.tier === 'summary') {
    // ── Summary tooltip: compact, shows key stats ──
    return (
      <div
        className="absolute z-50 pointer-events-none rounded-md shadow-xl border overflow-hidden"
        style={{
          left: `${left}px`,
          top: `${top}px`,
          borderColor: teamColor + '60',
          backgroundColor: '#111827',
        }}
      >
        <div className="px-3 py-2" style={{ borderLeft: `3px solid ${teamColor}` }}>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-bold text-white text-sm">{d.driver}</span>
            <span className="text-xs text-gray-500">{d.team ?? ''}</span>
          </div>
          <div className="space-y-0.5 text-xs">
            <TooltipRow label="Median" value={formatLapTime(d.median)} />
            <TooltipRow label="Mean" value={formatLapTime(d.mean)} />
            <TooltipRow label="Gap" value={gap} />
          </div>
          <div className="mt-1.5 text-[10px] text-gray-600">
            {fuelCorrected ? 'fuel-corrected' : 'raw lap times'}
          </div>
        </div>
      </div>
    )
  }

  // ── Detailed tooltip: full distribution breakdown ──
  return (
    <div
      className="absolute z-50 pointer-events-none rounded-md shadow-xl border overflow-hidden"
      style={{
        left: `${left}px`,
        top: `${top}px`,
        borderColor: teamColor + '60',
        backgroundColor: '#111827',
        minWidth: '230px',
      }}
    >
      <div className="px-3 py-2" style={{ borderLeft: `3px solid ${teamColor}` }}>
        {/* Driver header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="font-bold text-white text-sm">{d.driver}</span>
          <span className="text-xs text-gray-500">{d.team ?? ''}</span>
          {d.finishingPosition != null && (
            <span className="ml-auto text-xs text-gray-500">
              P{d.finishingPosition}
            </span>
          )}
        </div>

        {/* Distribution stats */}
        <div className="space-y-0.5 text-xs">
          <TooltipRow label="Min" value={formatLapTime(d.minTime)} muted />
          <TooltipRow label="Q1" value={formatLapTime(d.q1)} />
          <TooltipRow label="Median" value={formatLapTime(d.median)} highlight />
          <TooltipRow label="Q3" value={formatLapTime(d.q3)} />
          <TooltipRow label="Max" value={formatLapTime(d.maxTime)} muted />
        </div>

        <div className="my-1.5 border-t border-white/5" />

        {/* Derived & contextual stats */}
        <div className="space-y-0.5 text-xs">
          <TooltipRow label="Mean" value={formatLapTime(d.mean)} />
          <TooltipRow label="IQR" value={`${iqr.toFixed(3)}s`} />
          <TooltipRow label="Gap" value={gap} />
        </div>

        <div className="my-1.5 border-t border-white/5" />

        {/* Race context */}
        <div className="space-y-0.5 text-xs">
          <TooltipRow label="Strategy" value={strat} />
          <TooltipRow
            label="Consistency"
            value={
              d.consistencyScore != null
                ? `${d.consistencyScore.toFixed(3)}s \u03C3`
                : '\u2014'
            }
          />
          <TooltipRow
            label="Traffic"
            value={`${d.lapsInTraffic ?? 0} / ${d.totalRacingLaps ?? 0} laps`}
          />
          {d.outliers && d.outliers.length > 0 && (
            <TooltipRow label="Outliers" value={`${d.outliers.length} laps`} />
          )}
        </div>

        <div className="mt-1.5 text-[10px] text-gray-600">
          {fuelCorrected ? 'fuel-corrected' : 'raw lap times'}
        </div>
      </div>
    </div>
  )
}

/** Single row in the custom tooltip */
function TooltipRow({
  label,
  value,
  highlight,
  muted,
}: {
  label: string
  value: string
  highlight?: boolean
  muted?: boolean
}) {
  return (
    <div className="flex justify-between gap-4">
      <span className={muted ? 'text-gray-600' : 'text-gray-400'}>{label}</span>
      <span
        className={
          highlight
            ? 'text-white font-semibold tabular-nums'
            : muted
              ? 'text-gray-500 tabular-nums'
              : 'text-gray-300 tabular-nums'
        }
      >
        {value}
      </span>
    </div>
  )
}
