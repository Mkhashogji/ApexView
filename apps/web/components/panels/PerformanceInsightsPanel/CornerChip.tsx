'use client'

interface CornerChipProps {
  /** Corner name (e.g., "Turn 1", "T3") */
  corner: string
  /** Whether this is a gaining or losing corner */
  type: 'gain' | 'loss'
}

/**
 * Small badge showing a corner with gain/loss coloring.
 * Green for corners where driver gains time, red for time lost.
 */
export function CornerChip({ corner, type }: CornerChipProps) {
  const isGain = type === 'gain'

  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium border ${
        isGain
          ? 'bg-green-900/30 text-green-400 border-green-700/50'
          : 'bg-red-900/30 text-red-400 border-red-700/50'
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${isGain ? 'bg-green-400' : 'bg-red-400'}`}
      />
      {corner}
    </span>
  )
}
