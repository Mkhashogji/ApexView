'use client'

import { useState } from 'react'
import { useVisibility } from '@/lib/hooks/useVisibility'
import { useCircuitSVGQuery } from '@/lib/hooks/useCircuitSVGQuery'
import { useSectorAnalysisQuery } from '@/lib/hooks/useSectorAnalysisQuery'
import { getTrackIntelligence } from '@/data/tracks/index'
import { getRaceCircuitName } from '@/data/tracks/race-lookup'

// =============================================================================
// Default sector colours — fallback when Track Intelligence is unavailable
// =============================================================================

const DEFAULT_SECTOR_COLORS = ['#FF0000', '#0066FF', '#FFCC00'] as const

interface SectorMapPanelProps {
  /** F1 round number (1-24) for SVG lookup + sector colours */
  round: number
  /** Session ID (e.g. "2025_4_FP2") for sector analysis data */
  sessionId: string
}

/**
 * Circuit Map with Sector Highlighting panel.
 *
 * Renders an SVG track map with S1/S2/S3 colour-coded using Track
 * Intelligence sector colours. The fastest driver per sector (from
 * the sector analysis endpoint) is annotated in a legend below the map.
 *
 * Positioned between ShortRunPanel and SectorAnalysisPanel to provide
 * a visual anchor for interpreting sector times spatially.
 *
 * Graceful degradation: if SVG fetch fails or the round has no mapped
 * SVG, the panel renders nothing (returns null).
 */
