'use client'

import { useState, useRef, useEffect } from 'react'
import { getTeamColorForMode } from '@/lib/drivers'

interface DriverChipSelectorProps {
  identifiers: string[]
  selectedIdentifiers: string[]
  onSelectionChange: (selected: string[]) => void
  mode: 'driver' | 'team'
  /** 'dropdown' (default): selected chips + "Add" overlay dropdown.
   *  'inline': all identifiers shown as toggleable chips — selected
   *  are solid, unselected are outlined. Panel auto-sizes. */
  displayMode?: 'dropdown' | 'inline'
}

/**
 * Multi-select chip picker for drivers or teams.
 * Dismissible chips with team color accents.
 * Client-side filtering only — no API calls.
 */
export default function DriverChipSelector({
  identifiers,
  selectedIdentifiers,
  onSelectionChange,
  mode,
  displayMode = 'dropdown',
}: DriverChipSelectorProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unselected = identifiers.filter((id) => !selectedIdentifiers.includes(id))
  const allSelected = selectedIdentifiers.length === identifiers.length
  const noneSelected = selectedIdentifiers.length === 0

  const handleRemove = (id: string) => {
    onSelectionChange(selectedIdentifiers.filter((s) => s !== id))
  }

  const handleAdd = (id: string) => {
    onSelectionChange([...selectedIdentifiers, id])
    setShowDropdown(false)
  }

  const handleSelectAll = () => {
    onSelectionChange([...identifiers])
  }

  const handleClearAll = () => {
    onSelectionChange([])
  }

  // ── Inline mode: all identifiers as toggleable chips ──────────────
  if (displayMode === 'inline') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500 uppercase tracking-wider">
            {mode === 'driver' ? 'Drivers' : 'Teams'}
          </span>
          <div className="flex items-center gap-2">
            {!allSelected && (
              <button
                onClick={handleSelectAll}
                className="text-xs text-gray-500 hover:text-white transition-colors"
              >
                Select All
              </button>
            )}
            {!noneSelected && (
              <button
                onClick={handleClearAll}
                className="text-xs text-gray-500 hover:text-white transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {identifiers.map((id) => {
            const color = getTeamColorForMode(id, mode)
            const isSelected = selectedIdentifiers.includes(id)

            if (isSelected) {
              return (
                <button
                  key={id}
                  onClick={() => handleRemove(id)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-white/10 text-gray-200 border border-white/10 hover:bg-white/20 transition-colors cursor-pointer"
                  style={{ borderLeftColor: color, borderLeftWidth: 3 }}
                >
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  {id}
                </button>
              )
            }

            return (
              <button
                key={id}
                onClick={() => handleAdd(id)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-gray-500 border border-dashed border-white/15 hover:bg-white/10 hover:text-gray-300 transition-colors cursor-pointer"
                style={{ borderLeftColor: `${color}66`, borderLeftWidth: 3 }}
              >
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0 opacity-40"
                  style={{ backgroundColor: color }}
                />
                {id}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  // ── Dropdown mode (default): selected chips + "Add" overlay ──────
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider">
          {mode === 'driver' ? 'Drivers' : 'Teams'}
        </span>
        <div className="flex items-center gap-2">
          {!allSelected && (
            <button
              onClick={handleSelectAll}
              className="text-xs text-gray-500 hover:text-white transition-colors"
            >
              Select All
            </button>
          )}
          {!noneSelected && (
            <button
              onClick={handleClearAll}
              className="text-xs text-gray-500 hover:text-white transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {selectedIdentifiers.map((id) => {
          const color = getTeamColorForMode(id, mode)
          return (
            <span
              key={id}
              className="inline-flex items-center gap-1 pl-2 pr-1 py-0.5 rounded-full text-xs font-medium bg-white/10 text-gray-200 border border-white/10"
              style={{ borderLeftColor: color, borderLeftWidth: 3 }}
            >
              {id}
              <button
                onClick={() => handleRemove(id)}
                className="ml-0.5 p-0.5 rounded-full hover:bg-white/20 transition-colors text-gray-400 hover:text-white"
                aria-label={`Remove ${id}`}
              >
                <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M3 3L9 9M9 3L3 9"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </span>
          )
        })}

        {/* Add button with dropdown */}
        {unselected.length > 0 && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs text-gray-500 hover:text-white hover:bg-white/10 border border-dashed border-white/20 transition-colors"
            >
              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6 2V10M2 6H10"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
              Add
            </button>
            {showDropdown && (
              <div className="absolute z-50 mt-1 py-1 bg-f1dark border border-white/10 rounded-lg shadow-xl min-w-[160px] max-h-60 overflow-y-auto">
                {unselected.map((id) => {
                  const color = getTeamColorForMode(id, mode)
                  return (
                    <button
                      key={id}
                      onClick={() => handleAdd(id)}
                      className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-white/10 hover:text-white flex items-center gap-2 transition-colors"
                    >
                      <span
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      {id}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
