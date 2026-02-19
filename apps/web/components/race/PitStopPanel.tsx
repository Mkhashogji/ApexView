'use client'

import { useState } from 'react'
import { usePitStopsQuery } from '@/lib/hooks/usePitStopsQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'
import PitStopViewTabs, { type PitStopView } from './PitStopViewTabs'
import PitStopByTeam from './PitStopByTeam'
import PitStopByDriver from './PitStopByDriver'
import PitStopGapToFastest from './PitStopGapToFastest'
import PitStopInsights from './PitStopInsights'
import PitStopAnomalyNote from './PitStopAnomalyNote'

interface PitStopPanelProps {
  sessionId: string | undefined
}

/**
 * Phase 4: Pit Stop Analysis panel orchestrator.
 *
 * Manages the view state (By Team / By Driver / Gap to Fastest),
 * delegates rendering to sub-components, and handles loading/error states.
 * All three chart views use the same API response — switching views
 * is instant with no additional data fetching.
 *
 * Deferred loading: useVisibility + IntersectionObserver delays data fetching
 * until the panel approaches the viewport (200px threshold).
 */
export default function PitStopPanel({ sessionId }: PitStopPanelProps) {
  const { containerRef, isVisible } = useVisibility()
  const [activeView, setActiveView] = useState<PitStopView>('byTeam')
  const [showGuide, setShowGuide] = useState(false)
  const { data, isLoading, isError, error, isPlaceholderData } =
    usePitStopsQuery(sessionId, isVisible)

  const showSkeleton = !isVisible || (isLoading && !data)
  const showError = !showSkeleton && (isError || !data)
  const showEmpty = !showSkeleton && !showError && data && data.teamAggregates.length === 0
  const showContent = !showSkeleton && !showError && !showEmpty && data

  return (
    <div ref={containerRef} className="content-defer">
      {showSkeleton && <PitStopSkeleton />}

      {showError && (
        <section className="card-panel">
          <h2 className="card-panel-header">Pit Stop Analysis</h2>
          <div className="h-[300px] flex items-center justify-center text-red-400 text-sm">
            <div className="text-center">
              <p>Failed to load pit stop data</p>
              <p className="text-gray-500 mt-1">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          </div>
        </section>
      )}

      {showEmpty && (
        <section className="card-panel">
          <h2 className="card-panel-header">Pit Stop Analysis</h2>
          <div className="h-[200px] flex items-center justify-center text-gray-500 text-sm">
            No pit stop data available for this session.
          </div>
        </section>
      )}

      {showContent && (
        <section
          className={`card-panel transition-opacity duration-300 ${
            isPlaceholderData ? 'opacity-50' : 'opacity-100'
          }`}
        >
          <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
            <h2 className="card-panel-header mb-0">Pit Stop Analysis</h2>
            <PitStopViewTabs activeView={activeView} onViewChange={setActiveView} />
          </div>

          {/* Chart area — switches view without API round-trip */}
          <div className="min-h-[200px]">
            {activeView === 'byTeam' && (
              <PitStopByTeam teamAggregates={data.teamAggregates} />
            )}
            {activeView === 'byDriver' && (
              <PitStopByDriver driverAggregates={data.driverAggregates} />
            )}
            {activeView === 'gapToFastest' && (
              <PitStopGapToFastest
                gapData={data.gapToFastest}
                fastestTeam={data.fastestTeam}
              />
            )}
          </div>

          {/* Anomaly note — only renders when anomalies exist */}
          {data.anomalyNotes.length > 0 && (
            <PitStopAnomalyNote anomalies={data.anomalyNotes} />
          )}

          {/* Insight cards */}
          <div className="mt-5">
            <PitStopInsights insights={data.insights} />
          </div>

          {/* Expandable explanation guide */}
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
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  What is pit lane time?
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    During a race, cars must stop to change tyres. The{' '}
                    <span className="text-gray-400 font-medium">pit lane time</span>{' '}
                    is the total time a car spends in the pit lane &mdash; from entry
                    to exit. It includes the drive in, the stationary stop where the
                    crew changes the tyres, and the drive out. Lower times are better.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Three chart views
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">By Team</span>{' '}
                    &mdash; Shows the average pit lane time for each team, combining
                    all their drivers&apos; stops. This highlights which pit crew was
                    fastest overall.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">By Driver</span>{' '}
                    &mdash; Breaks down the average per driver so you can spot
                    differences between teammates and across the full grid.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Gap to Fastest</span>{' '}
                    &mdash; Shows how much time each team lost compared to the fastest
                    team. A gap of +0.5s means that team&apos;s average stop was half
                    a second slower.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Insight cards
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Quickest on Average</span>{' '}
                    &mdash; The team with the lowest average pit lane time across all
                    their non-anomalous stops.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Most Consistent</span>{' '}
                    &mdash; The team whose stop times varied the least. For teams with
                    three or more stops, consistency is measured using the Interquartile
                    Range (IQR), which captures how tightly the middle 50% of stop
                    times cluster together. For teams with exactly two stops, it is
                    the simple difference between those two times. A lower value means
                    more repeatable performance.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Anomalous stops
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    Unusually long stops &mdash; caused by incidents, penalties, or
                    mechanical issues &mdash; are automatically detected and excluded
                    from averages and consistency calculations. When present, they are
                    listed below the chart so you can see what happened without those
                    outliers distorting the results.
                  </p>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}

function PitStopSkeleton() {
  return (
    <section className="card-panel">
      <div className="h-6 w-48 skeleton rounded mb-4" />
      <div className="h-[300px] skeleton rounded-lg" />
      <div className="grid grid-cols-2 gap-4 mt-5">
        <div className="h-24 skeleton rounded" />
        <div className="h-24 skeleton rounded" />
      </div>
    </section>
  )
}
