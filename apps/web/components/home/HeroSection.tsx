import Link from 'next/link'
import type { SeasonStats } from '@/app/page'
import SeasonStatsDisplay from './SeasonStats'

interface HeroSectionProps {
  seasonStats: SeasonStats
}

export default function HeroSection({ seasonStats }: HeroSectionProps) {
  return (
    <section className="relative rounded-lg">
      {/* Dark gradient backdrop */}
      <div className="absolute inset-0 bg-gradient-to-br from-f1dark/90 via-f1dark/80 to-f1dark/95" />

      {/* Content */}
      <div className="relative z-10 px-6 py-16 sm:px-10 sm:py-20">
        {/* Headline — Montserrat weight-800 */}
        <h1 className="font-heading text-5xl sm:text-6xl md:text-7xl font-extrabold uppercase tracking-tight">
          Apex<span className="text-f1red">View</span>
        </h1>

        {/* Purpose line — f1red accent */}
        <p className="mt-4 text-lg sm:text-xl text-f1red font-medium tracking-wide">
          Where Formula 1 Data Becomes Insight
        </p>

        {/* Season stats counters */}
        <div className="mt-8">
          <SeasonStatsDisplay seasonStats={seasonStats} />
        </div>

        {/* CTA button */}
        <div className="mt-10">
          <Link
            href="/race"
            className="inline-flex items-center gap-2 rounded-lg border border-f1red bg-f1red/10 px-6 py-3 font-heading text-sm font-semibold uppercase tracking-wider text-white transition-all duration-200 hover:bg-f1red/20 hover:shadow-glow-red-sm focus-ring"
          >
            Explore Race Data
            <span className="text-f1red" aria-hidden="true">&rarr;</span>
          </Link>
        </div>
      </div>
    </section>
  )
}
