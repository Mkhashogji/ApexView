/**
 * Loading skeleton for the Qualifying Analysis page.
 * 
 * This component is displayed during:
 * - Server-side rendering (static generation)
 * - React hydration on the client
 * - Before URL parameters are available
 * 
 * Matches the layout of the actual qualifying page for smooth transitions.
 */
export function QualifyingPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <header className="border-l-4 border-f1gray pl-4">
        <div className="h-10 w-80 bg-f1gray/30 rounded" />
        <div className="mt-2 h-5 w-64 bg-f1gray/20 rounded" />
      </header>

      {/* Session Tabs & Filters Skeleton */}
      <div className="card-panel space-y-4">
        {/* Tabs Row */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Session Tabs */}
          <div className="flex gap-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 w-16 bg-f1gray/30 rounded" />
            ))}
          </div>
          
          {/* Reference Selector */}
          <div className="flex items-center gap-3">
            <div className="h-4 w-16 bg-f1gray/20 rounded" />
            <div className="h-10 w-24 bg-f1gray/30 rounded" />
          </div>
        </div>

        {/* Driver Selection Area */}
        <div className="space-y-3">
          <div className="h-4 w-32 bg-f1gray/20 rounded" />
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 w-20 bg-f1gray/30 rounded-md" />
            ))}
          </div>
          <div className="h-10 w-32 bg-f1gray/30 rounded-md" />
        </div>
      </div>

      {/* 2x2 Grid Skeleton */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Chart Skeletons */}
        {[
          'Speed Trace',
          'Delta to Reference',
          'Sector Breakdown',
          'AI Insights'
        ].map((title, i) => (
          <div key={i} className="card-panel">
            {/* Panel Header */}
            <div className="h-5 w-32 bg-f1gray/30 rounded mb-4" />
            
            {/* Chart Area */}
            <div className="h-80 bg-f1gray/10 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block h-12 w-12 rounded-full bg-f1gray/20 mb-3" />
                <div className="h-4 w-24 mx-auto bg-f1gray/20 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
