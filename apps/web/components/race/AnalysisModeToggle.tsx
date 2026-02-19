'use client'

interface AnalysisModeToggleProps {
  mode: 'driver' | 'team'
  onModeChange: (mode: 'driver' | 'team') => void
}

/**
 * Radio toggle for switching between Driver and Team analysis modes.
 * Mode changes trigger a backend refetch (different regression computation).
 */
export default function AnalysisModeToggle({
  mode,
  onModeChange,
}: AnalysisModeToggleProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
      <button
        onClick={() => onModeChange('driver')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          mode === 'driver'
            ? 'bg-f1red text-white'
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
      >
        Driver Analysis
      </button>
      <button
        onClick={() => onModeChange('team')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          mode === 'team'
            ? 'bg-f1red text-white'
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
      >
        Team Analysis
      </button>
    </div>
  )
}
