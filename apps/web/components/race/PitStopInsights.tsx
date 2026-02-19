'use client'

import { getTeamColorForMode } from '@/lib/drivers'
import type { PitStopInsights as PitStopInsightsType } from '@/../../packages/models/src/types'

interface PitStopInsightsProps {
  insights: PitStopInsightsType
}

/**
 * Template-based insight cards for pit stop analysis.
 * Two cards: "Quickest on Average" and "Most Consistent".
 * All text is deterministic — no AI generation, no hallucination risk.
 *
 * The "Most Consistent" card selects template wording based on
 * consistencyType ('iqr' for ≥3 stops, 'range' for exactly 2 stops).
 */
export default function PitStopInsights({ insights }: PitStopInsightsProps) {
  if (!insights.quickest && !insights.mostConsistent) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {insights.quickest && (
        <InsightCard
          title="Quickest on Average"
          team={insights.quickest.team}
          text={`${insights.quickest.team} was the quickest team in the pit lane, with an average total time of ${insights.quickest.averageTime.toFixed(2)}s. This is ${insights.quickest.percentageFaster.toFixed(1)}% faster than the grid's overall average of ${insights.quickest.gridAverage.toFixed(2)}s.`}
        />
      )}
      {insights.mostConsistent && (
        <InsightCard
          title="Most Consistent"
          team={insights.mostConsistent.team}
          text={buildConsistencyText(insights.mostConsistent)}
        />
      )}
    </div>
  )
}

/**
 * Select template wording based on consistency type.
 *
 * 'iqr' (≥3 stops): References IQR and the "middle 50%" concept.
 * 'range' (exactly 2 stops): Plain language about the difference
 *   between two stops — no statistical jargon.
 */
function buildConsistencyText(insight: {
  team: string
  consistency: number
  consistencyType: 'iqr' | 'range'
}): string {
  const value = insight.consistency.toFixed(3)

  if (insight.consistencyType === 'iqr') {
    return `${insight.team} was the most consistent, with an Interquartile Range (IQR) of just ${value}s. This means the middle 50% of their pit stop times fall within this very narrow window.`
  }

  // consistencyType === 'range' (one-stop strategy, 2 total stops)
  return `${insight.team} was the most consistent, with just ${value}s separating their two pit stops.`
}

function InsightCard({
  title,
  team,
  text,
}: {
  title: string
  team: string
  text: string
}) {
  const teamColor = getTeamColorForMode(team, 'team')

  return (
    <div
      className="rounded-lg border border-white/10 bg-f1dark/60 p-4"
      style={{ borderLeftWidth: '3px', borderLeftColor: teamColor }}
    >
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-300 leading-relaxed">{text}</p>
    </div>
  )
}
