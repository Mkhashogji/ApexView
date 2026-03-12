import type { SeasonStats } from '@/app/page'

interface SeasonStatsDisplayProps {
  seasonStats: SeasonStats
}

/**
 * Three stat counters showing season number, total rounds, and next race.
 * Uses JetBrains Mono for values (tabular-nums), Inter for labels.
 * Vertical dividers separate each stat group.
 */
export default function SeasonStatsDisplay({ seasonStats }: SeasonStatsDisplayProps) {
  const isSeasonComplete = seasonStats.nextRaceRound === null

  return (
    <div className="flex items-center gap-6 sm:gap-8">
      {/* Season */}
      <div className="flex flex-col">
        <span className="font-mono text-2xl sm:text-3xl font-medium tabular-nums text-white">
          {seasonStats.season}
        </span>
        <span className="mt-1 text-xs uppercase tracking-wider text-gray-400">
          Season
        </span>
      </div>

      {/* Divider */}
      <div className="w-px h-12 bg-f1gray/50" />

      {/* Rounds */}
      <div className="flex flex-col">
        <span className="font-mono text-2xl sm:text-3xl font-medium tabular-nums text-white">
          {seasonStats.totalRounds}
        </span>
        <span className="mt-1 text-xs uppercase tracking-wider text-gray-400">
          Rounds
        </span>
      </div>

      {/* Divider */}
      <div className="w-px h-12 bg-f1gray/50" />

      {/* Next Race or Season Complete */}
      <div className="flex flex-col">
        <span className="font-mono text-base sm:text-lg font-medium text-white leading-tight">
          {seasonStats.nextRaceName}
        </span>
        <span className="mt-1 text-xs uppercase tracking-wider text-gray-400">
          {isSeasonComplete ? 'Status' : 'Next Race'}
        </span>
      </div>
    </div>
  )
}
