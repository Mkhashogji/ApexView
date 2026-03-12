import { Suspense } from 'react'
import type { Metadata } from 'next'
import { QualifyingContent } from './QualifyingContent'
import { QualifyingSubtitle } from './QualifyingSubtitle'
import { QualifyingPageSkeleton } from '@/components/skeletons/QualifyingPageSkeleton'

export const metadata: Metadata = {
  title: 'Qualifying Analysis | ApexView',
  description:
    'Analyse Formula 1 qualifying sector deltas, mini-sector heatmaps, ' +
    'and AI-generated driver technique profiles across the 2025 season.',
  openGraph: {
    title: 'Qualifying Analysis | ApexView',
    description:
      'Sector-level qualifying analysis, lap delta comparisons, and driver ' +
      'technique profiling for every round of the 2025 Formula 1 season.',
    type: 'website',
  },
}

/**
 * Qualifying Analysis Page — Server Component
 *
 * Renders the header and static shell immediately (SSR),
 * then streams in the interactive client content via Suspense.
 * This ensures the LCP element (<h1>) is server-rendered and
 * paints within the first contentful paint window.
 */
export default function QualifyingPage() {
  return (
    <div className="space-y-6">
      {/* SSR: Header renders immediately — this is the LCP element */}
      <header className="border-l-4 border-f1red pl-4">
        <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
          Qualifying Analysis
        </h1>
        <Suspense fallback={
          <div className="mt-2 h-5 w-64 bg-f1gray/20 rounded animate-pulse" />
        }>
          <QualifyingSubtitle />
        </Suspense>
      </header>

      {/* Client-side interactive content streams in */}
      <Suspense fallback={<QualifyingPageSkeleton />}>
        <QualifyingContent />
      </Suspense>
    </div>
  )
}
