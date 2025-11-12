import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Race Analysis | F1 Engineering',
  description: 'Race strategy analysis with stint management and tyre degradation',
}

export default function RacePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Race Analysis</h1>
        <div className="flex gap-2">
          <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
            Coming Soon
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-f1gray bg-f1dark/50 p-8">
        <h2 className="mb-4 text-xl font-semibold">Race Features</h2>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Stint Management</h3>
            <p className="text-sm text-gray-400">
              Visualize pit stop strategy and stint lengths with compound selection.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Tyre Degradation</h3>
            <p className="text-sm text-gray-400">
              Track pace loss over stint age with degradation rate calculations.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Position Changes</h3>
            <p className="text-sm text-gray-400">
              Timeline of overtakes, pit stops, and position evolution throughout the race.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Strategy Analysis</h3>
            <p className="text-sm text-gray-400">
              Compare different strategies and identify optimal pit windows.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Pace Evolution</h3>
            <p className="text-sm text-gray-400">
              Track pace changes across the race with fuel effect compensation.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Safety Car Impact</h3>
            <p className="text-sm text-gray-400">
              Analyze strategy opportunities during safety car and VSC periods.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-f1red/10 p-4">
          <p className="text-sm text-gray-300">
            <strong className="text-f1red">Note:</strong> This page will provide comprehensive race
            analysis including stint-by-stint pace, tyre degradation modeling, position tracking,
            and strategic decision analysis. Interactive charts will show pace evolution and
            strategy comparison tools.
          </p>
        </div>
      </div>
    </div>
  )
}
