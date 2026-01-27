'use client'

import type { InsightMode } from '@/../../packages/models/src/types'
import { CornerChip } from './CornerChip'

interface FocusAreasProps {
  /** Corners where driver gains time */
  gainingCorners: string[]
  /** Corners where driver loses time */
  losingCorners: string[]
  /** Current insight mode */
  mode: InsightMode
}

/**
 * Display gaining and losing corners as chip groups.
 * Labels change based on mode:
 * - Engineer mode: "Gaining:" / "Losing:"
 * - Driver mode: "Strengths:" / "Work On:"
 */
export function FocusAreas({ gainingCorners, losingCorners, mode }: FocusAreasProps) {
  const gainLabel = mode === 'engineer' ? 'Gaining:' : 'Strengths:'
  const lossLabel = mode === 'engineer' ? 'Losing:' : 'Work On:'

  const hasGains = gainingCorners.length > 0
  const hasLosses = losingCorners.length > 0

  if (!hasGains && !hasLosses) {
    return (
      <div className="text-sm text-gray-500">
        No significant corner gains or losses identified.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Focus Areas
      </h4>

      {hasGains && (
        <div className="flex items-start gap-2">
          <span className="w-20 text-xs text-gray-400 pt-0.5">{gainLabel}</span>
          <div className="flex flex-wrap gap-1.5">
            {gainingCorners.map((corner) => (
              <CornerChip key={corner} corner={corner} type="gain" />
            ))}
          </div>
        </div>
      )}

      {hasLosses && (
        <div className="flex items-start gap-2">
          <span className="w-20 text-xs text-gray-400 pt-0.5">{lossLabel}</span>
          <div className="flex flex-wrap gap-1.5">
            {losingCorners.map((corner) => (
              <CornerChip key={corner} corner={corner} type="loss" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
