import { Suspense } from 'react'
import { QualifyingContent } from './QualifyingContent'
import { QualifyingPageSkeleton } from '@/components/skeletons/QualifyingPageSkeleton'

/**
 * Qualifying Analysis Page
 * 
 * Server Component wrapper that provides a Suspense boundary for the
 * client-side QualifyingContent component. This is required because
 * QualifyingContent uses useSearchParams() which needs runtime URL access.
 * 
 * The Suspense boundary allows Next.js to:
 * 1. Statically generate the page shell at build time
 * 2. Stream the loading skeleton during initial render
 * 3. Hydrate with actual URL parameters on the client
 */
export default function QualifyingPage() {
  return (
    <Suspense fallback={<QualifyingPageSkeleton />}>
      <QualifyingContent />
    </Suspense>
  )
}
