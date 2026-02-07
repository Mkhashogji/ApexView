'use client'

import { useSearchParams } from 'next/navigation'
import raceCalendarData from '@/data/race-calendar-2025.json'

const RACE_CALENDAR = raceCalendarData.races
const DEFAULT_SEASON = 2025
const DEFAULT_ROUND = 24

export function QualifyingSubtitle() {
  const searchParams = useSearchParams()
  const season = parseInt(searchParams.get('season') || String(DEFAULT_SEASON))
  const round = parseInt(searchParams.get('round') || String(DEFAULT_ROUND))
  const raceName = RACE_CALENDAR.find(r => r.round === round)?.name || 'Grand Prix'

  return (
    <p className="mt-2 text-gray-400">
      {raceName} · {season} Season · Round {round}
    </p>
  )
}
