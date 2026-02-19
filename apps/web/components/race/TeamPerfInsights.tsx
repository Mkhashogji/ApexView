'use client'

import { getTeamColorForMode } from '@/lib/drivers'
import type { TeamPerformanceInsights } from '@/../../packages/models/src/types'

interface TeamPerfInsightsProps {
  insights: TeamPerformanceInsights
  fieldAverages: { topSpeed: number; meanSpeed: number }
}

/**
 * Template-based insight cards for team performance analysis.
 * Two cards: "Fastest on Straights" and "Highest Mean Speed".
 * All text is deterministic — no AI generation, no hallucination risk.
 *
 * Follows the PitStopInsights pattern: InsightCard sub-component
 * with team-colored left border.
 */
export default function TeamPerfInsights({
  insights,
  fieldAverages,
}: TeamPerfInsightsProps) {
  if (!insights.fastestOnStraights && !insights.highestMeanSpeed) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {insights.fastestOnStraights && (
        <InsightCard
          title="Fastest on Straights"
          team={insights.fastestOnStraights.team}
          text={`${insights.fastestOnStraights.team} had the highest average top speed at ${insights.fastestOnStraights.value.toFixed(1)} km/h, which is ${Math.abs(insights.fastestOnStraights.delta).toFixed(1)} km/h above the field average of ${fieldAverages.topSpeed.toFixed(1)} km/h. This suggests a lower-drag aerodynamic setup or a power unit advantage on the straights.`}
        />
      )}
      {insights.highestMeanSpeed && (
        <InsightCard
          title="Highest Mean Speed"
          team={insights.highestMeanSpeed.team}
          text={`${insights.highestMeanSpeed.team} achieved the highest mean lap speed at ${insights.highestMeanSpeed.value.toFixed(2)} km/h, which is ${Math.abs(insights.highestMeanSpeed.delta).toFixed(2)} km/h above the field average of ${fieldAverages.meanSpeed.toFixed(2)} km/h. This reflects the fastest overall car performance, combining both straight-line speed and cornering pace.`}
        />
      )}
    </div>
  )
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