export default function SectorMapPanel({
  round,
  sessionId,
}: SectorMapPanelProps) {
  const { containerRef, isVisible } = useVisibility()

  // How-to-read guide toggle
  const [showGuide, setShowGuide] = useState(false)

  // Fetch and parse the circuit SVG
  const {
    data: svgData,
    isLoading: svgLoading,
  } = useCircuitSVGQuery(round, isVisible)

  // Reuse sector analysis data for fastest driver per sector
  const {
    data: sectorData,
  } = useSectorAnalysisQuery(sessionId, isVisible)

  // ── Sector colours from Track Intelligence ────────────────────────
  const trackIntel = getTrackIntelligence(round)
  const s1Color = trackIntel?.sectors[0]?.color ?? DEFAULT_SECTOR_COLORS[0]
  const s2Color = trackIntel?.sectors[1]?.color ?? DEFAULT_SECTOR_COLORS[1]
  const s3Color = trackIntel?.sectors[2]?.color ?? DEFAULT_SECTOR_COLORS[2]

  // ── Fastest driver per sector ─────────────────────────────────────
  const s1Driver = sectorData?.summary?.fastestSector1Driver ?? null
  const s2Driver = sectorData?.summary?.fastestSector2Driver ?? null
  const s3Driver = sectorData?.summary?.fastestSector3Driver ?? null

  // ── Circuit name for header ───────────────────────────────────────
  const circuitName = getRaceCircuitName(round)

  // Only show "not available" when the query has actually completed with no data.
  // A disabled query (isVisible=false) has isLoading=false and data=undefined in
  // React Query v5 — without the isVisible guard, this falsely triggers the empty
  // state before the panel ever scrolls into view.
  const noSVG = isVisible && !svgLoading && !svgData

  return (
    <div ref={containerRef} className="card-panel content-defer">
      {/* Panel Header */}
      <div className="mb-3">
        <h2 className="card-panel-header !mb-0">
          Circuit Map
        </h2>
        {circuitName && (
          <p className="text-xs text-gray-400 mt-0.5">
            {circuitName}
          </p>
        )}
      </div>

      {/* Loading skeleton — shown while not yet visible or while fetching */}
      {(svgLoading || !isVisible) && !svgData && (
        <div className="animate-pulse">
          <div className="h-[300px] bg-f1gray/10 rounded-lg" />
        </div>
      )}

      {/* No SVG available — graceful empty state */}
      {noSVG && (
        <div className="flex items-center justify-center h-24 text-gray-500 text-sm">
          Track map not available for this circuit.
        </div>
      )}

      {/* ── SVG Track Map ──────────────────────────────────────────── */}
      {svgData && (
        <>
          <div className="flex justify-center">
            <svg
              viewBox={svgData.viewBox}
              className="w-full h-auto max-h-[400px]"
              role="img"
              aria-label={`Circuit map of ${circuitName ?? 'this circuit'} with sector highlighting`}
            >
              {/* Gray base layer — all 3 sector paths as thick gray outlines */}
              <path
                d={svgData.sector1PathD}
                fill="none"
                stroke="#374151"
                strokeWidth={6}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d={svgData.sector2PathD}
                fill="none"
                stroke="#374151"
                strokeWidth={6}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d={svgData.sector3PathD}
                fill="none"
                stroke="#374151"
                strokeWidth={6}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Coloured overlay — thinner, on top */}
              <path
                d={svgData.sector1PathD}
                fill="none"
                stroke={s1Color}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-label="Sector 1"
              />
              <path
                d={svgData.sector2PathD}
                fill="none"
                stroke={s2Color}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-label="Sector 2"
              />
              <path
                d={svgData.sector3PathD}
                fill="none"
                stroke={s3Color}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-label="Sector 3"
              />
            </svg>
          </div>

          {/* ── Sector Legend ─────────────────────────────────────── */}
          <div className="flex items-center justify-center gap-6 mt-3">
            <SectorLegendItem
              label="S1"
              color={s1Color}
              driver={s1Driver}
            />
            <SectorLegendItem
              label="S2"
              color={s2Color}
              driver={s2Driver}
            />
            <SectorLegendItem
              label="S3"
              color={s3Color}
              driver={s3Driver}
            />
          </div>
        </>
      )}

      {/* ── How to read this component guide ──────────────────────── */}
      {svgData && (
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
            How to read this component
          </button>
          {showGuide && (
            <div className="mt-2 p-3 rounded border border-white/10 bg-white/[0.02] text-sm text-gray-500 space-y-2">
              <div>
                <span className="text-gray-400 font-medium">What this component shows: </span>
                The circuit map displays the full track layout divided into three
                colour-coded sectors (S1, S2, S3). Each sector is a timed segment
                of the circuit — the timing system records how long each driver
                takes to traverse each sector independently.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Reading the track layout: </span>
                The thick gray outline shows the complete circuit shape. On top of
                this, thinner coloured lines highlight each sector. The track runs
                as a continuous loop: S1 leads into S2, S2 leads into S3, and S3
                connects back to S1 at the start/finish line. Tight, angular sections
                represent low-speed corners, while smooth sweeping curves indicate
                high-speed turns.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Sector colours: </span>
                Each sector is displayed in a distinct colour specific to this
                circuit. The colours match the sector data shown in the Sector
                Analysis table below, creating a visual link between the map and
                the numerical breakdown. The dual-layer design (thick gray base
                with a thinner coloured overlay) ensures sector boundaries remain
                clear even where two sectors meet.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Sector legend: </span>
                Below the map, the legend shows the sector label (S1, S2, S3),
                the matching colour, and the fastest driver in that sector from
                the current session. This tells you at a glance which driver
                dominated each part of the circuit.
              </div>
              <div>
                <span className="text-gray-400 font-medium">Cross-referencing with sector analysis: </span>
                Use this map alongside the Sector Analysis table below. When the
                table shows a driver losing time in a specific sector, the map
                reveals what that sector looks like physically — whether it
                contains the technical chicane, the high-speed sequence, or the
                long straight. This spatial context transforms abstract sector
                deltas into actionable insights about car setup and driving style.
              </div>
              <div>
                <span className="text-gray-400 font-medium">What to look for: </span>
                Check whether the same driver is fastest in all three sectors or
                whether different drivers dominate different sections. Multiple
                drivers holding sector-fastest times suggests a competitive session.
                A single driver fastest everywhere indicates clear dominance.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Sector Legend Item
// =============================================================================

interface SectorLegendItemProps {
  label: string
  color: string
  driver: string | null
}

function SectorLegendItem({ label, color, driver }: SectorLegendItemProps) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      <span
        className="h-2.5 w-2.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="text-gray-400 font-medium">{label}</span>
      {driver && (
        <>
          <span className="text-gray-600">—</span>
          <span className="text-gray-300 font-mono text-xs">{driver}</span>
        </>
      )}
    </div>
  )
}
