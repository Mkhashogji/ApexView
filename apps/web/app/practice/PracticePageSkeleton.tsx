/**
 * Loading skeleton for the Practice page content area.
 *
 * CRITICAL: This skeleton must match the exact layout structure of
 * PracticeContent to prevent Cumulative Layout Shift (CLS).
 * Layout: sidebar (lg:w-72) + main content (flex-1)
 */
export default function PracticePageSkeleton() {
  return (
    <div className="flex flex-col lg:flex-row gap-6 animate-pulse">
      {/* Sidebar Skeleton — matches PracticeSidebar dimensions */}
      <aside className="w-full lg:w-72 lg:flex-shrink-0">
        <div className="card-panel space-y-6">
          {/* Session info placeholder */}
          <div>
            <div className="h-3 w-24 bg-f1gray/20 rounded mb-3" />
            <div className="h-6 w-48 bg-f1gray/30 rounded" />
            <div className="h-3 w-56 bg-f1gray/20 rounded mt-2" />
          </div>
          {/* Fuel correction toggle placeholder */}
          <div>
            <div className="h-3 w-32 bg-f1gray/20 rounded mb-3" />
            <div className="h-6 w-48 bg-f1gray/30 rounded" />
          </div>
        </div>
      </aside>

      {/* Main Content Skeleton */}
      <main className="flex-1 min-w-0 space-y-6">
        {/* Session tabs skeleton */}
        <div className="flex gap-2">
          <div className="h-8 w-16 bg-f1gray/30 rounded" />
          <div className="h-8 w-16 bg-f1gray/20 rounded" />
          <div className="h-8 w-16 bg-f1gray/20 rounded" />
        </div>

        {/* Long Run Pace panel skeleton */}
        <div className="card-panel">
          <div className="h-5 w-48 bg-f1gray/30 rounded mb-4" />
          <div className="h-[500px] bg-f1gray/10 rounded-lg" />
        </div>

        {/* Short Run / Best Lap panel skeleton */}
        <div className="card-panel space-y-3">
          <div className="h-5 w-40 bg-f1gray/30 rounded" />
          <div className="h-3 w-64 bg-f1gray/20 rounded" />
          <div className="space-y-2 mt-4">
            {[85, 79, 72, 65, 58, 51].map((w, i) => (
              <div key={i} className="h-8 rounded bg-gray-700/50" style={{ width: `${w}%` }} />
            ))}
          </div>
        </div>

        {/* Circuit Map panel skeleton */}
        <div className="card-panel">
          <div className="h-5 w-32 bg-f1gray/30 rounded mb-3" />
          <div className="h-[300px] bg-f1gray/10 rounded-lg" />
        </div>

        {/* Sector Analysis panel skeleton */}
        <div className="card-panel content-defer space-y-4">
          <div className="h-5 w-36 bg-f1gray/30 rounded" />
          <div className="h-3 w-72 bg-f1gray/20 rounded" />
          <div className="grid grid-cols-3 gap-3 mt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-f1gray/10 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Session Progression panel skeleton */}
        <div className="card-panel content-defer">
          <div className="h-5 w-44 bg-f1gray/30 rounded mb-2" />
          <div className="h-3 w-80 bg-f1gray/20 rounded mb-4" />
          <div className="h-[380px] bg-f1gray/10 rounded-lg" />
        </div>
      </main>
    </div>
  )
}
