import type { Metadata } from 'next'
import { Suspense } from 'react'
import { TrackIntelligenceContent } from './TrackIntelligenceContent'

type Props = {
  searchParams: { round?: string; season?: string }
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const round = parseInt(searchParams.round || '24', 10)

  return {
    title: `Round ${round} Track Intelligence | ApexView`,
    description:
      'Comprehensive circuit analysis with technical insights, sector breakdown, ' +
      'and strategic considerations.',
    openGraph: {
      title: `Round ${round} Track Intelligence | ApexView`,
      description:
        'Circuit characteristics, Pirelli tyre data, DRS zones, and strategic ' +
        'insights for every Formula 1 Grand Prix venue.',
      type: 'website',
    },
  }
}

export default function TrackPage({ searchParams }: Props) {
  const round = parseInt(searchParams.round || '24', 10)
  const season = parseInt(searchParams.season || '2025', 10)

  // Validate round number
  if (isNaN(round) || round < 1 || round > 24) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Invalid Round</h1>
          <p className="mt-2 text-gray-400">
            Please select a valid race weekend (Round 1-24).
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Suspense fallback={<TrackIntelligenceFallback />}>
        <TrackIntelligenceContent round={round} season={season} />
      </Suspense>
    </div>
  )
}

// Fallback component for Suspense
function TrackIntelligenceFallback() {
  return (
    <div className="animate-pulse space-y-6">
      {/* Tags skeleton */}
      <div className="flex gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-10 w-32 rounded-full bg-f1gray/30" />
        ))}
      </div>

      {/* Header skeleton */}
      <div className="space-y-4">
        <div className="h-10 w-2/3 rounded bg-f1gray/30" />
        <div className="h-6 w-1/3 rounded bg-f1gray/30" />
        <div className="h-24 w-full rounded-lg bg-f1gray/30" />
      </div>

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-20 rounded-lg bg-f1gray/30" />
        ))}
      </div>

      {/* Two-column skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-64 rounded-lg bg-f1gray/30" />
        <div className="h-64 rounded-lg bg-f1gray/30" />
      </div>
    </div>
  )
}
