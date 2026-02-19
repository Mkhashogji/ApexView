'use client'

export type TeamPerfView = 'topSpeed' | 'meanSpeed' | 'quadrant'

interface TeamPerfViewTabsProps {
  activeView: TeamPerfView
  onViewChange: (view: TeamPerfView) => void
}

const VIEWS: { key: TeamPerfView; label: string }[] = [
  { key: 'topSpeed', label: 'Top Speed' },
  { key: 'meanSpeed', label: 'Mean Speed' },
  { key: 'quadrant', label: 'Quadrant' },
]

/**
 * Three-tab switcher for team performance chart views.
 * Styled to match the Phase 4 PitStopViewTabs pattern.
 * Switching is client-side only — no API call.
 */
export default function TeamPerfViewTabs({
  activeView,
  onViewChange,
}: TeamPerfViewTabsProps) {
  return (
    <div className="flex items-center gap-1 border-b border-white/10">
      {VIEWS.map(({ key, label }) => {
        const isActive = key === activeView
        return (
          <button
            key={key}
            onClick={() => onViewChange(key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              isActive
                ? 'border-f1red text-white'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
