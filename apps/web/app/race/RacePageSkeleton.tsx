/**
 * Loading skeleton for the Race page content area.
 *
 * CRITICAL: This skeleton must match the exact layout structure of
 * RaceContent to prevent Cumulative Layout Shift (CLS).
 * Layout: sidebar (lg:w-72) + main content (flex-1)
 */
export default function RacePageSkeleton() {
  return (
    <div className="flex flex-col lg:flex-row gap-6 animate-pulse">
      {/* Sidebar Skeleton — matches RaceSidebar dimensions */}
      <aside className="w-full lg:w-72 lg:flex-shrink-0">
        <div className="card-panel space-y-6">
          {/* Fuel correction toggle */}
          <div>
            <div className="h-3 w-24 bg-f1gray/20 rounded mb-3" />
            <div className="h-6 w-48 bg-f1gray/30 rounded" />
            <div className="h-3 w-56 bg-f1gray/20 rounded mt-2" />
          </div>
        </div>
      </aside>

      {/* Main Content Skeleton — matches box plot panel */}
      <main className="flex-1 min-w-0 space-y-6">
        <div className="card-panel">
          <div className="h-5 w-48 bg-f1gray/30 rounded mb-4" />
          <div className="h-[500px] bg-f1gray/10 rounded-lg" />
        </div>
      </main>
    </div>
  )
}
