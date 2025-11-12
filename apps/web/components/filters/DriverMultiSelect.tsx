'use client'

import { DRIVERS_2025, getTeamColor } from '@/lib/drivers'
import { useState } from 'react'

interface DriverMultiSelectProps {
  selected: string[]
  onChange: (drivers: string[]) => void
  maxDrivers?: number
}

export function DriverMultiSelect({ selected, onChange, maxDrivers = 6 }: DriverMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)

  const toggleDriver = (driverAbbr: string) => {
    if (selected.includes(driverAbbr)) {
      // Remove driver
      onChange(selected.filter((d) => d !== driverAbbr))
    } else {
      // Add driver if under max
      if (selected.length < maxDrivers) {
        onChange([...selected, driverAbbr])
      }
    }
  }

  return (
    <div className="relative">
      <label className="mb-1 block text-sm font-medium">Drivers (max {maxDrivers}):</label>
      
      {/* Selected drivers badges */}
      <div className="flex flex-wrap gap-2 mb-2">
        {selected.map((driverAbbr) => {
          const color = getTeamColor(driverAbbr)
          return (
            <button
              key={driverAbbr}
              onClick={() => toggleDriver(driverAbbr)}
              className="flex items-center gap-1 rounded px-2 py-1 text-sm font-medium text-white hover:opacity-80"
              style={{ backgroundColor: color }}
            >
              {driverAbbr}
              <span className="text-xs">×</span>
            </button>
          )
        })}
        {selected.length === 0 && (
          <span className="text-sm text-gray-500">Select drivers...</span>
        )}
      </div>

      {/* Dropdown toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="rounded bg-f1dark px-3 py-2 text-sm hover:bg-f1gray"
      >
        {isOpen ? 'Close' : 'Add Drivers'}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 mt-2 max-h-96 w-64 overflow-y-auto rounded-lg border border-f1gray bg-f1dark shadow-lg">
          <div className="p-2">
            {DRIVERS_2025.map((driver) => {
              const isSelected = selected.includes(driver.abbreviation)
              const canSelect = selected.length < maxDrivers || isSelected
              
              return (
                <button
                  key={driver.abbreviation}
                  onClick={() => canSelect && toggleDriver(driver.abbreviation)}
                  disabled={!canSelect}
                  className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm transition-colors ${
                    isSelected
                      ? 'bg-f1gray font-semibold'
                      : canSelect
                      ? 'hover:bg-f1gray/50'
                      : 'cursor-not-allowed opacity-40'
                  }`}
                  title={driver.fullName}
                >
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: driver.teamColor }}
                  />
                  <span className="font-medium">{driver.abbreviation}</span>
                  <span className="text-xs text-gray-400">{driver.fullName}</span>
                  {isSelected && <span className="ml-auto">✓</span>}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

