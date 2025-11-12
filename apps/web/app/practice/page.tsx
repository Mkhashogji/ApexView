import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Practice Analysis | F1 Engineering',
  description: 'Practice session analysis with telemetry consistency and setup insights',
}

export default function PracticePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Practice Analysis</h1>
        <div className="flex gap-2">
          <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
            Coming Soon
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-f1gray bg-f1dark/50 p-8">
        <h2 className="mb-4 text-xl font-semibold">Practice Session Features</h2>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Telemetry Consistency</h3>
            <p className="text-sm text-gray-400">
              Analyze lap-to-lap consistency and identify setup changes across practice sessions.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Long Run Analysis</h3>
            <p className="text-sm text-gray-400">
              Track tyre degradation and race pace simulation data from long runs.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Setup Evolution</h3>
            <p className="text-sm text-gray-400">
              Compare telemetry across FP1, FP2, FP3 to see setup progression.
            </p>
          </div>

          <div className="rounded-lg border border-f1gray/30 p-4">
            <h3 className="mb-2 font-semibold text-f1red">Fuel-Corrected Pace</h3>
            <p className="text-sm text-gray-400">
              Adjust lap times for estimated fuel load to understand true pace.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-f1red/10 p-4">
          <p className="text-sm text-gray-300">
            <strong className="text-f1red">Note:</strong> This page will include comprehensive practice
            session analysis with consistency metrics, long run pace analysis, and setup comparison tools.
            The features will reuse components from the qualifying page with practice-specific insights.
          </p>
        </div>
      </div>
    </div>
  )
}
