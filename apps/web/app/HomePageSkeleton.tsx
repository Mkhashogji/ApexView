export default function HomePageSkeleton() {
  return (
    <div className="space-y-12 animate-pulse">
      {/* Hero skeleton */}
      <div className="space-y-4 py-16">
        <div className="h-16 bg-f1gray/30 rounded-lg w-2/3" />
        <div className="h-8 bg-f1gray/20 rounded-lg w-1/2" />
        <div className="flex gap-8 pt-4">
          <div className="h-12 bg-f1gray/20 rounded-lg w-32" />
          <div className="h-12 bg-f1gray/20 rounded-lg w-32" />
          <div className="h-12 bg-f1gray/20 rounded-lg w-32" />
        </div>
      </div>

      {/* Feature cards skeleton (2×2 grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card-panel space-y-3">
            <div className="h-6 bg-f1gray/30 rounded w-1/3" />
            <div className="h-4 bg-f1gray/20 rounded w-full" />
            <div className="h-4 bg-f1gray/20 rounded w-4/5" />
            <div className="h-4 bg-f1gray/20 rounded w-1/4 mt-4" />
          </div>
        ))}
      </div>

      {/* Platform capabilities skeleton */}
      <div className="space-y-4">
        <div className="h-6 bg-f1gray/30 rounded w-1/4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-4 bg-f1gray/20 rounded w-full" />
          ))}
        </div>
      </div>
    </div>
  )
}
