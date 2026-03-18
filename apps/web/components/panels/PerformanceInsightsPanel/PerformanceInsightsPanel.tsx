'use client'

import { useState } from 'react'
import type { InsightMode, PerformanceInsightsResponse } from '@/../../packages/models/src/types'
import { ModeToggle } from './ModeToggle'
import { DriverInsightCard } from './DriverInsightCard'

interface PerformanceInsightsPanelProps {
  /** Performance data from the unified Phase 6 endpoint */
  data: PerformanceInsightsResponse | undefined
  /** Reference driver code */
  referenceDriver: string
  /** Drivers being compared against reference */
  compareDrivers: string[]
  /** Whether data is loading */
  isLoading: boolean
  /** Whether there was an error */
  isError: boolean
  /** Error object if isError */
  error: Error | null
  /** Current insight mode */
  mode: InsightMode
  /** Callback when mode changes */
  onModeChange: (mode: InsightMode) => void
}

/**
 * Performance Insights Panel - Phase 7 Component
 *
 * Displays rich, actionable performance analysis from the unified
 * Phase 6 endpoint. Now receives data as props from QualifyingContent
 * instead of self-fetching, to avoid redundant analysis calls.
 *
 * Features:
 * - Engineer/Driver mode toggle
 * - Per-driver technique profiles
 * - Dimension bars (braking, apex, exit, consistency)
 * - Focus areas (gaining/losing corners)
 * - Natural language summaries
 */
