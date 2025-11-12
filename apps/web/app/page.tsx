import { SessionSummary } from '@/components/panels/SessionSummary'

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="border-l-4 border-f1red pl-4">
        <h1 className="text-4xl font-bold">Weekend Overview</h1>
        <p className="mt-2 text-gray-400">
          Current season race weekend analysis and insights
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
          <h2 className="text-xl font-semibold">Latest Session</h2>
          <p className="mt-2 text-sm text-gray-400">Loading session data...</p>
        </div>
        
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
          <h2 className="text-xl font-semibold">Quick Stats</h2>
          <p className="mt-2 text-sm text-gray-400">Performance metrics</p>
        </div>
        
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
          <h2 className="text-xl font-semibold">Track Info</h2>
          <p className="mt-2 text-sm text-gray-400">Circuit details</p>
        </div>
      </div>

      <SessionSummary />
    </div>
  )
}

