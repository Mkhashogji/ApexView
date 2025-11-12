'use client'

export function SessionSummary() {
  return (
    <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
      <h2 className="mb-4 text-2xl font-semibold">Session Summary</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded border border-f1gray/50 p-4">
          <p className="text-sm text-gray-400">Fastest Lap</p>
          <p className="mt-1 text-xl font-bold">1:32.837</p>
          <p className="text-sm text-gray-500">VER</p>
        </div>
        <div className="rounded border border-f1gray/50 p-4">
          <p className="text-sm text-gray-400">Top Speed</p>
          <p className="mt-1 text-xl font-bold">342 km/h</p>
          <p className="text-sm text-gray-500">SAI</p>
        </div>
        <div className="rounded border border-f1gray/50 p-4">
          <p className="text-sm text-gray-400">Total Laps</p>
          <p className="mt-1 text-xl font-bold">412</p>
          <p className="text-sm text-gray-500">All drivers</p>
        </div>
        <div className="rounded border border-f1gray/50 p-4">
          <p className="text-sm text-gray-400">Session Time</p>
          <p className="mt-1 text-xl font-bold">60:00</p>
          <p className="text-sm text-gray-500">Duration</p>
        </div>
      </div>
    </div>
  )
}

