import type { Metadata } from 'next'
import { Suspense } from 'react'
import HomePageSkeleton from './HomePageSkeleton'
import HomeContent from './HomeContent'
import raceCalendarData from '@/data/race-calendar-2025.json'

export const metadata: Metadata = {
  title: 'ApexView | Formula 1 Data Analytics',
  description:
    'Explore Formula 1 race strategy, qualifying pace, practice performance, ' +
    'and circuit intelligence across the full 2025 season.',
  openGraph: {
    title: 'ApexView | Formula 1 Data Analytics',
    description:
      'Race strategy, qualifying analysis, practice performance, and circuit ' +
      'intelligence for every round of the 2025 Formula 1 season.',
    type: 'website',
  },
}

/** Season-level statistics derived from the static race calendar JSON. */
export interface SeasonStats {
  season: number
  totalRounds: number
  nextRaceName: string
  nextRaceRound: number | null
}

/**
 * Derives season-level stats from the race calendar at build/SSR time.
 * Finds the next upcoming race by comparing race dates against today's date.
 * If all races have passed, returns "Season Complete" with null round.
 */
function deriveSeasonStats(
  races: typeof raceCalendarData.races
): SeasonStats {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const nextRace = races.find((race) => {
    const raceDate = new Date(race.date)
    raceDate.setHours(0, 0, 0, 0)
    return raceDate >= today
  })

  return {
    season: raceCalendarData.season,
    totalRounds: races.length,
    nextRaceName: nextRace ? nextRace.name : 'Season Complete',
    nextRaceRound: nextRace ? nextRace.round : null,
  }
}

export default function HomePage() {
  const seasonStats = deriveSeasonStats(raceCalendarData.races)

  return (
    <div className="space-y-12 py-8">
      <Suspense fallback={<HomePageSkeleton />}>
        <HomeContent seasonStats={seasonStats} />
      </Suspense>
    </div>
  )
}
