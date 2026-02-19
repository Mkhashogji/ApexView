'use client'

import type { AnomalyNote } from '@/../../packages/models/src/types'

interface PitStopAnomalyNoteProps {
  anomalies: AnomalyNote[]
}

/**
 * Brief text note listing pit stops excluded from averages.
 * Renders only when anomalies exist — returns null otherwise.
 * Deliberately minimal: faded text, small font, subtle border.
 */
export default function PitStopAnomalyNote({
  anomalies,
}: PitStopAnomalyNoteProps) {
  if (anomalies.length === 0) return null

  return (
    <div className="text-xs text-gray-500 border-t border-white/5 pt-3">
      <p className="font-medium text-gray-400 mb-1">
        Excluded from averages:
      </p>
      {anomalies.map((a) => (
        <p key={`${a.driver}-${a.stopNumber}`}>
          {a.driver} (Stop {a.stopNumber}, Lap {a.lapNumber})
          {a.pitLaneTime != null && ` \u2014 ${a.pitLaneTime.toFixed(1)}s`}
        </p>
      ))}
    </div>
  )
}
