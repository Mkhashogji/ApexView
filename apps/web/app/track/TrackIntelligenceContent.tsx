'use client'

import { useTrackIntelligence } from '@/lib/hooks'
import {
  CircuitOverview,
  CharacteristicsBars,
  SectorBreakdown,
  TechnicalInsights,
  BenchmarkTimes,
  StrategicNotes,
  DefiningTags,
} from '@/components/track'

interface TrackIntelligenceContentProps {
  round: number
  season?: number
}

export function TrackIntelligenceContent({ round, season = 2025 }: TrackIntelligenceContentProps) {
  const { editorial, apiData, isLoading, isError, hasEditorial } = useTrackIntelligence(round, season)

  // Loading state
  if (isLoading) {
    return <TrackIntelligenceSkeleton />
  }

  // Error state
  if (isError) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-8 text-center">
        <h2 className="text-xl font-semibold text-red-400">Error Loading Track Data</h2>
        <p className="mt-2 text-gray-400">
          Unable to load track information for Round {round}. Please try again later.
        </p>
      </div>
    )
  }

  // No editorial data - show basic fallback with API data
  if (!hasEditorial || !editorial) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">
              {apiData?.circuitName || `Round ${round} Circuit`}
            </h1>
            <p className="mt-1 text-gray-400">Track Intelligence</p>
          </div>
          <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
            Coming Soon
          </span>
        </div>

        <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-8">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-white">Detailed Track Intelligence</h2>
            <p className="mt-2 text-gray-400">
              Comprehensive track analysis for this circuit is coming soon.
            </p>
            <p className="mt-4 text-sm text-gray-500">
              In the meantime, basic track data is available via the API.
            </p>
          </div>

          {/* Show basic API data if available */}
          {apiData && (
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4 text-center">
                <p className="text-xs text-gray-500">Track Length</p>
                <p className="text-2xl font-bold text-white">
                  {(apiData.length / 1000).toFixed(3)} km
                </p>
              </div>
              <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4 text-center">
                <p className="text-xs text-gray-500">Corners</p>
                <p className="text-2xl font-bold text-white">
                  {apiData.corners?.length || 'N/A'}
                </p>
              </div>
              <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4 text-center">
                <p className="text-xs text-gray-500">DRS Zones</p>
                <p className="text-2xl font-bold text-white">
                  {apiData.drsZones?.length || 'N/A'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Full Track Intelligence page with editorial content
  return (
    <div className="space-y-6">
      {/* Defining Characteristics Tags - at the top for quick context */}
      <DefiningTags characteristics={editorial.definingCharacteristics} />

      {/* Circuit Overview */}
      <CircuitOverview
        overview={editorial.circuitOverview}
        stats={editorial.circuitStats}
      />

      {/* Two-column layout for characteristics and sectors */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CharacteristicsBars
          characteristics={editorial.circuitCharacteristics}
          energyProfile={editorial.energyProfile}
        />
        <SectorBreakdown sectors={editorial.sectors} />
      </div>

      {/* Technical Insights - full width */}
      <TechnicalInsights
        technicalInsights={editorial.technicalInsights}
        overtakingAnalysis={editorial.overtakingAnalysis}
        drsZones={editorial.drsZones}
      />

      {/* Strategic Analysis and Benchmarks */}
      <div className="grid gap-6 lg:grid-cols-2">
        <StrategicNotes
          strategicInsights={editorial.strategicInsights}
          weatherProfile={editorial.weatherProfile}
        />
        <div /> {/* Spacer for grid alignment */}
      </div>

      {/* Benchmark Times - full width */}
      <BenchmarkTimes benchmarks={editorial.benchmarkLapTimes} />
    </div>
  )
}

// Loading skeleton component
function TrackIntelligenceSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      {/* Tags skeleton */}
      <div className="flex gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-10 w-32 rounded-full bg-f1gray/30" />
        ))}
      </div>

      {/* Header skeleton */}
      <div className="space-y-4">
        <div className="h-10 w-2/3 rounded bg-f1gray/30" />
        <div className="h-6 w-1/3 rounded bg-f1gray/30" />
        <div className="h-24 w-full rounded-lg bg-f1gray/30" />
      </div>

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-20 rounded-lg bg-f1gray/30" />
        ))}
      </div>

      {/* Two-column skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-64 rounded-lg bg-f1gray/30" />
        <div className="h-64 rounded-lg bg-f1gray/30" />
      </div>

      {/* Full-width skeleton */}
      <div className="h-96 rounded-lg bg-f1gray/30" />
    </div>
  )
}
