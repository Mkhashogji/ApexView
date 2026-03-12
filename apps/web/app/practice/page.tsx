import { Suspense } from 'react'
import type { Metadata } from 'next'
import PracticeContent from './PracticeContent'
import PracticePageSkeleton from './PracticePageSkeleton'

export const metadata: Metadata = {
  title: 'Practice Analysis | ApexView',
  description:
    'Practice session analysis with long run pace, tyre insights, ' +
    'and session comparison across the 2025 Formula 1 season.',
  openGraph: {
    title: 'Practice Analysis | ApexView',
    description:
      'Long run pace comparison, sector analysis, and session progression ' +
      'for every practice weekend of the 2025 Formula 1 season.',
    type: 'website',
  },
}

/**
 * Practice Analysis Page — Server Component
 *
 * Renders the header and static shell immediately (SSR),
 * then streams in the interactive client content via Suspense.
 */
export default function PracticePage() {
  return (
    <div className="space-y-6">
      {/* SSR: Header renders immediately — this is the LCP element */}
      <header className="border-l-4 border-f1red pl-4">
        <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
          Practice Analysis
        </h1>
        <p className="mt-2 text-gray-400">
          Long run pace comparison, tyre degradation hints, and session analysis
        </p>
      </header>

      {/* Client-side interactive content streams in */}
      <Suspense fallback={<PracticePageSkeleton />}>
        <PracticeContent />
      </Suspense>
    </div>
  )
}
