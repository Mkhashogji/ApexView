'use client'

import { useState, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

// Hooks
import { useSessionsQuery } from '@/lib/hooks/useSessionsQuery'
import { useTelemetryQuery } from '@/lib/hooks/useTelemetryQuery'
import { useSectorsQuery } from '@/lib/hooks/useSectorsQuery'
import { useTrackQuery } from '@/lib/hooks/useTrackQuery'
import { useLapsQuery } from '@/lib/hooks/useLapsQuery'
import { usePerformanceInsightsQuery } from '@/lib/hooks/usePerformanceInsightsQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'

// Components
import { QualifyingSidebar } from '@/components/qualifying/QualifyingSidebar'
import { TelemetryLine } from '@/components/charts/TelemetryLine'
import { DeltaPlot } from '@/components/charts/DeltaPlot'
import { SectorCards } from '@/components/panels/SectorCards'
import { ScalingMetadataPanel } from '@/components/panels/ScalingMetadataPanel'
import { CornerBreakdownPanel } from '@/components/panels/CornerBreakdownPanel'
import { PerformanceInsightsPanel } from '@/components/panels/PerformanceInsightsPanel'
import { ErrorBoundary } from '@/components/race/ErrorBoundary'

// Types
import { Telemetry, QualifyingSessionPart, DeltaData, InsightMode } from '@/../../packages/models/src/types'

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
 * - Data-driven insights (single unified call, visibility-gated)
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

  // Insight mode state (lifted from PerformanceInsightsPanel)
  const [insightMode, setInsightMode] = useState<InsightMode>('engineer')

  // Visibility gate — defers analysis query until user scrolls near the Delta panel
  const { containerRef: analysisPanelRef, isVisible: isAnalysisPanelVisible } = useVisibility()

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

  // Queries with loading/error/placeholder states destructured
  const {
    data: sessionsData,
    isLoading: isSessionsLoading,
    isError: isSessionsError,
    isPlaceholderData: isSessionsPlaceholder,
  } = useSessionsQuery(season, round)

  const {
    data: telemetryData,
    isLoading: isTelemetryLoading,
    isError: isTelemetryError,
    isPlaceholderData: isTelemetryPlaceholder,
    refetch: refetchTelemetry
  } = useTelemetryQuery(sessionId, selectedDrivers, qualifyingPart)

  const {
    data: sectorsData,
    isLoading: isSectorsLoading,
    isError: isSectorsError,
    isPlaceholderData: isSectorsPlaceholder,
    refetch: refetchSectors
  } = useSectorsQuery(sessionId, selectedDrivers, qualifyingPart)

  const {
    data: lapsData,
    isLoading: isLapsLoading,
    isPlaceholderData: isLapsPlaceholder,
  } = useLapsQuery(sessionId, selectedDrivers)

  const {
    data: trackData,
    isLoading: isTrackLoading,
    isPlaceholderData: isTrackPlaceholder,
  } = useTrackQuery(round, season)

  // Unified analysis query — replaces separate scaled-delta, corner-analysis, and performance-insights calls
  // Visibility-gated: only fires when user scrolls near the Delta panel
  const {
    data: performanceData,
    isLoading: isPerformanceLoading,
    isError: isPerformanceError,
    error: performanceError,
    isPlaceholderData: isPerformancePlaceholder,
  } = usePerformanceInsightsQuery({
    sessionId,
    referenceDriver,
    compareDrivers,
    corners: trackData?.corners,
    mode: insightMode,
    sessionPart: qualifyingPart,
    trackLength: trackData?.length,
    enabled: isAnalysisPanelVisible && !isTrackPlaceholder,
  })

  // Aggregate placeholder state for transition visual indicator
  const isAnyPlaceholder = isTelemetryPlaceholder || isSectorsPlaceholder || isTrackPlaceholder || isPerformancePlaceholder

  // Derived data - safe access with guards
  const isSprintWeekend = sessionsData?.some(s => s?.isSprintWeekend) ?? false

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

  // Transform performanceData results to DeltaData format for DeltaPlot
  // Sources delta from the unified analysis endpoint (Phase 2 data embedded in results)
  const transformedDeltaData = useMemo((): DeltaData[] => {
    if (!performanceData?.results) return []

    return performanceData.results.map(result => ({
      referenceDriver,
      compareDriver: result.driver,
      distance: result.distance ?? [],
      delta: result.delta ?? [],
    }))
  }, [performanceData, referenceDriver])

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

  return (
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

      {/* Main Content Area — progressive loading per section */}
      <main className="flex-1 min-w-0 space-y-6">
        {selectedDrivers.length > 0 ? (
          <>
            {/* Telemetry Trace + Sector Breakdown Row */}
            <div className="flex flex-col xl:flex-row gap-6">
              {/* Telemetry Chart — loads when telemetry + track data ready */}
              <ErrorBoundary key={`telemetry-${sessionId}`} panelName="Telemetry Trace">
                <div className="flex-1 card-panel min-w-0">
                  <h2 className="card-panel-header">Telemetry Trace</h2>
                  {(isTelemetryLoading || isTrackLoading) && !telemetryData ? (
                    <div className="h-96 skeleton rounded-lg" />
                  ) : isTelemetryError ? (
                    <div className="h-96 flex items-center justify-center text-red-400 text-sm">
                      Failed to load telemetry.{' '}
                      <button onClick={() => refetchTelemetry()} className="underline ml-1">Retry</button>
                    </div>
                  ) : telemetryData && trackData ? (
                    <div className={`transition-opacity duration-300 ${isTelemetryPlaceholder || isTrackPlaceholder ? 'opacity-50' : ''}`}>
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
                  ) : (
                    <div className="h-96 flex items-center justify-center text-gray-500 text-sm">
                      Waiting for data...
                    </div>
                  )}
                </div>
              </ErrorBoundary>

              {/* Sector Breakdown — loads when sectors data ready */}
              <ErrorBoundary key={`sectors-${sessionId}`} panelName="Sector Breakdown">
                <div className="xl:w-80 xl:flex-shrink-0 card-panel">
                  <h2 className="card-panel-header">Sector Breakdown</h2>
                  {isSectorsLoading && !sectorsData ? (
                    <div className="space-y-3">
                      {[1, 2, 3, 4].map(i => (
                        <div key={i} className="h-8 skeleton rounded" />
                      ))}
                    </div>
                  ) : isSectorsError ? (
                    <div className="text-red-400 text-sm py-4">
                      Failed to load sectors.{' '}
                      <button onClick={() => refetchSectors()} className="underline ml-1">Retry</button>
                    </div>
                  ) : (
                    <div className={`transition-opacity duration-300 ${isSectorsPlaceholder ? 'opacity-50' : ''}`}>
                      <SectorCards
                        sectorData={sectorsData ?? []}
                        referenceDriver={referenceDriver}
                      />
                    </div>
                  )}
                </div>
              </ErrorBoundary>
            </div>

            {/* Delta to Reference */}
            <ErrorBoundary key={`delta-${sessionId}`} panelName="Delta to Reference">
              <div className="card-panel">
                <h2 className="card-panel-header">
                  Delta to Reference ({referenceDriver})
                </h2>
                {(isPerformanceLoading || isTrackLoading) && !performanceData ? (
                  <div className="h-96 skeleton rounded-lg" />
                ) : isPerformanceError ? (
                  <div className="h-96 flex items-center justify-center text-red-400 text-sm">
                    Failed to load delta data: {(performanceError as Error)?.message}
                  </div>
                ) : (
                  <div className={`transition-opacity duration-300 ${isPerformancePlaceholder || isTrackPlaceholder ? 'opacity-50' : ''}`}>
                    <DeltaPlot
                      deltaData={transformedDeltaData}
                      referenceDriver={referenceDriver}
                      sectors={trackData?.sectors ?? []}
                      trackLength={trackData?.length ?? undefined}
                      onRangeChange={handleChartRangeChange}
                      xRange={chartXRange}
                    />
                  </div>
                )}
              </div>
            </ErrorBoundary>

            {/* Phase 2: Scaled Delta Analysis Metadata — visibility trigger for analysis query */}
            <ErrorBoundary key={`scaling-${sessionId}`} panelName="Scaled Delta Analysis">
              <div ref={analysisPanelRef} className="content-defer">
                <ScalingMetadataPanel
                  results={performanceData?.results ?? []}
                  referenceDriver={referenceDriver}
                  isLoading={isPerformanceLoading}
                  error={isPerformanceError ? (performanceError as Error)?.message : undefined}
                />
              </div>
            </ErrorBoundary>

            {/* Phase 3: Corner Analysis Breakdown — fed from unified analysis response */}
            <ErrorBoundary key={`corners-${sessionId}`} panelName="Corner Analysis">
              <div className="content-defer">
                <CornerBreakdownPanel
                  results={performanceData?.results ?? []}
                  referenceDriver={referenceDriver}
                  isLoading={isPerformanceLoading}
                  error={isPerformanceError ? (performanceError as Error)?.message : undefined}
                />
              </div>
            </ErrorBoundary>

            {/* Performance Insights — Phase 7, fed from unified analysis response */}
            <ErrorBoundary key={`insights-${sessionId}`} panelName="Performance Insights">
              <div className="content-defer">
                <PerformanceInsightsPanel
                  data={performanceData}
                  referenceDriver={referenceDriver}
                  compareDrivers={compareDrivers}
                  isLoading={isPerformanceLoading}
                  isError={isPerformanceError}
                  error={performanceError}
                  mode={insightMode}
                  onModeChange={setInsightMode}
                />
              </div>
            </ErrorBoundary>
          </>
        ) : (
          <div className="card-panel text-center py-12">
            <p className="text-gray-400">Select drivers from the sidebar to begin analysis</p>
          </div>
        )}
      </main>
    </div>
  )
}