export function PerformanceInsightsPanel({
  data,
  referenceDriver,
  compareDrivers,
  isLoading,
  isError,
  error,
  mode,
  onModeChange,
}: PerformanceInsightsPanelProps) {
  const [showGuide, setShowGuide] = useState(false)

  // ═══════════════════════════════════════════════════════════════════════════
  // IDLE STATE: No drivers selected
  // ═══════════════════════════════════════════════════════════════════════════
  if (compareDrivers.length === 0) {
    return (
      <div className="card-panel border-f1red/30 bg-gradient-to-br from-f1red/5 to-transparent">
        <div className="flex items-center justify-between mb-4">
          <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide">
            <span className="text-f1red">📊</span>
            Performance Insights
          </h2>
        </div>
        <p className="text-sm text-gray-500">
          Select drivers to compare for performance analysis.
        </p>
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LOADING STATE: Skeleton cards
  // ═══════════════════════════════════════════════════════════════════════════
  if (isLoading) {
    return (
      <div className="card-panel border-f1red/30 bg-gradient-to-br from-f1red/5 to-transparent">
        <div className="flex items-center justify-between mb-4">
          <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide">
            <span className="text-f1red">📊</span>
            Performance Insights
          </h2>
          <span className="text-xs text-gray-500 animate-pulse">
            Analyzing performance...
          </span>
        </div>
        <div className="space-y-4">
          {compareDrivers.map((driver) => (
            <div key={driver} className="rounded-lg border border-f1gray/30 p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-8 w-8 rounded-full bg-f1gray/30" />
                <div className="space-y-2">
                  <div className="h-4 w-24 bg-f1gray/30 rounded" />
                  <div className="h-3 w-40 bg-f1gray/20 rounded" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 w-full bg-f1gray/20 rounded" />
                <div className="h-3 w-3/4 bg-f1gray/20 rounded" />
              </div>
              <div className="mt-4 space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-20 h-3 bg-f1gray/20 rounded" />
                    <div className="flex-1 h-2 bg-f1gray/20 rounded" />
                    <div className="w-8 h-3 bg-f1gray/20 rounded" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ERROR STATE
  // ═══════════════════════════════════════════════════════════════════════════
  if (isError) {
    return (
      <div className="card-panel border-red-500/30 bg-red-500/5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide text-red-400">
            <span>⚠️</span>
            Performance Insights
          </h2>
        </div>
        <p className="text-sm text-red-400/80 mb-4">
          {error?.message || 'Failed to load performance insights.'}
        </p>
        <p className="text-xs text-red-400/60 mt-2">
          Try changing the driver selection or refreshing the page.
        </p>
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SUCCESS STATE: Render driver cards
  // ═══════════════════════════════════════════════════════════════════════════
  if (!data || data.results.length === 0) {
    return (
      <div className="card-panel border-f1red/30 bg-gradient-to-br from-f1red/5 to-transparent">
        <div className="flex items-center justify-between mb-4">
          <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide">
            <span className="text-f1red">📊</span>
            Performance Insights
          </h2>
        </div>
        <p className="text-sm text-gray-500">
          No analysis results available for the selected drivers.
        </p>
      </div>
    )
  }

  return (
    <div className="card-panel border-f1red/30 bg-gradient-to-br from-f1red/5 to-transparent">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide">
          <span className="text-f1red">📊</span>
          Performance Insights
        </h2>
        <div className="flex items-center gap-3">
          <ModeToggle mode={mode} onChange={onModeChange} />
          <span className="inline-flex items-center gap-1 text-xs text-f1red">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            Advanced Analysis
          </span>
        </div>
      </div>

      {/* Driver Cards */}
      <div className="space-y-4">
        {data.results.map((result) => (
          <DriverInsightCard
            key={result.driver}
            result={result}
            referenceDriver={referenceDriver}
            mode={mode}
          />
        ))}
      </div>

      {/* Warnings */}
      {data.warnings && data.warnings.length > 0 && (
        <div className="mt-4 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
          <p className="text-xs font-medium text-yellow-400 mb-1">Warnings:</p>
          <ul className="text-xs text-yellow-400/80 space-y-1">
            {data.warnings.map((warning, i) => (
              <li key={i}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <p>
          Analyzed {data.total_drivers_processed} driver{data.total_drivers_processed !== 1 ? 's' : ''} across{' '}
          {data.total_corners} corners in {data.total_duration_ms}ms
        </p>
      </div>

      {/* How to read these insights */}
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
        How to read these insights
      </button>
      {showGuide && (
        <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] p-4 space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">How Insights Are Generated</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                All insights are computationally generated from the telemetry analysis pipeline. Every statement traces to a specific calculation — there is no AI-generated reasoning or speculation involved. The system uses structured templates filled with measured values.
              </p>
              <p>
                Engineer mode shows technical detail (percentiles, deltas in milliseconds, corner numbers). Driver mode uses simplified language focused on strengths and areas to work on.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Technique Profile Bars</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                Each bar represents a dimension of performance: Braking (corner entry), Apex (mid-corner speed), Exit (corner exit acceleration), Consistency (variation in deltas across corners), and Straight-Line (speed between corners).
              </p>
              <p>
                The percentile (P0–P100) ranks the comparison driver against all drivers in this session. P0 = best in session, P100 = worst. Lower is better.
              </p>
              <p>
                Bar colour: green (strong, top third), yellow (neutral, middle third), red (weak, bottom third). The delta value in milliseconds shows the total time gained or lost across all corners in that dimension.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Focus Areas</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                Gaining/losing corners list the specific turns where the driver has the largest positive or negative time deltas — the highest-leverage areas for performance improvement.
              </p>
              <p>
                Straight-line focus areas identify specific straights with the largest speed advantages or disadvantages.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Data Source &amp; Limitations</h4>
            <div className="text-sm text-gray-500/80 italic space-y-1.5">
              <p>
                All analysis is derived from publicly broadcast telemetry data accessed via the FastF1 library. This data has lower sampling rates and fewer channels than the proprietary telemetry available to F1 teams. Teams have access to hundreds of additional sensor channels (ride height, aero load, damper positions, brake temperatures, energy deployment maps) that enable deeper analysis. The insights shown here represent what can be reliably determined from public data and should be interpreted as informative rather than definitive.
              </p>
              <p>
                Percentiles are session-relative: a &quot;strong braking&quot; profile in one session is not directly comparable to the same rating in a different session with different conditions or fewer drivers.
              </p>
              <p>
                Profiles are based on a limited sample of corners that varies by circuit (as few as 8 on low-downforce circuits, up to 20+ on street circuits). A single unusual corner result can noticeably affect a dimension&apos;s percentile. These profiles are indicative of tendencies rather than precise measurements.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
