'use client'

import { useState, useMemo, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import {
  BASE_LAYOUT,
  BASE_AXIS,
  BASE_CONFIG,
  CHART_CONTAIN_STYLE,
} from '@/lib/plotlyTheme'
import { getTeamColorForMode } from '@/lib/drivers'
import { getCompoundColor } from '@/lib/compounds'
import { formatLapTime } from '@/lib/formatters'
import { useSessionProgressionQuery } from '@/lib/hooks/useSessionProgressionQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'
import AnalysisModeToggle from '@/components/race/AnalysisModeToggle'
import DriverChipSelector from '@/components/race/DriverChipSelector'
import type {
  PracticeProgressionDriver,
  PracticeProgressionEntry,
} from '@/../../packages/models/src/types'

interface SessionProgressionPanelProps {
  year: number
  round: number
}

/**
 * Session Progression panel — connected dot plot showing each driver's
 * gap-to-session-best across FP1, FP2, and FP3.
 *
 * Answers: how did each driver's single-lap pace evolve across the
 * practice weekend? Uses gap-to-session-best (not raw times) to
 * neutralise track evolution between sessions.
 *
 * Sprint weekends (FP1 only): shows a ranked list instead of a chart.
 */
export default function SessionProgressionPanel({
  year,
  round,
}: SessionProgressionPanelProps) {
  const { containerRef, isVisible } = useVisibility()

  const {
    data,
    isLoading,
    isError,
  } = useSessionProgressionQuery(year, round, isVisible)

  const [showGuide, setShowGuide] = useState(false)

  // ── URL state persistence (sp = session-progression) ──────────────
  const router = useRouter()
  const searchParams = useSearchParams()
  const pathname = usePathname()

  const urlMode = (searchParams.get('spMode') as 'driver' | 'team') || 'driver'
  const urlDrivers = searchParams.get('spDrivers')?.split(',').filter(Boolean) || []

  const [mode, setMode] = useState<'driver' | 'team'>(urlMode)
  const [selectedIdentifiers, setSelectedIdentifiers] = useState<string[]>(urlDrivers)
  const [userHasFiltered, setUserHasFiltered] = useState(urlDrivers.length > 0)

  // ── Derived state ─────────────────────────────────────────────────
  const hasData = data && data.drivers.length > 0
  const isSprint = data?.isSprintWeekend ?? false

  // Extract all identifiers from response (driver abbrevs or team names)
  const allIdentifiers = useMemo(() => {
    if (!data) return []
    const ids = new Set<string>()
    for (const driver of data.drivers) {
      ids.add(mode === 'driver' ? driver.driver : driver.team)
    }
    return Array.from(ids).sort()
  }, [data, mode])

  // ── URL update helper ─────────────────────────────────────────────
  const updateProgressionURL = useCallback(
    (newMode: string, newDrivers: string[]) => {
      const params = new URLSearchParams(searchParams.toString())
      params.set('spMode', newMode)
      // Only persist selection when it's a subset (all-selected is the default)
      if (newDrivers.length > 0 && newDrivers.length < allIdentifiers.length) {
        params.set('spDrivers', newDrivers.join(','))
      } else {
        params.delete('spDrivers')
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false })
    },
    [searchParams, pathname, router, allIdentifiers.length]
  )

  // ── Handlers ──────────────────────────────────────────────────────
  const handleModeChange = useCallback(
    (newMode: 'driver' | 'team') => {
      setMode(newMode)
      setUserHasFiltered(false)
      setSelectedIdentifiers([])
      updateProgressionURL(newMode, [])
    },
    [updateProgressionURL]
  )

  const handleSelectionChange = useCallback(
    (selected: string[]) => {
      setSelectedIdentifiers(selected)
      setUserHasFiltered(true)
      updateProgressionURL(mode, selected)
    },
    [mode, updateProgressionURL]
  )

  // ── Auto-select + validation ──────────────────────────────────────
  // When data arrives: auto-populate all if user hasn't manually filtered.
  // On GP change: allIdentifiers change → prune invalid, fallback to all.
  useEffect(() => {
    if (allIdentifiers.length > 0) {
      if (userHasFiltered && selectedIdentifiers.length > 0) {
        const valid = selectedIdentifiers.filter((id) => allIdentifiers.includes(id))
        if (valid.length === 0) {
          setSelectedIdentifiers(allIdentifiers)
          setUserHasFiltered(false)
        } else if (valid.length !== selectedIdentifiers.length) {
          setSelectedIdentifiers(valid)
        }
      } else if (!userHasFiltered) {
        setSelectedIdentifiers(allIdentifiers)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allIdentifiers])

  // ── Filter drivers by selection ───────────────────────────────────
  const filteredDrivers = useMemo(() => {
    if (!data) return []
    return data.drivers.filter((d) =>
      mode === 'driver'
        ? selectedIdentifiers.includes(d.driver)
        : selectedIdentifiers.includes(d.team)
    )
  }, [data, selectedIdentifiers, mode])

  // Build chart traces and layout from filtered drivers
  const { traces, layout } = useMemo(() => {
    if (!hasData || isSprint || filteredDrivers.length === 0) {
      return { traces: [], layout: {} }
    }
    return buildProgressionChart(filteredDrivers, data.availableSessions)
  }, [filteredDrivers, data, hasData, isSprint])

  // ── Loading skeleton ───────────────────────────────────────────────
  if (isLoading) {
    return (
      <div ref={containerRef} className="content-defer">
        <div className="card-panel">
          <div className="animate-pulse space-y-3">
            <div className="h-5 w-52 rounded bg-f1gray/30" />
            <div className="h-3 w-80 rounded bg-f1gray/20" />
            <div className="mt-4 h-[380px] rounded bg-f1gray/10" />
          </div>
        </div>
      </div>
    )
  }

  // ── Error state ────────────────────────────────────────────────────
  if (isError || !data) {
    return (
      <div ref={containerRef} className="content-defer">
        <div className="card-panel">
          <h2 className="card-panel-header !mb-0">Session Progression</h2>
          <p className="mt-2 text-sm text-gray-500">
            Session progression data unavailable for this weekend.
          </p>
        </div>
      </div>
    )
  }

  // ── Sprint weekend ─────────────────────────────────────────────────
  if (isSprint || data.availableSessions.length === 1) {
    return (
      <div ref={containerRef} className="content-defer">
        <div className="card-panel">
          <h2 className="card-panel-header !mb-0">Session Progression</h2>
          <p className="mt-1 text-xs text-gray-500">
            Sprint Weekend — FP1 only. Cross-session progression requires
            multiple practice sessions.
          </p>
          {hasData && <SprintProgressionList drivers={data.drivers} />}
        </div>
      </div>
    )
  }

  // ── Empty state ────────────────────────────────────────────────────
  if (!hasData) {
    return (
      <div ref={containerRef} className="content-defer">
        <div className="card-panel">
          <h2 className="card-panel-header !mb-0">Session Progression</h2>
          <p className="mt-4 text-sm text-gray-500">
            No progression data available for this weekend.
          </p>
        </div>
      </div>
    )
  }

  // ── Chart ──────────────────────────────────────────────────────────
  return (
    <div ref={containerRef} className="content-defer">
      <div className="card-panel">
        {/* Panel Header */}
        <div className="mb-3">
          <h2 className="card-panel-header !mb-0">Session Progression</h2>
          <p className="mt-1 text-xs text-gray-500">
            Gap to each session&apos;s fastest lap. Accounts for track evolution
            across FP1, FP2, and FP3.
          </p>
        </div>

        {/* Mode toggle + Driver/Team selector */}
        <div className="mb-3 space-y-3">
          <AnalysisModeToggle mode={mode} onModeChange={handleModeChange} />
          <DriverChipSelector
            identifiers={allIdentifiers}
            selectedIdentifiers={selectedIdentifiers}
            onSelectionChange={handleSelectionChange}
            mode={mode}
            displayMode="inline"
          />
        </div>

        {/* Connected dot plot or empty selection message */}
        {filteredDrivers.length === 0 ? (
          <p className="mt-4 text-sm text-gray-500">
            Select at least one {mode === 'driver' ? 'driver' : 'team'} to display the chart.
          </p>
        ) : (
          <div style={CHART_CONTAIN_STYLE}>
            <PlotlyLazy
              data={traces}
              layout={layout}
              config={BASE_CONFIG}
              style={{ width: '100%', height: '420px' }}
              useResizeHandler
            />
          </div>
        )}

        {/* How to read this chart guide */}
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
                Each line connects a driver&apos;s gap-to-session-best across
                FP1, FP2, and FP3. A driver appearing closer to the top (0.000s)
                was more competitive in that session relative to the field.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Why gap-to-session-best: </span>
                Raw lap times decrease across sessions as the track rubbers in
                (track evolution). Using the gap to each session&apos;s fastest
                driver neutralises this effect and shows relative competitiveness.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Compound indicators: </span>
                The filled dot colour shows the tyre compound used on the
                driver&apos;s best lap in each session. Softer compounds are
                expected to produce faster laps.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Driver / Team filtering: </span>
                Use the mode toggle to switch between individual driver and team
                views. Click chips to remove, or use the + button to add back
                specific drivers or teams for targeted comparisons.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


// ─── Chart builder ───────────────────────────────────────────────────────────

function buildProgressionChart(
  drivers: PracticeProgressionDriver[],
  availableSessions: string[],
): { traces: Record<string, unknown>[]; layout: Record<string, unknown> } {
  const traces: Record<string, unknown>[] = []

  for (const driver of drivers) {
    const teamColor = getTeamColorForMode(driver.team, 'team')

    const sessionMap = new Map(
      driver.sessions.map((s) => [s.session, s])
    )

    const xPoints: string[] = []
    const yPoints: number[] = []
    const markerColors: string[] = []
    const hoverTexts: string[] = []

    for (const session of availableSessions) {
      const entry = sessionMap.get(session)
      if (!entry) continue  // Driver absent from this session — skip dot

      xPoints.push(session)
      yPoints.push(entry.gapToSessionBest)
      markerColors.push(getCompoundColor(entry.compound))
      hoverTexts.push(buildHoverText(driver.driver, entry))
    }

    if (xPoints.length === 0) continue

    // Trace 1: connecting line (team-coloured, no markers)
    // Only render if driver has 2+ sessions — single point has no line
    if (xPoints.length > 1) {
      traces.push({
        type: 'scatter' as const,
        mode: 'lines' as const,
        x: xPoints,
        y: yPoints,
        name: driver.driver,
        line: {
          color: teamColor,
          width: 1.5,
        },
        showlegend: false,
        hoverinfo: 'none',
      })
    }

    // Trace 2: compound-coloured markers (one per data point)
    traces.push({
      type: 'scatter' as const,
      mode: 'markers' as const,
      x: xPoints,
      y: yPoints,
      name: driver.driver,
      marker: {
        color: markerColors,
        size: 10,
        line: {
          color: teamColor,
          width: 2,
        },
      },
      hoverinfo: 'text',
      hovertext: hoverTexts,
      showlegend: true,
    })
  }

  const allGaps = drivers.flatMap((d) =>
    d.sessions.map((s) => s.gapToSessionBest)
  )
  const maxGap = Math.max(...allGaps, 0)
  // Y-axis range: 0 (fastest) to maxGap + 0.3s padding
  const yMax = Math.ceil((maxGap + 0.3) * 10) / 10

  const layout: Record<string, unknown> = {
    ...BASE_LAYOUT,
    showlegend: true,
    legend: {
      orientation: 'h' as const,
      y: -0.18,
      x: 0.5,
      xanchor: 'center' as const,
      font: { color: '#9CA3AF', size: 11 },
    },
    xaxis: {
      ...BASE_AXIS,
      type: 'category' as const,
      categoryorder: 'array' as const,
      categoryarray: availableSessions,
      title: { text: 'Practice Session', font: { color: '#9CA3AF', size: 12 } },
      tickfont: { color: '#9CA3AF', size: 12 },
    },
    yaxis: {
      ...BASE_AXIS,
      title: {
        text: 'Gap to Session Best (s)',
        font: { color: '#9CA3AF', size: 12 },
      },
      range: [yMax, -0.05],   // Inverted: smaller gap (better) at top
      tickfont: { color: '#9CA3AF', size: 11 },
      tickformat: '+.3f',
    },
    margin: { t: 20, b: 80, l: 70, r: 20 },
    height: 420,
  }

  return { traces, layout }
}


// ─── Hover text builder ──────────────────────────────────────────────────────

function buildHoverText(
  driverAbbrev: string,
  entry: PracticeProgressionEntry,
): string {
  const gapStr =
    entry.gapToSessionBest === 0
      ? 'Session Best'
      : `+${entry.gapToSessionBest.toFixed(3)}s`

  return [
    `<b>${driverAbbrev} — ${entry.session}</b>`,
    `Lap: ${formatLapTime(entry.bestLapTime)}`,
    `Gap: ${gapStr}`,
    `Compound: ${entry.compound}`,
    `Tyre life: ${entry.tyreLife} laps`,
  ].join('<br>')
}


// ─── Sprint weekend fallback ─────────────────────────────────────────────────

function SprintProgressionList({
  drivers,
}: {
  drivers: PracticeProgressionDriver[]
}) {
  if (!drivers.length) return null

  return (
    <div className="mt-4 space-y-2">
      {drivers.map((d, i) => {
        const entry = d.sessions[0]
        if (!entry) return null
        const teamColor = getTeamColorForMode(d.team, 'team')
        const gapStr =
          entry.gapToSessionBest === 0
            ? 'Session Best'
            : `+${entry.gapToSessionBest.toFixed(3)}s`

        return (
          <div key={d.driver} className="flex items-center gap-3 text-sm">
            <span className="w-5 text-right text-xs text-gray-500">
              {i + 1}
            </span>
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: teamColor }}
            />
            <span className="w-10 font-mono text-white/90">{d.driver}</span>
            <span className="text-gray-500">{formatLapTime(entry.bestLapTime)}</span>
            <span className="ml-auto text-gray-400">{gapStr}</span>
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: getCompoundColor(entry.compound) }}
            />
          </div>
        )
      })}
    </div>
  )
}
