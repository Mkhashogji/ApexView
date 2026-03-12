'use client'

import { useState, useRef, useEffect, useTransition } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import raceCalendarData from '@/data/race-calendar-2025.json'

interface Race {
  round: number
  name: string
  shortName: string
  circuit: string
  country: string
  city: string
  date: string
  isSprint?: boolean
}

const RACE_CALENDAR: Race[] = raceCalendarData.races

/**
 * Race weekend selector dropdown for the navigation bar.
 * Allows users to switch between different race weekends.
 */
export function RaceWeekendSelector() {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, startTransition] = useTransition()
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  // Get current selection from URL params
  const currentRound = parseInt(searchParams.get('round') || '24')
  const currentSeason = parseInt(searchParams.get('season') || '2025')
  const currentRace = RACE_CALENDAR.find(r => r.round === currentRound)

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

  // Close on escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        buttonRef.current?.focus()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const handleSelect = (round: number) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('round', String(round))
    params.set('season', String(currentSeason))

    // Navigate with startTransition to keep UI responsive during round switch
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`)
    })
    setIsOpen(false)
  }

  // Determine if a race date is in the past
  const isPastRace = (dateString: string) => {
    const raceDate = new Date(dateString)
    const today = new Date()
    return raceDate < today
  }

  return (
    <div className="relative">
      {/* Selector Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-md bg-f1gray/50 px-3 py-2 text-sm font-medium transition-colors hover:bg-f1gray focus-ring"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label={`${currentSeason} ${currentRace?.shortName || 'Select Race'} — select race weekend`}
      >
        <span className="text-gray-400">{currentSeason}</span>
        <span className="text-white">•</span>
        <span className="text-white">{currentRace?.shortName || 'Select Race'}</span>
        {isPending ? (
          <div className="h-4 w-4 rounded-full border-2 border-f1red border-t-transparent animate-spin" />
        ) : (
          <svg
            className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 z-50 mt-2 w-72 max-h-96 overflow-y-auto rounded-lg border border-f1gray bg-f1dark/95 backdrop-blur shadow-xl"
          role="listbox"
          aria-label="Race weekends"
        >
          {/* Completed Races */}
          <div className="p-2">
            <p className="px-3 py-2 text-xs font-medium uppercase tracking-wide text-gray-500">
              Completed
            </p>
            {RACE_CALENDAR.filter(race => isPastRace(race.date)).map((race) => (
              <RaceOption
                key={race.round}
                race={race}
                isSelected={race.round === currentRound}
                onSelect={handleSelect}
              />
            ))}
          </div>

          {/* Divider */}
          <hr className="border-f1gray/50" />

          {/* Upcoming Races */}
          <div className="p-2">
            <p className="px-3 py-2 text-xs font-medium uppercase tracking-wide text-gray-500">
              Upcoming
            </p>
            {RACE_CALENDAR.filter(race => !isPastRace(race.date)).map((race) => (
              <RaceOption
                key={race.round}
                race={race}
                isSelected={race.round === currentRound}
                onSelect={handleSelect}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** Individual race option in dropdown */
function RaceOption({ 
  race, 
  isSelected, 
  onSelect 
}: { 
  race: Race
  isSelected: boolean
  onSelect: (round: number) => void 
}) {
  return (
    <button
      onClick={() => onSelect(race.round)}
      className={`
        flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors
        focus-ring
        ${isSelected
          ? 'bg-f1red/20 text-white'
          : 'hover:bg-f1gray/40 text-gray-300'
        }
      `}
      role="option"
      aria-selected={isSelected}
    >
      <span className="w-6 text-xs text-gray-500 font-mono">
        R{race.round}
      </span>
      <span className={`flex-1 truncate ${isSelected ? 'font-medium' : ''}`}>
        {race.shortName}
      </span>
      {race.isSprint && (
        <span className="rounded bg-purple-500/20 px-1.5 py-0.5 text-xs text-purple-400">
          Sprint
        </span>
      )}
      {isSelected && (
        <svg className="h-4 w-4 text-f1red flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  )
}
