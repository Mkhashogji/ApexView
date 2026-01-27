'use client'

import type { DimensionType, DimensionLevel } from '@/../../packages/models/src/types'

interface DimensionBarProps {
  /** Dimension type */
  dimension: DimensionType
  /** Percentile rank (0-100, lower is better) */
  percentile: number
  /** Performance level */
  level: DimensionLevel
  /** Time delta in seconds (optional) */
  delta?: number
  /** Override default label */
  label?: string
}

/** Label mapping for dimensions */
const DIMENSION_LABELS: Record<DimensionType, string> = {
  braking: 'Braking',
  apex: 'Apex',
  exit: 'Exit',
  consistency: 'Consistency',
}

/** Color mapping for performance levels */
const LEVEL_COLORS: Record<DimensionLevel, string> = {
  strong: 'bg-green-500',
  neutral: 'bg-yellow-500',
  weak: 'bg-red-500',
}

/**
 * Display a single dimension (braking/apex/exit/consistency)
 * with percentile progress bar, level indicator, and optional delta.
 */
export function DimensionBar({
  dimension,
  percentile,
  level,
  delta,
  label,
}: DimensionBarProps) {
  const displayLabel = label ?? DIMENSION_LABELS[dimension]
  const barColor = LEVEL_COLORS[level]

  // Format delta as milliseconds
  const formatDelta = (seconds: number) => {
    const ms = Math.round(seconds * 1000)
    const sign = ms >= 0 ? '+' : ''
    return `${sign}${ms}ms`
  }

  // Convert percentile to bar width (percentile 0 = 100% width = best)
  // Lower percentile is better, so invert for visual representation
  const barWidth = 100 - percentile

  return (
    <div className="flex items-center gap-3">
      {/* Label */}
      <span className="w-24 text-sm text-gray-400">{displayLabel}</span>

      {/* Progress bar container */}
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${barColor}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>

      {/* Percentile badge */}
      <span className="w-12 text-right font-mono text-xs text-gray-400">
        P{Math.round(percentile)}
      </span>

      {/* Delta (if applicable) */}
      {delta !== undefined && (
        <span
          className={`w-16 text-right font-mono text-xs ${
            delta <= 0 ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {formatDelta(delta)}
        </span>
      )}
    </div>
  )
}
