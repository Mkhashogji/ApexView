'use client'

import type { SeasonStats } from '@/app/page'
import HeroSection from '@/components/home/HeroSection'
import FeatureCard from '@/components/home/FeatureCard'
import PlatformCapabilities from '@/components/home/PlatformCapabilities'

/** Feature card data — one per analytical page. */
const FEATURE_CARDS = [
  {
    href: '/qualifying',
    title: 'Qualifying',
    question: 'Who was genuinely fastest over a single lap, and why?',
    capabilities: ['Lap Deltas', 'Sector Breakdown', 'AI Technique Profiles'],
  },
  {
    href: '/race',
    title: 'Race',
    question: 'How did strategy, tyre degradation, and pit stops shape the result?',
    capabilities: ['Pace Distribution', 'Tyre Degradation', 'Pit Stop Analysis'],
  },
  {
    href: '/practice',
    title: 'Practice',
    question: 'What do long run stints and short run pace reveal about race day form?',
    capabilities: ['Long Run Pace', 'Sector Analysis', 'Session Progression'],
  },
  {
    href: '/track',
    title: 'Track Intelligence',
    question: 'What defines each circuit and how does it influence strategy?',
    capabilities: ['Circuit Data', 'Tyre Characteristics', 'Strategic Insights'],
  },
] as const

interface HomeContentProps {
  seasonStats: SeasonStats
}

export default function HomeContent({ seasonStats }: HomeContentProps) {
  return (
    <div className="space-y-16">
      {/* Section 1: Hero — animates first, no delay */}
      <div className="animate-fade-slide-in">
        <HeroSection seasonStats={seasonStats} />
      </div>

      {/* Section 2: Feature cards — 150ms delay */}
      <div className="animate-fade-slide-in-delay-1">
        <section>
          <h2 className="sr-only">Analytical Pages</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {FEATURE_CARDS.map((card) => (
              <FeatureCard
                key={card.href}
                href={card.href}
                title={card.title}
                question={card.question}
                capabilities={card.capabilities as unknown as string[]}
              />
            ))}
          </div>
        </section>
      </div>

      {/* Section 3: Platform capabilities — 300ms delay */}
      <div className="animate-fade-slide-in-delay-2">
        <PlatformCapabilities />
      </div>
    </div>
  )
}
