/**
 * Loading skeleton for the Qualifying page content area.
 *
 * CRITICAL: This skeleton must match the exact layout structure of
 * QualifyingContent to prevent Cumulative Layout Shift (CLS).
 * Layout: sidebar (lg:w-72) + main content (flex-1)
 */
export function QualifyingPageSkeleton() {
  return (
    <div className="flex flex-col lg:flex-row gap-6 animate-pulse">
      {/* Sidebar Skeleton — matches QualifyingSidebar dimensions */}
      <aside className="w-full lg:w-72 lg:flex-shrink-0">
        <div className="card-panel space-y-6">
          {/* Session tabs */}
          <div>
            <div className="h-3 w-16 bg-f1gray/20 rounded mb-3" />
            <div className="flex gap-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-10 w-16 bg-f1gray/30 rounded" />
              ))}
            </div>
          </div>
          {/* Reference driver */}
          <div>
            <div className="h-3 w-28 bg-f1gray/20 rounded mb-3" />
            <div className="h-10 w-full bg-f1gray/30 rounded" />
          </div>
          <hr className="border-f1gray/30" />
          {/* Driver selection */}
          <div>
            <div className="h-3 w-20 bg-f1gray/20 rounded mb-3" />
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-8 w-20 bg-f1gray/30 rounded-md" />
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Skeleton — matches content area dimensions */}
      <main className="flex-1 min-w-0 space-y-6">
        {/* Telemetry + Sectors row */}
        <div className="flex flex-col xl:flex-row gap-6">
          <div className="flex-1 card-panel min-w-0">
            <div className="h-5 w-32 bg-f1gray/30 rounded mb-4" />
            <div className="h-96 bg-f1gray/10 rounded-lg" />
          </div>
          <div className="xl:w-80 xl:flex-shrink-0 card-panel">
            <div className="h-5 w-36 bg-f1gray/30 rounded mb-4" />
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-8 bg-f1gray/10 rounded" />
              ))}
            </div>
          </div>
        </div>

        {/* Delta plot */}
        <div className="card-panel">
          <div className="h-5 w-48 bg-f1gray/30 rounded mb-4" />
          <div className="h-96 bg-f1gray/10 rounded-lg" />
        </div>

        {/* Scaling metadata */}
        <div className="card-panel">
          <div className="h-5 w-40 bg-f1gray/30 rounded mb-4" />
          <div className="h-24 bg-f1gray/10 rounded-lg" />
        </div>

        {/* Corner analysis */}
        <div className="card-panel">
          <div className="h-5 w-32 bg-f1gray/30 rounded mb-4" />
          <div className="h-48 bg-f1gray/10 rounded-lg" />
        </div>
      </main>
    </div>
  )
}
