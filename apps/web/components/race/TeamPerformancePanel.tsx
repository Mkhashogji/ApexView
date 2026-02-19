'use client'

import { useState } from 'react'
import { useTeamPerformanceQuery } from '@/lib/hooks/useTeamPerformanceQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'
import TeamPerfViewTabs, { type TeamPerfView } from './TeamPerfViewTabs'
import TopSpeedDivergence from './TopSpeedDivergence'
import MeanSpeedDivergence from './MeanSpeedDivergence'
import TeamQuadrantScatter from './TeamQuadrantScatter'
import TeamPerfInsights from './TeamPerfInsights'

interface TeamPerformancePanelProps {
  sessionId: string | undefined
  fuelEffect?: number
}

/**
 * Phase 5: Team Performance Quadrant panel orchestrator.
 *
 * Manages the view state (Top Speed / Mean Speed / Quadrant),
 * delegates rendering to sub-components, and handles loading/error states.
 * All three chart views use the same API response — switching views
 * is instant with no additional data fetching.
 *
 * Deferred loading: useVisibility + IntersectionObserver delays data fetching
 * until the panel approaches the viewport (200px threshold).
 */
export default function TeamPerformancePanel({
  sessionId,
  fuelEffect,
}: TeamPerformancePanelProps) {
  const { containerRef, isVisible } = useVisibility()
  const [activeView, setActiveView] = useState<TeamPerfView>('quadrant')
  const [showGuide, setShowGuide] = useState(false)
  const { data, isLoading, isError, error, isPlaceholderData } =
    useTeamPerformanceQuery(sessionId, fuelEffect, isVisible)

  const showSkeleton = !isVisible || (isLoading && !data)
  const showError = !showSkeleton && (isError || !data)
  const showEmpty = !showSkeleton && !showError && data && data.teams.length === 0
  const showContent = !showSkeleton && !showError && !showEmpty && data

  return (
    <div ref={containerRef} className="content-defer">
      {showSkeleton && <TeamPerformanceSkeleton />}

      {showError && (
        <section className="card-panel">
          <h2 className="card-panel-header">Team Performance</h2>
          <div className="h-[300px] flex items-center justify-center text-red-400 text-sm">
            <div className="text-center">
              <p>Failed to load team performance data</p>
              <p className="text-gray-500 mt-1">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          </div>
        </section>
      )}

      {showEmpty && (
        <section className="card-panel">
          <h2 className="card-panel-header">Team Performance</h2>
          <div className="h-[200px] flex items-center justify-center text-gray-500 text-sm">
            No speed data available for this session. Try clearing the cache and reloading.
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
            <h2 className="card-panel-header mb-0">Team Performance</h2>
            <TeamPerfViewTabs activeView={activeView} onViewChange={setActiveView} />
          </div>

          {/* Chart area — switches view without API round-trip */}
          <div className="min-h-[200px]">
            {activeView === 'topSpeed' && (
              <TopSpeedDivergence teams={data.teams} />
            )}
            {activeView === 'meanSpeed' && (
              <MeanSpeedDivergence teams={data.teams} />
            )}
            {activeView === 'quadrant' && (
              <TeamQuadrantScatter
                teams={data.teams}
                fieldAverages={data.fieldAverages}
              />
            )}
          </div>

          {/* Insight cards */}
          <div className="mt-5">
            <TeamPerfInsights
              insights={data.insights}
              fieldAverages={data.fieldAverages}
            />
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
                  What does this panel show?
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    This panel reveals each team&apos;s aerodynamic setup philosophy by
                    decomposing race pace into two components:{' '}
                    <span className="text-gray-400 font-medium">top speed</span>{' '}
                    (straight-line performance) and{' '}
                    <span className="text-gray-400 font-medium">mean speed</span>{' '}
                    (overall pace including corners).
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Three chart views
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Top Speed</span>{' '}
                    &mdash; Shows each team&apos;s average speed trap reading compared
                    to the field average. Teams to the right have lower drag or
                    stronger power units.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Mean Speed</span>{' '}
                    &mdash; Shows each team&apos;s average lap speed (track length
                    divided by fuel-corrected lap time). This captures overall car
                    performance including both straights and corners.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Quadrant</span>{' '}
                    &mdash; Plots both metrics on a single chart. The dashed crosshairs
                    mark the field average. Teams in the top-right are efficient
                    everywhere; those in the bottom-right traded straight-line speed
                    for cornering downforce.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  The four quadrants
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-green-400/70 font-medium">High Efficiency</span>{' '}
                    (top-right) &mdash; Fast everywhere. Strong power unit and
                    aero efficiency.
                  </p>
                  <p>
                    <span className="text-blue-400/70 font-medium">High Downforce</span>{' '}
                    (bottom-right) &mdash; Fast in corners despite a straight-line
                    deficit. High downforce setup.
                  </p>
                  <p>
                    <span className="text-yellow-400/70 font-medium">Low Downforce</span>{' '}
                    (top-left) &mdash; Fast on straights but slow in corners.
                    Low drag, low downforce setup.
                  </p>
                  <p>
                    <span className="text-red-400/70 font-medium">Low Efficiency</span>{' '}
                    (bottom-left) &mdash; Struggling across the board. Below-average
                    pace on both straights and corners.
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

function TeamPerformanceSkeleton() {
  return (
    <section className="card-panel">
      <div className="h-6 w-48 skeleton rounded mb-4" />
      <div className="h-[400px] skeleton rounded-lg" />
      <div className="grid grid-cols-2 gap-4 mt-5">
        <div className="h-24 skeleton rounded" />
        <div className="h-24 skeleton rounded" />
      </div>
    </section>
  )
}
