'use client'

export type PitStopView = 'byTeam' | 'byDriver' | 'gapToFastest'

interface PitStopViewTabsProps {
  activeView: PitStopView
  onViewChange: (view: PitStopView) => void
}

const VIEWS: { key: PitStopView; label: string }[] = [
  { key: 'byTeam', label: 'By Team' },
  { key: 'byDriver', label: 'By Driver' },
  { key: 'gapToFastest', label: 'Gap to Fastest' },
]

/**
 * Three-tab switcher for pit stop chart views.
 * Styled to match the Race page tab pattern (CompoundTabs).
 * Switching is client-side only — no API call.
 */
export default function PitStopViewTabs({
  activeView,
  onViewChange,
}: PitStopViewTabsProps) {
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
