'use client'

import { getCompoundColor } from '@/lib/compounds'
import { COMPOUND_DISPLAY_NAMES } from '@/lib/compounds'

interface CompoundTabsProps {
  compounds: string[]
  activeCompound: string
  onCompoundChange: (compound: string) => void
}

/**
 * Tab bar for switching between tyre compounds.
 * Each tab shows a colored dot indicating the compound color.
 * Switching tabs is client-side only — no API call.
 */
export default function CompoundTabs({
  compounds,
  activeCompound,
  onCompoundChange,
}: CompoundTabsProps) {
  if (compounds.length === 0) return null

  return (
    <div className="flex items-center gap-1 border-b border-white/10">
      {compounds.map((compound) => {
        const isActive = compound === activeCompound
        const color = getCompoundColor(compound)
        const displayName = COMPOUND_DISPLAY_NAMES[compound] ?? compound

        return (
          <button
            key={compound}
            onClick={() => onCompoundChange(compound)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              isActive
                ? 'border-current text-white'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
            style={isActive ? { borderColor: color } : undefined}
          >
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            {displayName}
          </button>
        )
      })}
    </div>
  )
}
