'use client'

import { useState } from 'react'
import type {
  DriverPerformanceResult,
  InsightMode,
} from '@/../../packages/models/src/types'
import { getTeamColor } from '@/lib/drivers'
import { TechniqueProfileDisplay } from './TechniqueProfileDisplay'
import { FocusAreas } from './FocusAreas'
import { LapBreakdownPanel } from '@/components/panels/LapBreakdownPanel'

interface DriverInsightCardProps {
  /** Driver performance result from Phase 6 */
  result: DriverPerformanceResult
  /** Reference driver code */
  referenceDriver: string
  /** Current insight mode */
  mode: InsightMode
}

/**
 * Display gaining and losing straights as chip groups (5th dimension).
 */
function StraightFocusAreas({
  gainingStraights,
  losingStraights,
  mode,
}: {
  gainingStraights: string[]
  losingStraights: string[]
  mode: InsightMode
}) {
  const gainLabel = mode === 'engineer' ? 'Gaining (Straights):' : 'Strong Straights:'
  const lossLabel = mode === 'engineer' ? 'Losing (Straights):' : 'Work On (Straights):'

  const hasGains = gainingStraights.length > 0
  const hasLosses = losingStraights.length > 0

  if (!hasGains && !hasLosses) {
    return null
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Straight-Line Focus
      </h4>

      {hasGains && (
        <div className="flex items-start gap-2">
          <span className="w-28 text-xs text-gray-400 pt-0.5">{gainLabel}</span>
          <div className="flex flex-wrap gap-1.5">
            {gainingStraights.map((straight) => (
              <span
                key={straight}
                className="px-2 py-0.5 text-xs rounded bg-green-500/20 text-green-400 border border-green-500/30"
              >
                {straight}
              </span>
            ))}
          </div>
        </div>
      )}

      {hasLosses && (
        <div className="flex items-start gap-2">
          <span className="w-28 text-xs text-gray-400 pt-0.5">{lossLabel}</span>
          <div className="flex flex-wrap gap-1.5">
            {losingStraights.map((straight) => (
              <span
                key={straight}
                className="px-2 py-0.5 text-xs rounded bg-red-500/20 text-red-400 border border-red-500/30"
              >
                {straight}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Complete card for one driver's performance insights.
 * Includes header, summary, technique profile, and focus areas.
 */
export function DriverInsightCard({
  result,
  referenceDriver,
  mode,
}: DriverInsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const teamColor = getTeamColor(result.driver)

  // Get summary text based on mode
  const summaryText =
    result.insight?.summary || result.technique_profile?.style_summary || 'Analysis in progress...'

  // Get headline (style summary from technique profile)
  const headline = result.technique_profile?.style_summary || ''

  // Format delta for display
  const formatDelta = (seconds: number) => {
    const sign = seconds >= 0 ? '+' : ''
    return `${sign}${seconds.toFixed(3)}s`
  }

  return (
    <article
      className="rounded-lg border border-f1gray/50 bg-f1dark/60"
      style={{ borderLeftColor: teamColor, borderLeftWidth: '3px' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-f1gray/30">
        <div className="flex items-center gap-3">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
            style={{ backgroundColor: `${teamColor}30`, color: teamColor }}
          >
            {result.driver}
          </span>
          <div>
            <h3 className="text-sm font-semibold text-gray-200">
              {result.driver} vs {referenceDriver}
            </h3>
            {headline && (
              <p className="text-xs text-gray-400 italic">&quot;{headline}&quot;</p>
            )}
          </div>
        </div>

        {/* Delta badge */}
        <span
          className={`rounded-full px-2 py-1 text-xs font-mono ${
            result.official_gap <= 0
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}
        >
          {formatDelta(result.official_gap)}
        </span>
      </div>

      {/* Summary */}
      <div className="p-4 border-b border-f1gray/30">
        <p className="text-sm text-gray-300 leading-relaxed">{summaryText}</p>
        {result.insight?.confidence_level && (
          <p className="mt-2 text-xs text-gray-500">
            Confidence: {result.insight.confidence_level}
          </p>
        )}
      </div>

      {/* Lap Breakdown - 5th Dimension */}
      {result.lap_breakdown && (
        <div className="p-4 border-b border-f1gray/30">
          <LapBreakdownPanel
            breakdown={result.lap_breakdown}
            compDriver={result.driver}
            className="border-0 bg-transparent p-0"
          />
        </div>
      )}

      {/* Technique Profile */}
      {result.technique_profile && (
        <div className="p-4 border-b border-f1gray/30">
          <TechniqueProfileDisplay profile={result.technique_profile} />
        </div>
      )}

      {/* Focus Areas - Corners */}
      {result.technique_profile && (
        <div className="p-4 border-b border-f1gray/30">
          <FocusAreas
            gainingCorners={result.technique_profile.top_gaining_corners}
            losingCorners={result.technique_profile.top_losing_corners}
            mode={mode}
          />
        </div>
      )}

      {/* Focus Areas - Straights (5th Dimension) */}
      {result.technique_profile?.straight_line && (
        <div className="p-4">
          <StraightFocusAreas
            gainingStraights={result.technique_profile.straight_line.top_gaining_straights}
            losingStraights={result.technique_profile.straight_line.top_losing_straights}
            mode={mode}
          />
        </div>
      )}

      {/* Expandable Details */}
      {result.insight?.dimension_insights && result.insight.dimension_insights.length > 0 && (
        <div className="border-t border-f1gray/30">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex w-full items-center justify-between px-4 py-2 text-xs text-gray-400 hover:bg-f1gray/10 transition-colors"
          >
            <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
            <svg
              className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {isExpanded && (
            <div className="px-4 pb-4 space-y-3">
              {result.insight.dimension_insights.map((insight) => (
                <div key={insight.dimension} className="text-sm">
                  <span className="font-medium text-gray-300 capitalize">
                    {insight.dimension}:
                  </span>{' '}
                  <span className="text-gray-400">{insight.text}</span>
                </div>
              ))}

              {result.insight.opportunity_text && (
                <div className="mt-3 p-3 rounded bg-f1gray/20 border border-f1gray/30">
                  <p className="text-xs text-gray-300">
                    <span className="font-medium">Opportunity: </span>
                    {result.insight.opportunity_text}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  )
}
