'use client'

import { useState, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

// Hooks
import {
  useSessionsQuery,
  useTelemetryQuery,
  useDeltaQuery,
  useSectorsQuery,
  useTrackQuery,
  useLapsQuery,
  useScaledDeltaQuery,
  useCornerAnalysisQuery,
} from '@/lib/hooks'

// Components
import { QualifyingSidebar } from '@/components/qualifying/QualifyingSidebar'
import { TelemetryLine } from '@/components/charts/TelemetryLine'
import { DeltaPlot } from '@/components/charts/DeltaPlot'
import { SectorCards } from '@/components/panels/SectorCards'
import { ScalingMetadataPanel } from '@/components/panels/ScalingMetadataPanel'
import { CornerBreakdownPanel } from '@/components/panels/CornerBreakdownPanel'
import { PerformanceInsightsPanel } from '@/components/panels/PerformanceInsightsPanel'

// Types
import { Telemetry, QualifyingSessionPart } from '@/../../packages/models/src/types'

// Data
import raceCalendarData from '@/data/race-calendar-2025.json'

// Race calendar lookup
const RACE_CALENDAR = raceCalendarData.races

// Default values
const DEFAULT_DRIVERS = ['VER', 'NOR', 'PIA']
const DEFAULT_SESSION = 'Q3' as QualifyingSessionPart
const DEFAULT_SEASON = 2025
const DEFAULT_ROUND = 24 // Abu Dhabi

/**
 * Qualifying Analysis Page Content
 * 
 * This client component contains all the logic for the qualifying page.
 * It must be wrapped in a Suspense boundary because it uses useSearchParams().
 * 
 * Provides comprehensive qualifying session analysis with:
 * - Multi-driver telemetry comparison
 * - Delta analysis vs reference driver
 * - Sector breakdown with theoretical best
 * - ML-powered insights
 */
export function QualifyingContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Parse URL state - these are derived directly from URL and update when URL changes
  const season = parseInt(searchParams.get('season') || String(DEFAULT_SEASON))
  const round = parseInt(searchParams.get('round') || String(DEFAULT_ROUND))
  
  // These can be state since they're user-controlled within the page
  const initialDrivers = searchParams.get('drivers')?.split(',').filter(Boolean) || DEFAULT_DRIVERS
  const initialSession = (searchParams.get('session') as QualifyingSessionPart) || DEFAULT_SESSION
  const initialRef = searchParams.get('ref') || initialDrivers[0] || 'VER'

  // Local state for user selections
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(initialDrivers)
  const [referenceDriver, setReferenceDriver] = useState<string>(initialRef)
  const [sessionPart, setSessionPart] = useState<QualifyingSessionPart>(initialSession)
  
  // Chart sync state for zoom/pan
  const [chartXRange, setChartXRange] = useState<[number, number] | null>(null)

  // Construct session ID - base session without the Q1/Q2/Q3 part
  // The session part filtering is handled via the session_part API parameter
  const sessionId = useMemo(() => {
    // For sprint weekends, use SQ format
    const sessionPrefix = sessionPart.startsWith('S') ? 'Sprint_Qualifying' : 'Qualifying'
    return `${season}_${round}_${sessionPrefix}`
  }, [season, round, sessionPart])

  // Extract the qualifying part (Q1, Q2, Q3, SQ1, SQ2, SQ3) for API filtering
  const qualifyingPart = useMemo(() => {
    // Map session part to API filter value
    // SQ1/SQ2/SQ3 -> Q1/Q2/Q3 (FastF1 uses Q1/Q2/Q3 columns even for sprint qualifying)
    if (sessionPart.startsWith('S')) {
      return sessionPart.slice(1) // SQ1 -> Q1
    }
    return sessionPart // Q1, Q2, Q3
  }, [sessionPart])

  // Delta query helper - compare all non-reference drivers to reference
  const compareDrivers = useMemo(() => 
    selectedDrivers.filter(d => d !== referenceDriver),
    [selectedDrivers, referenceDriver]
  )

  // Queries with loading/error states destructured
  const { 
    data: sessionsData, 
    isLoading: isSessionsLoading,
    isError: isSessionsError 
  } = useSessionsQuery(season, round)

  const { 
    data: telemetryData, 
    isLoading: isTelemetryLoading,
    isError: isTelemetryError,
    refetch: refetchTelemetry 
  } = useTelemetryQuery(sessionId, selectedDrivers, qualifyingPart)

  const { 
    data: sectorsData, 
    isLoading: isSectorsLoading,
    isError: isSectorsError,
    refetch: refetchSectors 
  } = useSectorsQuery(sessionId, selectedDrivers, qualifyingPart)

  const { 
    data: lapsData, 
    isLoading: isLapsLoading 
  } = useLapsQuery(sessionId, selectedDrivers)

  const { 
    data: trackData, 
    isLoading: isTrackLoading 
  } = useTrackQuery(round, season)

  const {
    data: deltaData,
    isLoading: isDeltaLoading
  } = useDeltaQuery(sessionId, referenceDriver, compareDrivers, qualifyingPart)

  // Phase 2: Scaled Delta Query
  const {
    data: scaledDeltaData,
    isLoading: isScaledDeltaLoading,
    isError: isScaledDeltaError,
    error: scaledDeltaError,
  } = useScaledDeltaQuery(sessionId, referenceDriver, compareDrivers, qualifyingPart)

  // Phase 3: Corner Analysis Query
  const {
    data: cornerAnalysisData,
    isLoading: isCornerAnalysisLoading,
    isError: isCornerAnalysisError,
    error: cornerAnalysisError,
  } = useCornerAnalysisQuery(sessionId, referenceDriver, compareDrivers, trackData?.corners, qualifyingPart)

  // Combined loading state - wait for ALL data (including laps for completeness)
  const isLoading = 
    isSessionsLoading || 
    isTelemetryLoading || 
    isSectorsLoading || 
    isDeltaLoading || 
    isTrackLoading ||
    isLapsLoading

  // Combined error state
  const hasError = 
    isTelemetryError || 
    isSectorsError || 
    isSessionsError

  // Derived data - safe access with guards
  const isSprintWeekend = sessionsData?.some(s => s?.isSprintWeekend) ?? false
  const currentSession = sessionsData?.find(s => 
    s?.sessionType === 'Qualifying' || s?.sessionType === 'Sprint Qualifying'
  )

  // Convert telemetry array to Map for TelemetryLine
  const telemetryMap = useMemo(() => {
    const map = new Map<string, Telemetry>()
    if (telemetryData && Array.isArray(telemetryData)) {
      telemetryData.forEach(t => {
        if (t && t.driver) {
          map.set(t.driver, t)
        }
      })
    }
    return map
  }, [telemetryData])

  // Update URL when state changes
  const updateURL = useCallback((
    drivers: string[],
    session: QualifyingSessionPart,
    ref: string
  ) => {
    const params = new URLSearchParams()
    params.set('season', String(season))
    params.set('round', String(round))
    params.set('drivers', drivers.join(','))
    params.set('session', session)
    params.set('ref', ref)
    router.replace(`/qualifying?${params.toString()}`, { scroll: false })
  }, [season, round, router])

  // Handlers
  const handleDriversChange = useCallback((drivers: string[]) => {
    setSelectedDrivers(drivers)
    // Update reference driver if it's no longer selected
    if (drivers.length > 0 && !drivers.includes(referenceDriver)) {
      setReferenceDriver(drivers[0])
      updateURL(drivers, sessionPart, drivers[0])
    } else {
      updateURL(drivers, sessionPart, referenceDriver)
    }
  }, [referenceDriver, sessionPart, updateURL])

  const handleReferenceChange = useCallback((ref: string) => {
    setReferenceDriver(ref)
    updateURL(selectedDrivers, sessionPart, ref)
  }, [selectedDrivers, sessionPart, updateURL])

  const handleSessionChange = useCallback((session: QualifyingSessionPart) => {
    setSessionPart(session)
    updateURL(selectedDrivers, session, referenceDriver)
  }, [selectedDrivers, referenceDriver, updateURL])

  const handleChartRangeChange = useCallback((range: [number, number] | null) => {
    setChartXRange(range)
  }, [])

  // GUARD: Show loading skeleton while data is being fetched
  if (isLoading) {
    // DEBUG: Remove after confirming fix works
    console.log('[QualifyingPage] Loading state - waiting for data...')
    return (
      <div className="space-y-6">
        {/* Header skeleton */}
        <header className="border-l-4 border-f1red pl-4">
          <div className="h-10 w-72 bg-f1gray/30 rounded animate-pulse" />
          <div className="mt-2 h-5 w-48 bg-f1gray/20 rounded animate-pulse" />
        </header>
        
        {/* Filters skeleton */}
        <div className="card-panel space-y-4">
          <div className="flex gap-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-10 w-16 bg-f1gray/30 rounded animate-pulse" />
            ))}
          </div>
          <div className="h-12 w-full bg-f1gray/20 rounded animate-pulse" />
        </div>
        
        {/* Charts skeleton - 2x2 grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card-panel h-96 skeleton" />
          ))}
        </div>
      </div>
    )
  }

  // GUARD: Show error state if any critical query failed
  if (hasError) {
    // DEBUG: Remove after confirming fix works
    console.log('[QualifyingPage] Error state - query failed')
    return (
      <div className="space-y-6">
        <header className="border-l-4 border-f1red pl-4">
          <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
            Qualifying Analysis
          </h1>
        </header>
        
        <div className="card-panel border-red-500/50 bg-red-500/10 text-center py-12">
          <h3 className="text-lg font-semibold text-red-400 mb-2">
            Failed to Load Data
          </h3>
          <p className="text-gray-400 mb-4">
            Could not fetch qualifying data. Please try again.
          </p>
          <button
            onClick={() => {
              refetchTelemetry()
              refetchSectors()
            }}
            className="rounded-md bg-f1red px-6 py-2 text-sm font-medium hover:bg-f1red/80 focus-ring"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // GUARD: Verify critical data exists (defensive programming)
  if (!telemetryData || !sectorsData || !trackData) {
    // DEBUG: Remove after confirming fix works
    console.log('[QualifyingPage] Data existence check - waiting for data...', {
      hasTelemetry: !!telemetryData,
      telemetryLength: telemetryData?.length ?? 'N/A',
      hasSectors: !!sectorsData,
      sectorsLength: sectorsData?.length ?? 'N/A',
      hasTrack: !!trackData,
      trackLength: trackData?.length ?? 'N/A',
      trackDrsZones: trackData?.drsZones?.length ?? 'N/A',
    })
    return (
      <div className="space-y-6">
        <header className="border-l-4 border-f1red pl-4">
          <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
            Qualifying Analysis
          </h1>
        </header>
        
        <div className="card-panel text-center py-12">
          <p className="text-gray-400">Waiting for data...</p>
        </div>
      </div>
    )
  }

  // DEBUG: Remove after confirming fix works
  console.log('[QualifyingPage] Rendering with data - all guards passed', {
    telemetryMapSize: telemetryMap.size,
    sectorsDataLength: sectorsData?.length ?? 0,
    deltaDataLength: deltaData?.length ?? 0,
    trackDataExists: !!trackData,
    trackLength: trackData?.length ?? 'undefined',
    trackDrsZones: trackData?.drsZones?.length ?? 0,
    trackCorners: trackData?.corners?.length ?? 0,
    trackSectors: trackData?.sectors?.length ?? 0,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="border-l-4 border-f1red pl-4">
        <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
          Qualifying Analysis
        </h1>
        <p className="mt-2 text-gray-400">
          {RACE_CALENDAR.find(r => r.round === round)?.name || currentSession?.circuitName || 'Grand Prix'} 
          {' · '}{season} Season · Round {round}
        </p>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Sidebar */}
        <QualifyingSidebar
          sessionPart={sessionPart}
          onSessionChange={handleSessionChange}
          isSprintWeekend={isSprintWeekend}
          referenceDriver={referenceDriver}
          onReferenceChange={handleReferenceChange}
          selectedDrivers={selectedDrivers}
          onDriversChange={handleDriversChange}
          maxDrivers={6}
        />

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 space-y-6">
          {selectedDrivers.length > 0 ? (
            <>
              {/* Telemetry Trace + Sector Breakdown Row */}
              <div className="flex flex-col xl:flex-row gap-6">
                {/* Telemetry Chart - Takes most width */}
                <div className="flex-1 card-panel min-w-0">
                  <h2 className="card-panel-header">Telemetry Trace</h2>
                  <TelemetryLine
                    telemetryData={telemetryMap}
                    selectedDrivers={selectedDrivers}
                    drsZones={trackData?.drsZones ?? []}
                    corners={trackData?.corners ?? []}
                    trackLength={trackData?.length ?? undefined}
                    onRangeChange={handleChartRangeChange}
                    xRange={chartXRange}
                  />
                </div>

                {/* Sector Breakdown - Fixed width on larger screens */}
                <div className="xl:w-80 xl:flex-shrink-0 card-panel">
                  <h2 className="card-panel-header">Sector Breakdown</h2>
                  <SectorCards
                    sectorData={sectorsData ?? []}
                    referenceDriver={referenceDriver}
                  />
                </div>
              </div>

              {/* Delta to Reference - Full Width */}
              <div className="card-panel">
                <h2 className="card-panel-header">Delta to Reference ({referenceDriver})</h2>
                <DeltaPlot
                  deltaData={deltaData ?? []}
                  referenceDriver={referenceDriver}
                  sectors={trackData?.sectors ?? []}
                  trackLength={trackData?.length ?? undefined}
                  onRangeChange={handleChartRangeChange}
                  xRange={chartXRange}
                />
              </div>

              {/* Phase 2: Scaled Delta Analysis Metadata */}
              <ScalingMetadataPanel
                results={scaledDeltaData?.results ?? []}
                referenceDriver={referenceDriver}
                isLoading={isScaledDeltaLoading}
                error={isScaledDeltaError ? (scaledDeltaError as Error)?.message : undefined}
              />

              {/* Phase 3: Corner Analysis Breakdown */}
              <CornerBreakdownPanel
                results={cornerAnalysisData?.results ?? []}
                referenceDriver={referenceDriver}
                isLoading={isCornerAnalysisLoading}
                error={isCornerAnalysisError ? (cornerAnalysisError as Error)?.message : undefined}
              />

              {/* Performance Insights - Phase 7 (replaces AIInsights) */}
              <PerformanceInsightsPanel
                sessionId={sessionId}
                referenceDriver={referenceDriver}
                selectedDrivers={selectedDrivers}
                corners={trackData?.corners ?? []}
                sessionPart={qualifyingPart}
              />
            </>
          ) : (
            /* Empty State */
            <div className="card-panel text-center py-12">
              <p className="text-gray-400">Select drivers from the sidebar to begin analysis</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
