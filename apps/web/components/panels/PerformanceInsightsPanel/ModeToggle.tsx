'use client'

import type { InsightMode } from '@/../../packages/models/src/types'

interface ModeToggleProps {
  /** Current mode */
  mode: InsightMode
  /** Callback when mode changes */
  onChange: (mode: InsightMode) => void
}

/**
 * Toggle between Engineer and Driver insight modes.
 * Engineer mode shows metrics-heavy technical analysis.
 * Driver mode shows actionable coaching-style feedback.
 */
export function ModeToggle({ mode, onChange }: ModeToggleProps) {
  return (
    <div className="flex gap-1 rounded-lg bg-gray-800/50 p-1">
      <button
        type="button"
        onClick={() => onChange('engineer')}
        className={`rounded-md px-3 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-f1red/50 ${
          mode === 'engineer'
            ? 'bg-f1red text-white'
            : 'bg-transparent text-gray-400 hover:text-white'
        }`}
        aria-pressed={mode === 'engineer'}
      >
        Engineer
      </button>
      <button
        type="button"
        onClick={() => onChange('driver')}
        className={`rounded-md px-3 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-f1red/50 ${
          mode === 'driver'
            ? 'bg-f1red text-white'
            : 'bg-transparent text-gray-400 hover:text-white'
        }`}
        aria-pressed={mode === 'driver'}
      >
        Driver
      </button>
    </div>
  )
}
