'use client'

import { DRIVERS_2025, getTeamColor, getDriverInfo, getAllTeams, getDriversByTeam } from '@/lib/drivers'
import { useState, useRef, useEffect, useCallback } from 'react'

interface DriverMultiSelectProps {
  selected: string[]
  onChange: (drivers: string[]) => void
  maxDrivers?: number
}

/** Team preset configurations */
const TEAM_PRESETS = [
  { label: 'Top 3', drivers: ['VER', 'NOR', 'LEC'] },
  { label: 'Red Bull', team: 'Red Bull Racing' },
  { label: 'Ferrari', team: 'Ferrari' },
  { label: 'McLaren', team: 'McLaren' },
  { label: 'Mercedes', team: 'Mercedes' },
]

export function DriverMultiSelect({ selected, onChange, maxDrivers = 6 }: DriverMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        !buttonRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false)
      buttonRef.current?.focus()
    }
  }, [])

  const toggleDriver = (driverAbbr: string) => {
    if (selected.includes(driverAbbr)) {
      onChange(selected.filter((d) => d !== driverAbbr))
    } else if (selected.length < maxDrivers) {
      onChange([...selected, driverAbbr])
    }
  }

  const removeDriver = (driverAbbr: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onChange(selected.filter((d) => d !== driverAbbr))
  }

  const applyPreset = (preset: typeof TEAM_PRESETS[0]) => {
    let drivers: string[]
    if (preset.drivers) {
      drivers = preset.drivers
    } else if (preset.team) {
      drivers = getDriversByTeam(preset.team).map(d => d.abbreviation)
    } else {
      return
    }
    // Limit to maxDrivers
    onChange(drivers.slice(0, maxDrivers))
  }

  const clearAll = () => {
    onChange([])
  }

  return (
    <div className="relative isolate" onKeyDown={handleKeyDown}>
      {/* Label */}
      <label 
        id="driver-select-label"
        className="mb-2 block text-sm font-medium text-gray-300"
      >
        Drivers ({selected.length}/{maxDrivers})
      </label>
      
      {/* Selected driver chips */}
      <div 
        className="flex flex-wrap gap-2 mb-3 min-h-[36px]"
        role="listbox"
        aria-labelledby="driver-select-label"
        aria-multiselectable="true"
      >
        {selected.map((driverAbbr) => {
          const driver = getDriverInfo(driverAbbr)
          const color = getTeamColor(driverAbbr)
          return (
            <div
              key={driverAbbr}
              className="driver-chip group cursor-default"
              style={{ backgroundColor: color }}
              role="option"
              aria-selected="true"
              title={driver?.fullName || driverAbbr}
            >
              <span className="font-semibold">{driverAbbr}</span>
              <button
                onClick={(e) => removeDriver(driverAbbr, e)}
                className="ml-1 rounded-full p-0.5 hover:bg-black/20 focus-ring"
                aria-label={`Remove ${driver?.fullName || driverAbbr}`}
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              {/* Tooltip with full name on hover */}
              <span className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-2 py-1 text-xs opacity-0 transition-opacity group-hover:opacity-100 pointer-events-none">
                {driver?.fullName}
              </span>
            </div>
          )
        })}
        {selected.length === 0 && (
          <span className="text-sm text-gray-500 italic">No drivers selected</span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          ref={buttonRef}
          onClick={() => setIsOpen(!isOpen)}
          className="rounded-md bg-f1gray/50 px-4 py-2 text-sm font-medium transition-colors hover:bg-f1gray focus-ring"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-label="Add drivers"
        >
          {isOpen ? 'Close' : '+ Add Drivers'}
        </button>
        
        {selected.length > 0 && (
          <button
            onClick={clearAll}
            className="rounded-md px-3 py-2 text-sm text-gray-400 transition-colors hover:text-white hover:bg-f1gray/30 focus-ring"
            aria-label="Clear all selected drivers"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Dropdown - mt-0 with pt-2 inside to avoid gap that causes hover issues */}
      {isOpen && (
        <div 
          ref={dropdownRef}
          className="absolute z-50 mt-0 pt-2 w-80"
          role="dialog"
          aria-label="Select drivers"
        >
          <div className="rounded-lg border border-f1gray bg-f1dark/95 backdrop-blur shadow-xl">
          {/* Quick presets */}
          <div className="border-b border-f1gray p-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-400">
              Quick Select
            </p>
            <div className="flex flex-wrap gap-2">
              {TEAM_PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => applyPreset(preset)}
                  className="rounded-md bg-f1gray/50 px-3 py-1.5 text-xs font-medium transition-colors hover:bg-f1red hover:text-white focus-ring"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Driver list */}
          <div className="max-h-72 overflow-y-auto p-2">
            {/* Group by team */}
            {getAllTeams().map((team) => {
              const teamDrivers = getDriversByTeam(team)
              return (
                <div key={team} className="mb-2">
                  <p className="px-2 py-1 text-xs font-medium text-gray-500">{team}</p>
                  {teamDrivers.map((driver) => {
                    const isSelected = selected.includes(driver.abbreviation)
                    const canSelect = selected.length < maxDrivers || isSelected
                    
                    return (
                      <button
                        key={driver.abbreviation}
                        onClick={() => canSelect && toggleDriver(driver.abbreviation)}
                        disabled={!canSelect}
                        className={`
                          flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors
                          focus-ring
                          ${isSelected
                            ? 'bg-f1gray/80 font-semibold'
                            : canSelect
                            ? 'hover:bg-f1gray/40'
                            : 'cursor-not-allowed opacity-40'
                          }
                        `}
                        role="option"
                        aria-selected={isSelected}
                        aria-disabled={!canSelect}
                      >
                        <span
                          className="h-3 w-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: driver.teamColor }}
                          aria-hidden="true"
                        />
                        <span className="font-medium w-10">{driver.abbreviation}</span>
                        <span className="text-gray-400 truncate">{driver.fullName}</span>
                        {isSelected && (
                          <svg className="ml-auto h-4 w-4 text-f1red flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </div>
          </div>
        </div>
      )}
    </div>
  )
}

