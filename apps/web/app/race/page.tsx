import { Suspense } from 'react'
import RaceContent from './RaceContent'
import RacePageSkeleton from './RacePageSkeleton'

/**
 * Race Analysis Page — Server Component
 *
 * Renders the header and static shell immediately (SSR),
 * then streams in the interactive client content via Suspense.
 * This ensures the LCP element (<h1>) is server-rendered and
 * paints within the first contentful paint window.
 */
export default function RacePage() {
  return (
    <div className="space-y-6">
      {/* SSR: Header renders immediately — this is the LCP element */}
      <header className="border-l-4 border-f1red pl-4">
        <h1 className="font-heading text-3xl md:text-4xl font-bold uppercase tracking-tight">
          Race Analysis
        </h1>
        <p className="mt-2 text-gray-400">
          Race pace distribution, tyre degradation, and performance analysis
        </p>
      </header>

      {/* Client-side interactive content streams in */}
      <Suspense fallback={<RacePageSkeleton />}>
        <RaceContent />
      </Suspense>
    </div>
  )
}
