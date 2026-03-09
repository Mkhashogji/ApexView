'use client'

import { useMemo, useState } from 'react'
import PlotlyLazy from '@/components/charts/PlotlyLazy'
import {
  BASE_LAYOUT,
  BASE_AXIS,
  BASE_CONFIG,
  CHART_CONTAIN_STYLE,
} from '@/lib/plotlyTheme'
import { getTeamColorForMode, getTeamColor } from '@/lib/drivers'
import { formatLapTime, formatSectorTime, formatDelta, getDeltaColorClass } from '@/lib/formatters'
import { useSectorAnalysisQuery } from '@/lib/hooks/useSectorAnalysisQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'
import type { PracticeSectorDriver, PracticeSectorSummary, PracticeSpeedTrapDriver } from '@/../../packages/models/src/types'

interface SectorAnalysisPanelProps {
  sessionId: string
}

/**
 * Sector Analysis panel for practice sessions.
 *
 * Three sections:
 * A) Sector times table — all drivers' session-best lap S1/S2/S3 with
 *    fastest-sector purple highlighting, deltas, and potential gain.
 * B) Theoretical best lap card — best individual sectors combined.
 * C) Speed trap comparison — horizontal bar chart of max SpeedST.
 */
export default function SectorAnalysisPanel({
  sessionId,
}: SectorAnalysisPanelProps) {
  const { containerRef, isVisible } = useVisibility()

  const {
    data,
    isLoading,
    isError,
  } = useSectorAnalysisQuery(sessionId, isVisible)

  // How-to-read guide toggle
  const [showGuide, setShowGuide] = useState(false)

  const hasData = data && data.drivers.length > 0

  // ── Sector table helpers ─────────────────────────────────────────────
  const sectorFastests = useMemo(() => {
    if (!hasData) return { s1: null as number | null, s2: null as number | null, s3: null as number | null }
    const s1 = data.summary.fastestSector1
    const s2 = data.summary.fastestSector2
    const s3 = data.summary.fastestSector3
    return { s1, s2, s3 }
  }, [data, hasData])

  const isFastestSector = (driver: PracticeSectorDriver, sectorNum: 1 | 2 | 3) => {
    if (!data) return false
    const summary = data.summary
    if (sectorNum === 1) return driver.sector1 !== null && driver.sector1 === summary.fastestSector1
    if (sectorNum === 2) return driver.sector2 !== null && driver.sector2 === summary.fastestSector2
    return driver.sector3 !== null && driver.sector3 === summary.fastestSector3
  }

  // ── Speed trap chart ─────────────────────────────────────────────────
  const { speedTraces, speedLayout } = useMemo(() => {
    if (!data || data.speedTraps.length === 0)
      return { speedTraces: [], speedLayout: {} }

    // Filter to drivers with valid speed trap, sorted by speed descending
    const validTraps = data.speedTraps
      .filter((st) => st.speedTrap !== null)
      .sort((a, b) => (a.speedTrap ?? 0) - (b.speedTrap ?? 0))

    if (validTraps.length === 0) return { speedTraces: [], speedLayout: {} }

    const fastestSpeed = validTraps[validTraps.length - 1].speedTrap ?? 0

    const barTrace = {
      type: 'bar' as const,
      orientation: 'h' as const,
      x: validTraps.map((st) => st.speedTrap),
      y: validTraps.map((st) => st.driver),
      text: validTraps.map((st) => {
        const speed = st.speedTrap ?? 0
        if (speed === fastestSpeed) return `${speed.toFixed(1)} km/h`
        const gap = speed - fastestSpeed
        return `${speed.toFixed(1)}  ${gap.toFixed(1)} km/h`
      }),
      textposition: 'outside' as const,
      textfont: { color: '#9CA3AF', size: 10 },
      hoverinfo: 'none' as const,
      marker: {
        color: validTraps.map((st) => getTeamColorForMode(st.team, 'team')),
        opacity: 0.9,
      },
      showlegend: false,
    } as Record<string, unknown>

    const chartHeight = Math.min(480, Math.max(220, validTraps.length * 28 + 80))
    const axisMin = validTraps[0].speedTrap
      ? validTraps[0].speedTrap - 5
      : undefined

    const chartLayout = {
      ...BASE_LAYOUT,
      height: chartHeight,
      margin: { l: 55, r: 100, t: 10, b: 40 },
      xaxis: {
        ...BASE_AXIS,
        title: {
          text: 'Speed (km/h)',
          font: { size: 11, color: '#6B7280' },
        },
        range: axisMin ? [axisMin, undefined] : undefined,
        tickformat: '.0f',
      },
      yaxis: {
        ...BASE_AXIS,
        automargin: true,
        tickfont: { size: 11 },
      },
      showlegend: false,
    }

    return { speedTraces: [barTrace], speedLayout: chartLayout }
  }, [data])

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div ref={containerRef} className="card-panel space-y-4 content-defer">
      {/* Panel Header */}
      <div>
        <h2 className="card-panel-header !mb-0">
          Sector Analysis
        </h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Session-best lap broken into sectors, theoretical best lap, and
          speed trap comparison. All times are raw (not fuel-corrected).
        </p>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="animate-pulse space-y-3">
          <div className="h-6 rounded bg-gray-700/50 w-3/4" />
          {[90, 85, 80, 75, 70, 65].map((w, i) => (
            <div
              key={i}
              className="h-7 rounded bg-gray-700/50"
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
          Unable to load sector analysis for this session.
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && !hasData && (
        <div className="flex flex-col items-center justify-center h-36 text-center space-y-2">
          <p className="text-gray-300 text-sm font-medium">
            No sector data available
          </p>
          <p className="text-gray-500 text-xs max-w-xs">
            Sector times may not be available for this session.
          </p>
        </div>
      )}

      {/* ── Section A: Sector Times Table ─────────────────────────────── */}
      {!isLoading && !isError && hasData && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-f1gray text-gray-400 text-xs uppercase tracking-wide">
                <th className="pb-2 text-left font-medium w-8">P</th>
                <th className="pb-2 text-left font-medium">Driver</th>
                <th className="pb-2 text-right font-medium">S1</th>
                <th className="pb-2 text-right font-medium">S2</th>
                <th className="pb-2 text-right font-medium">S3</th>
                <th className="pb-2 text-right font-medium">Lap</th>
                <th className="pb-2 text-right font-medium">Gain</th>
              </tr>
            </thead>
            <tbody>
              {data.drivers.map((d) => (
                <tr key={d.driver} className="border-b border-f1gray/20">
                  {/* Position */}
                  <td className="py-1.5 text-gray-500 text-xs">{d.position}</td>
                  {/* Driver */}
                  <td className="py-1.5">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getTeamColor(d.driver) }}
                        aria-hidden="true"
                      />
                      <span className="font-medium text-sm">{d.driver}</span>
                    </div>
                  </td>
                  {/* S1 */}
                  <td className={`py-1.5 text-right font-mono text-sm ${
                    isFastestSector(d, 1) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {d.sector1 !== null ? (
                      isFastestSector(d, 1)
                        ? formatSectorTime(d.sector1)
                        : <span className={getDeltaColorClass(d.sector1 - (sectorFastests.s1 ?? 0))}>
                            {formatDelta(d.sector1 - (sectorFastests.s1 ?? 0))}
                          </span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  {/* S2 */}
                  <td className={`py-1.5 text-right font-mono text-sm ${
                    isFastestSector(d, 2) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {d.sector2 !== null ? (
                      isFastestSector(d, 2)
                        ? formatSectorTime(d.sector2)
                        : <span className={getDeltaColorClass(d.sector2 - (sectorFastests.s2 ?? 0))}>
                            {formatDelta(d.sector2 - (sectorFastests.s2 ?? 0))}
                          </span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  {/* S3 */}
                  <td className={`py-1.5 text-right font-mono text-sm ${
                    isFastestSector(d, 3) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {d.sector3 !== null ? (
                      isFastestSector(d, 3)
                        ? formatSectorTime(d.sector3)
                        : <span className={getDeltaColorClass(d.sector3 - (sectorFastests.s3 ?? 0))}>
                            {formatDelta(d.sector3 - (sectorFastests.s3 ?? 0))}
                          </span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  {/* Lap Time */}
                  <td className="py-1.5 text-right font-mono text-sm text-gray-300">
                    {formatLapTime(d.lapTime)}
                  </td>
                  {/* Potential Gain */}
                  <td className="py-1.5 text-right font-mono text-xs text-gray-500">
                    {d.potentialGain !== null ? (
                      `${d.potentialGain.toFixed(3)}s`
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Fastest sectors summary */}
      {!isLoading && !isError && hasData && data.summary.fastestSector1Driver && (
        <div className="text-xs text-gray-400 space-y-1">
          <p className="font-medium text-gray-300">Fastest sectors:</p>
          <p>
            S1 <span className="text-purple-sector font-medium">{data.summary.fastestSector1Driver}</span>
            {' | '}
            S2 <span className="text-purple-sector font-medium">{data.summary.fastestSector2Driver}</span>
            {' | '}
            S3 <span className="text-purple-sector font-medium">{data.summary.fastestSector3Driver}</span>
          </p>
        </div>
      )}

      {/* ── Section B: Theoretical Best Lap Card ──────────────────────── */}
      {!isLoading && !isError && hasData && data.summary.theoreticalBestTime !== null && (
        <div className="pt-3 border-t border-f1gray/30">
          <p className="text-xs text-gray-400 uppercase tracking-wide">
            Theoretical Best Lap
          </p>
          <p className="font-mono text-lg font-bold text-purple-sector mt-1">
            {formatLapTime(data.summary.theoreticalBestTime)}
          </p>
          {data.summary.theoreticalGain !== null && (
            <p className="font-mono text-sm text-gray-400 mt-0.5">
              {formatDelta(-data.summary.theoreticalGain)} vs session best
            </p>
          )}
          <p className="text-xs text-gray-500 mt-1.5">
            Combines the fastest individual sectors across all laps and
            drivers — sectors may come from different laps.
          </p>
        </div>
      )}

      {/* ── Section C: Speed Trap Comparison ──────────────────────────── */}
      {!isLoading && !isError && hasData && speedTraces.length > 0 && (
        <div className="pt-3 border-t border-f1gray/30">
          <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-2">
            Speed Trap — Max Speed per Driver
          </h3>
          <div style={CHART_CONTAIN_STYLE}>
            <PlotlyLazy
              data={speedTraces}
              layout={speedLayout}
              config={BASE_CONFIG}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      )}

      {/* ── How to read this chart guide ──────────────────────────────── */}
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
                <span className="text-gray-400 font-medium">Sector table: </span>
                Each row shows a driver&apos;s session-best lap split into three
                sectors (S1, S2, S3). A circuit is divided into three timed
                segments at fixed points around the track. The three sector
                times sum to the total lap time shown in the Lap column.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Purple highlighting: </span>
                The fastest time in each sector column is displayed as an
                absolute time in purple — this is the benchmark for that sector.
                All other drivers show their gap to that benchmark (e.g. +0.123).
                Red deltas indicate the driver is slower in that sector. When three
                different drivers hold the purple time in three different sectors,
                it signals a competitive session where no single car dominates
                everywhere.
              </div>
              <div>
                <span className="text-gray-400 font-medium">How to spot patterns: </span>
                Read across each row to see a driver&apos;s sector profile. A
                driver with small deltas in S1 and S2 but a large red delta in
                S3 is losing time in one specific track section. Read down each
                column to compare all drivers in a single sector — this reveals
                which cars are strong or weak in each part of the circuit.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Potential gain: </span>
                The Gain column shows the difference between each driver&apos;s
                actual session-best lap and their theoretical best (sum of their
                best individual S1 + S2 + S3 across all laps — these may come
                from different laps). A larger number means more time was left
                on the table. In practice this is typically 0.1–0.5s, with higher
                values suggesting the driver did not combine their best performance
                from each sector into a single lap.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Theoretical best lap: </span>
                The purple time shown below the table combines the fastest
                individual sector from any driver across all laps in the session.
                These sectors may come from different drivers on different laps.
                The gap shown beneath it tells you how much faster this
                theoretical lap is compared to the actual session-best — a small
                gap means the fastest driver was already close to extracting
                maximum pace.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Speed trap: </span>
                The bar chart shows the maximum speed (km/h) recorded at the
                speed trap (typically the end of the longest straight) for each
                driver across all laps. The fastest speed is shown as an absolute
                value; others show speed and gap to fastest. Maximum rather than
                average is used because practice includes laps at varying engine
                modes — the maximum represents peak capability. Compare teammates
                to spot different aero configurations being tested.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Cross-referencing: </span>
                Compare the speed trap chart with the sector table. A driver with
                the highest top speed but poor sector times in twisty sections is
                likely running a low-downforce setup (fast on straights, slow in
                corners). The driver with the lowest trap speed but competitive
                sector times has a high-downforce package trading straight-line
                speed for cornering grip.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Important caveat: </span>
                Practice sector times are influenced by fuel load, engine mode,
                and traffic. All times shown are raw (not fuel-corrected) to match
                official timing. The true competitive picture is only fully
                revealed in qualifying.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
