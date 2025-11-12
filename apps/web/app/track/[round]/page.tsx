import type { Metadata } from 'next'

type Props = {
  params: { round: string }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return {
    title: `Round ${params.round} Circuit | F1 Engineering`,
    description: 'Circuit information with track layout, sectors, and technical profile',
  }
}

export default function TrackPage({ params }: Props) {
  const { round } = params

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Circuit Information</h1>
          <p className="mt-1 text-gray-400">Round {round}</p>
        </div>
        <div className="flex gap-2">
          <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
            Coming Soon
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-f1gray bg-f1dark/50 p-8">
        <h2 className="mb-4 text-xl font-semibold">Track Features</h2>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Interactive Track Map</h3>
            <p className="text-sm text-gray-400">
              SVG/Canvas visualization with turn numbers, DRS zones, and sector boundaries.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Elevation Profile</h3>
            <p className="text-sm text-gray-400">
              Track elevation changes mapped to distance for gradient analysis.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Corner Analysis</h3>
            <p className="text-sm text-gray-400">
              Detailed corner information including type, gear, typical speed, and difficulty.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Technical Profile</h3>
            <p className="text-sm text-gray-400">
              Circuit characteristics: downforce level, tyre stress, brake severity, overtaking difficulty.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Sector Breakdown</h3>
            <p className="text-sm text-gray-400">
              Sector characteristics and typical time distributions.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Historical Data</h3>
            <p className="text-sm text-gray-400">
              Lap records, pole times, and previous race winner statistics.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-f1red/10 p-4">
          <p className="text-sm text-gray-300">
            <strong className="text-f1red">Note:</strong> This page will feature an interactive
            track map with clickable corners, elevation profile visualization, comprehensive
            technical analysis, and historical data. Circuit data will be loaded from the
            static circuit catalog.
          </p>
        </div>

        <div className="mt-4 rounded-lg border border-f1gray/30 p-4">
          <h4 className="mb-2 font-semibold">Available Routes:</h4>
          <ul className="space-y-1 text-sm text-gray-400">
            <li><code className="rounded bg-f1gray/30 px-2 py-1">/track/1</code> - Round 1 Circuit</li>
            <li><code className="rounded bg-f1gray/30 px-2 py-1">/track/5</code> - Round 5 Circuit</li>
            <li><code className="rounded bg-f1gray/30 px-2 py-1">/track/21</code> - Round 21 Circuit</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
