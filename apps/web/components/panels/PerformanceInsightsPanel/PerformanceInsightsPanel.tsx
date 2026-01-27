'use client'

import { useState, useMemo } from 'react'
import type { Corner, InsightMode } from '@/../../packages/models/src/types'
import { usePerformanceInsightsQuery } from '@/lib/hooks'
import { ModeToggle } from './ModeToggle'
import { DriverInsightCard } from './DriverInsightCard'

interface PerformanceInsightsPanelProps {
  /** Session identifier */
  sessionId: string
  /** Reference driver code */
  referenceDriver: string
  /** Drivers to compare against reference */
  selectedDrivers: string[]
  /** Track corner definitions */
  corners: Corner[]
  /** Qualifying session part (Q1, Q2, Q3) */
  sessionPart?: string
  /** Track length in meters (required for lap breakdown) */
  trackLength?: number
}

/**
 * Performance Insights Panel - Phase 7 Component
 *
 * Displays rich, actionable performance analysis from the unified
 * Phase 6 endpoint, replacing the old AIInsights component.
 *
 * Features:
 * - Engineer/Driver mode toggle
 * - Per-driver technique profiles
 * - Dimension bars (braking, apex, exit, consistency)
 * - Focus areas (gaining/losing corners)
 * - Natural language summaries
 */
export function PerformanceInsightsPanel({
  sessionId,
  referenceDriver,
  selectedDrivers,
  corners,
  sessionPart,
  trackLength,
}: PerformanceInsightsPanelProps) {
  const [mode, setMode] = useState<InsightMode>('engineer')

  // Filter out reference driver from comparison list
  const compareDrivers = useMemo(
    () => selectedDrivers.filter((d) => d !== referenceDriver),
    [selectedDrivers, referenceDriver]
  )

  // Fetch performance insights
  const { data, isLoading, isError, error, refetch } = usePerformanceInsightsQuery({
    sessionId,
    referenceDriver,
    compareDrivers,
    corners,
    mode,
    sessionPart,
    trackLength,
  })

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
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-md bg-red-500/20 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/30 focus:outline-none focus:ring-2 focus:ring-red-500/50"
        >
          Retry
        </button>
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
          <ModeToggle mode={mode} onChange={setMode} />
          <span className="inline-flex items-center gap-1 text-xs text-f1red">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            AI Enhanced
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
    </div>
  )
}
