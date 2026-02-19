'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useRacePaceQuery } from '@/lib/hooks/useRacePaceQuery'
import { getRaceFuelEffect } from '@/data/tracks/race-lookup'
import { RaceSidebar } from '@/components/race/RaceSidebar'
import { RacePaceBoxPlot } from '@/components/race/RacePaceBoxPlot'
import { ErrorBoundary } from '@/components/race/ErrorBoundary'
import TyreDegradationPanel from '@/components/race/TyreDegradationPanel'
import PitStopPanel from '@/components/race/PitStopPanel'
import TeamPerformancePanel from '@/components/race/TeamPerformancePanel'

const DEFAULT_SEASON = 2025
const DEFAULT_ROUND = 24

/**
 * Race Analysis Page Content — Client Component
 *
 * Orchestrates data fetching, state management, and panel rendering
 * for the Race page. Must be wrapped in Suspense because it uses
 * useSearchParams().
 */
export default function RaceContent() {
  const searchParams = useSearchParams()

  // Parse URL state
  const season = parseInt(searchParams.get('season') || String(DEFAULT_SEASON))
  const round = parseInt(searchParams.get('round') || String(DEFAULT_ROUND))

  // Local state
  const [fuelCorrected, setFuelCorrected] = useState(true)

  // Derive session ID for race
  const sessionId = `${season}_${round}_Race`

  // Get circuit-specific fuel effect from lightweight lookup (no full Track Intelligence import)
  const fuelEffectPerKg = getRaceFuelEffect(round)

  // Determine fuel effect to pass to API:
  // When fuel-corrected, use circuit-specific factor
  // When raw, pass 0 (fuel_corrected_time == lap_time when factor is 0)
  const fuelEffect = fuelCorrected ? fuelEffectPerKg : 0

  // Data fetching
  const {
    data: racePaceData,
    isLoading,
    isError,
    error,
    isPlaceholderData,
  } = useRacePaceQuery(sessionId, fuelEffect)

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      <RaceSidebar
        fuelCorrected={fuelCorrected}
        onFuelCorrectedChange={setFuelCorrected}
      />

      <main className="flex-1 min-w-0 space-y-6">
        {/* Race Pace Distribution — above fold, inline loading/error handling */}
        <section
          className={`card-panel transition-opacity duration-300 ${
            isPlaceholderData ? 'opacity-50' : 'opacity-100'
          }`}
        >
          <ErrorBoundary key={`pace-${sessionId}`} panelName="Race Pace Distribution">
            {isLoading && !racePaceData ? (
              <>
                <h2 className="card-panel-header">Race Pace Distribution</h2>
                <div className="h-[450px] skeleton rounded-lg" />
              </>
            ) : isError ? (
              <>
                <h2 className="card-panel-header">Race Pace Distribution</h2>
                <div className="h-[450px] flex items-center justify-center text-red-400 text-sm">
                  <div className="text-center">
                    <p>Failed to load race pace data</p>
                    <p className="text-gray-500 mt-1">
                      {error instanceof Error ? error.message : 'Unknown error'}
                    </p>
                  </div>
                </div>
              </>
            ) : racePaceData ? (
              <RacePaceBoxPlot
                data={racePaceData}
                fuelCorrected={fuelCorrected}
              />
            ) : (
              <>
                <h2 className="card-panel-header">Race Pace Distribution</h2>
                <div className="h-[450px] flex items-center justify-center text-gray-500">
                  Select a Grand Prix to view race pace analysis
                </div>
              </>
            )}
          </ErrorBoundary>
        </section>

        {/* Below-fold panels — each has its own ref + content-defer internally */}
        <ErrorBoundary key={`tyre-${sessionId}`} panelName="Tyre Degradation Analysis">
          <TyreDegradationPanel sessionId={sessionId} fuelEffect={fuelEffect} />
        </ErrorBoundary>

        <ErrorBoundary key={`pit-${sessionId}`} panelName="Pit Stop Analysis">
          <PitStopPanel sessionId={sessionId} />
        </ErrorBoundary>

        <ErrorBoundary key={`team-${sessionId}`} panelName="Team Performance">
          <TeamPerformancePanel sessionId={sessionId} fuelEffect={fuelEffect} />
        </ErrorBoundary>
      </main>
    </div>
  )
}
