'use client'

import { useState, useMemo } from 'react'
import { useLongRunQuery } from '@/lib/hooks/useLongRunQuery'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import {
  BASE_LAYOUT,
  BASE_AXIS,
  BASE_CONFIG,
} from '@/lib/plotlyTheme'
import { getCompoundColor, COMPOUND_DISPLAY_NAMES } from '@/lib/compounds'
import { getTeamColor } from '@/lib/drivers'
import { formatLapTime } from '@/lib/formatters'
import { getRaceCircuitName } from '@/data/tracks/race-lookup'
import CompoundTabs from '@/components/race/CompoundTabs'
import type { PracticeLongRunStint } from '@/../../packages/models/src/types'

interface LongRunPacePanelProps {
  sessionId: string
  fuelEffect: number
  fuelCorrected: boolean
}

/**
 * Long Run Pace Comparison panel.
 *
 * Renders violin plots with team-coloured fills where each violin
 * represents one driver-stint (>= 4 push laps). Each violin uses Plotly's
 * native `points: 'all'` to render individual lap dots in compound
 * colours. Non-representative stints (installation laps, sensor runs) are
 * filtered out by the backend. Sorted by average pace (fastest left),
 * with hover tooltips showing average, median, gap, and stint statistics.
 */
export default function LongRunPacePanel({
  sessionId,
  fuelEffect,
  fuelCorrected,
}: LongRunPacePanelProps) {
  // Fetch long run data
  const {
    data,
    isLoading,
    isError,
    error,
    isPlaceholderData,
  } = useLongRunQuery(sessionId, fuelEffect > 0 ? fuelEffect : undefined)

  // Compound filter state
  const [selectedCompound, setSelectedCompound] = useState('ALL')

  // How-to-read guide toggle
  const [showGuide, setShowGuide] = useState(false)

  // Get available compounds from data
  const availableCompounds = useMemo(() => {
    if (!data?.stints?.length) return []
    const compounds = new Set(data.stints.map((s) => s.compound).filter(Boolean) as string[])
    return ['ALL', ...Array.from(compounds).sort()]
  }, [data])

  // Filter stints by selected compound
  const filteredStints = useMemo(() => {
    if (!data?.stints) return []
    if (selectedCompound === 'ALL') return data.stints
    return data.stints.filter((s) => s.compound === selectedCompound)
  }, [data, selectedCompound])

  // Build Plotly traces — single violin per stint with team-coloured fill
  const traces = useMemo(() => {
    const allTraces: Array<Record<string, unknown>> = []

    filteredStints.forEach((stint, idx) => {
      const teamColor = getTeamColor(stint.driver)
      const compoundColor = getCompoundColor(stint.compound ?? '')
      const lapTimes = stint.lapTimes?.map((lp) => lp.lapTime) ?? []

      // Skip stints with no individual lap data
      if (lapTimes.length === 0) return

      // Per-point hover text
      const pointTexts = stint.lapTimes?.map((lp) =>
        `<b>Lap ${lp.lapNumber}</b><br>${formatLapTime(lp.lapTime)}<br>${lp.compound ?? 'Unknown'}${lp.inTraffic ? '<br><i>In traffic</i>' : ''}`
      ) ?? []

      // Single violin trace — team-coloured body, compound-coloured dots
      allTraces.push({
        type: 'violin' as const,
        name: stint.driver,
        showlegend: false,
        y: lapTimes,
        x: lapTimes.map(() => idx),
        box: { visible: false },
        meanline: { visible: false },
        points: 'all',
        jitter: 0.12,
        pointpos: 0,
        side: 'both',
        fillcolor: teamColor + '4D', // ~30% opacity (matches Race box plot)
        line: { color: teamColor, width: 1.5 },
        marker: {
          color: compoundColor,
          size: 6,
          opacity: 0.9,
          line: { width: 0.5, color: 'rgba(0,0,0,0.3)' },
        },
        hoveron: 'points+violins',
        hoverinfo: 'text',
        hovertext: pointTexts,
        text: buildViolinHoverText(stint),
        bandwidth: 0.15,
        spanmode: 'hard',
        width: 0.5,
        scalemode: 'width',
        scalegroup: 'stints',
      })
    })

    return allTraces
  }, [filteredStints])

  // Compute y-axis range using percentiles (P2/P98) for tight bounds
  const yAxisRange = useMemo(() => {
    const allTimes: number[] = []
    filteredStints.forEach((stint) => {
      stint.lapTimes?.forEach((lp) => {
        allTimes.push(lp.lapTime)
      })
    })
    if (allTimes.length === 0) return [80, 100]

    allTimes.sort((a, b) => a - b)
    const p2Idx = Math.floor(allTimes.length * 0.02)
    const p98Idx = Math.min(
      Math.ceil(allTimes.length * 0.98),
      allTimes.length - 1
    )
    const p2 = allTimes[p2Idx]
    const p98 = allTimes[p98Idx]

    return [p2 - 0.5, p98 + 1.5]
  }, [filteredStints])

  // Build Plotly layout
  const layout = useMemo(
    () => ({
      ...BASE_LAYOUT,
      height: 550,
      margin: { l: 60, r: 20, t: 60, b: 60 },
      title: {
        text: formatChartTitle(sessionId),
        font: { color: '#D1D5DB', size: 14 },
        x: 0.5,
        xanchor: 'center' as const,
      },
      showlegend: false,
      xaxis: {
        ...BASE_AXIS,
        tickvals: filteredStints.map((_, i) => i),
        ticktext: filteredStints.map(
          (s) => `${s.driver} Stint ${s.displayStintNumber}`
        ),
        tickangle: filteredStints.length > 8 ? -45 : 0,
        tickfont: { size: 10, color: '#9CA3AF' },
        automargin: true,
        showgrid: false,
        range: [-0.6, filteredStints.length - 0.4],
      },
      yaxis: {
        ...BASE_AXIS,
        title: {
          text: fuelCorrected ? 'Fuel-Corrected Lap Time (s)' : 'Lap Time (s)',
          font: { color: '#9CA3AF', size: 12 },
        },
        range: yAxisRange,
        autorange: false,
      },
      violinmode: 'overlay',
      violingap: 0.3,
    }),
    [filteredStints, fuelCorrected, sessionId, yAxisRange]
  )

  const config = BASE_CONFIG

  // --- RENDER ---

  // Loading state
  if (isLoading && !data) {
    return (
      <section className="card-panel">
        <h2 className="card-panel-header">Long Run Pace Comparison</h2>
        <div className="h-[550px] skeleton rounded-lg" />
      </section>
    )
  }

  // Error state
  if (isError) {
    return (
      <section className="card-panel">
        <h2 className="card-panel-header">Long Run Pace Comparison</h2>
        <div className="h-[550px] flex items-center justify-center text-red-400 text-sm">
          <div className="text-center">
            <p>Failed to load long run data</p>
            <p className="text-gray-500 mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </section>
    )
  }

  // Empty state
  if (!data || data.stints.length === 0) {
    return (
      <section className="card-panel">
        <h2 className="card-panel-header">Long Run Pace Comparison</h2>
        <div className="h-[300px] flex items-center justify-center text-gray-500 text-sm">
          <div className="text-center">
            <p>No long runs (4+ push laps) found for this session</p>
            <p className="text-gray-600 mt-1">
              Long runs require at least 4 consecutive valid racing laps on the same compound
            </p>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section
      className={`card-panel transition-opacity duration-300 ${
        isPlaceholderData ? 'opacity-50' : 'opacity-100'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="card-panel-header">Long Run Pace Comparison</h2>
          <p className="text-xs text-gray-500 mt-1">
            {fuelCorrected ? '(approximate fuel correction applied)' : '(raw lap times)'}
            {' · '}
            {data.stints.length} long run stint{data.stints.length !== 1 ? 's' : ''} detected
          </p>
          {data.stintsFilteredCount > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">
              Showing {data.stints.length} of {data.totalLongRunsDetected} long run
              stints ({data.stintsFilteredCount} non-representative excluded)
            </p>
          )}
        </div>
      </div>

      {/* Compound Tabs */}
      {availableCompounds.length > 2 && (
        <div className="mb-4">
          <CompoundTabs
            compounds={availableCompounds}
            activeCompound={selectedCompound}
            onCompoundChange={setSelectedCompound}
          />
        </div>
      )}

      {/* Filtered empty state */}
      {filteredStints.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center text-gray-500 text-sm">
          No long runs found on {COMPOUND_DISPLAY_NAMES[selectedCompound] ?? selectedCompound} compound
        </div>
      ) : (
        <>
          {/* Violin Plot — scrollable for many stints */}
          <div className="overflow-x-auto">
            <div style={{ minWidth: `${Math.max(900, filteredStints.length * 55)}px` }}>
              <PlotlyLazy
                data={traces}
                layout={layout}
                config={config}
                style={{ width: '100%', height: '550px' }}
                useResizeHandler
              />
            </div>
          </div>

          {/* Team Legend (violin fill) + Compound Legend (dots) */}
          <div className="mt-2 space-y-1.5">
            <div className="flex gap-3 flex-wrap text-xs text-gray-400">
              {deduplicateTeams(filteredStints).map(({ team, color }) => (
                <div key={team} className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-3 h-3 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="whitespace-nowrap">{team}</span>
                </div>
              ))}
            </div>
            <div className="flex gap-3 flex-wrap text-xs text-gray-500">
              {availableCompounds.filter(c => c !== 'ALL').map(compound => (
                <div key={compound} className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: getCompoundColor(compound) }}
                  />
                  <span className="whitespace-nowrap">
                    {COMPOUND_DISPLAY_NAMES[compound] ?? compound} (dots)
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Stint Summary Cards */}
          <div className="mt-4 flex gap-3 overflow-x-auto pb-2">
            {filteredStints.map((stint) => (
              <StintCard key={`${stint.driver}-${stint.stintNumber}`} stint={stint} />
            ))}
          </div>

          {/* -- How to Read Guide (collapsible) -- */}
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
              {/* What this chart shows */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  What This Chart Shows
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    Each violin shape represents a single{' '}
                    <span className="text-gray-400 font-medium">long-run stint</span> —
                    a sequence of four or more consecutive push laps on the same
                    tyre compound. Long runs are the closest practice comes to
                    simulating actual race pace, making them the most valuable
                    data points for predicting race-day performance.
                  </p>
                  <p>
                    A driver may appear more than once if they completed multiple
                    long runs (e.g. on different compounds or across separate
                    stints). Violins are sorted left to right by average pace,
                    fastest first. Non-representative stints (installation laps,
                    sensor runs) are automatically excluded.
                  </p>
                </div>
              </div>

              {/* Reading the violins */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Reading the Violins
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Shape width</span> — The
                    wider the violin at a given lap time, the more laps the driver
                    completed at that pace. A narrow shape indicates highly consistent
                    performance; a wide, spread shape signals more variation.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Coloured dots</span> — Individual
                    laps are shown as dots inside the violin shape. Dot colour
                    matches the tyre compound of the stint — red for Soft, yellow
                    for Medium, white/grey for Hard. Hover over a dot to see lap
                    number and time.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Violin fill</span> — The
                    fill colour matches the driver&apos;s team — making it easy to
                    identify which team each stint belongs to at a glance, consistent
                    with the Race page. Individual dots inside still show the tyre
                    compound colour.
                  </p>
                </div>
              </div>

              {/* Stint summary cards */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Stint Summary Cards
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Avg</span> — Mean
                    lap time across all push laps in the stint.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Gap</span> — Time
                    difference to the fastest long-run stint in the session.
                    The reference stint shows &ldquo;Fastest&rdquo;.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Push</span> — Number
                    of push laps included in the statistics (excludes warm-up,
                    in/out laps, and anomalies).
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">SD</span> — Standard
                    deviation of lap times within the stint. Lower values indicate
                    more consistent pace — a hallmark of strong race-simulation runs.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Deg</span> — Degradation
                    hint: average of the last two laps minus the average of the
                    first two. A positive value (red) means the driver was getting
                    slower — indicating tyre wear. A negative value (green) means
                    improving — likely track evolution or tyre warm-up.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Air</span> — Percentage
                    of laps completed in clean air (no car within 1.5&nbsp;s ahead).
                    High clean-air stints are more representative of true pace.
                  </p>
                </div>
              </div>

              {/* Fuel correction */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Fuel Correction
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    Unlike race sessions where the starting fuel load is known,
                    practice stints begin with varying and unknown fuel quantities.
                    When fuel correction is enabled, an approximate adjustment is
                    applied using an estimated burn rate of ~1.6&nbsp;kg per lap and the
                    circuit-specific fuel-effect value from our track database.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">When enabled</span> —
                    Lap times are adjusted to an end-of-stint (lightest fuel)
                    equivalent, helping to isolate the tyre degradation trend that
                    would otherwise be partially masked by the car getting lighter.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">When disabled</span> —
                    Raw lap times are shown as recorded. Earlier laps in a stint
                    may appear slower due to higher fuel load, which can obscure
                    the true rate of tyre wear.
                  </p>
                  <p className="text-gray-500/80 italic">
                    This is a within-stint approximation. Actual fuel loads vary
                    by run plan and are not published, so the correction provides
                    a directional improvement rather than an exact adjustment.
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}


// =============================================================================
// Helper Components
// =============================================================================


function StintCard({ stint }: { stint: PracticeLongRunStint }) {
  const teamColor = getTeamColor(stint.driver)
  const compoundColor = getCompoundColor(stint.compound ?? '')

  return (
    <div
      className="flex-shrink-0 w-[180px] rounded-lg border border-white/10 bg-white/[0.03] p-3"
      style={{ borderTopColor: teamColor, borderTopWidth: '3px' }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm text-white">
          {stint.driver}{' '}
          <span className="text-gray-500 font-normal">S{stint.displayStintNumber}</span>
        </span>
        <span
          className="text-xs font-medium px-1.5 py-0.5 rounded"
          style={{ backgroundColor: compoundColor + '33', color: compoundColor }}
        >
          {stint.compound?.[0] ?? '?'}
        </span>
      </div>

      <div className="text-xs space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-500">Avg</span>
          <span className="text-gray-300 font-mono">{formatLapTime(stint.averageTime)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Gap</span>
          <span className={`font-mono ${stint.gapToFastest === 0 ? 'text-green-400' : 'text-gray-300'}`}>
            {stint.gapToFastest === 0 ? 'Fastest' : `+${stint.gapToFastest.toFixed(3)}`}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Push</span>
          <span className="text-gray-300">{stint.validLapCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">SD</span>
          <span className="text-gray-300 font-mono">{stint.stats.stdDev.toFixed(3)}s</span>
        </div>
        {stint.degradationHint != null && (
          <div className="flex justify-between">
            <span className="text-gray-500">Deg</span>
            <span className={`font-mono ${stint.degradationHint > 0 ? 'text-red-400' : 'text-green-400'}`}>
              {stint.degradationHint > 0 ? '+' : ''}
              {stint.degradationHint.toFixed(3)}s
            </span>
          </div>
        )}
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Air</span>
          <span className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${getCleanAirColorClass(stint.cleanAirPct)}`}
            />
            <span className="text-gray-300">{Math.round(stint.cleanAirPct * 100)}%</span>
          </span>
        </div>
      </div>
    </div>
  )
}


// =============================================================================
// Helper Functions
// =============================================================================


/**
 * Build hover text for the violin body (hoveron: 'violins').
 */
function buildViolinHoverText(stint: PracticeLongRunStint): string {
  const parts = [
    `<b>${stint.driver}</b> Stint ${stint.displayStintNumber} (${stint.compound ?? 'Unknown'})`,
    `Avg: ${formatLapTime(stint.averageTime)}`,
    `Median: ${formatLapTime(stint.stats.median)}`,
    `SD: ${stint.stats.stdDev.toFixed(3)}s`,
    stint.gapToFastest > 0 ? `Gap: +${stint.gapToFastest.toFixed(3)}s` : '<b>Fastest</b>',
    `Push Laps: ${stint.validLapCount}`,
    stint.degradationHint != null
      ? `Deg: ${stint.degradationHint > 0 ? '+' : ''}${stint.degradationHint.toFixed(3)}s`
      : null,
    `Clean air: ${Math.round(stint.cleanAirPct * 100)}%`,
  ]
  return parts.filter(Boolean).join('<br>')
}


/**
 * Format chart title from session ID.
 * E.g. "2025_1_FP2" -> "Long Run Pace - Albert Park Grand Prix Circuit (FP2) 2025"
 */
function formatChartTitle(sessionId: string): string {
  const parts = sessionId.split('_')
  if (parts.length >= 3) {
    const [year, roundStr, session] = parts
    const round = parseInt(roundStr)
    const name = getRaceCircuitName(round)
    return name
      ? `Long Run Pace \u2014 ${name} (${session}) ${year}`
      : `Long Run Pace \u2014 Round ${round} (${session}) ${year}`
  }
  return 'Long Run Pace'
}


/**
 * Deduplicate teams from stints — returns one entry per team with colour.
 * Matches the pattern from RacePaceBoxPlot.tsx.
 */
function deduplicateTeams(
  stints: PracticeLongRunStint[]
): { team: string; color: string }[] {
  const seen = new Map<string, string>()
  for (const s of stints) {
    const team = s.team ?? 'Unknown'
    if (!seen.has(team)) {
      seen.set(team, getTeamColor(s.driver))
    }
  }
  return Array.from(seen.entries()).map(([team, color]) => ({ team, color }))
}


function getCleanAirColorClass(pct: number): string {
  if (pct >= 0.8) return 'bg-green-400'
  if (pct >= 0.5) return 'bg-amber-400'
  return 'bg-red-400'
}
