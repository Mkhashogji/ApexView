/**
 * Platform Capabilities — 8-item grid showcasing what ApexView can explore.
 *
 * Uses the standard `border-l-4 border-f1red pl-4` section header pattern
 * from the analytical pages. Each item has a red dot bullet and card treatment.
 */

const CAPABILITIES = [
  'Compare qualifying lap deltas with sector-level precision',
  'Analyse race pace distribution across all drivers and compounds',
  'Track tyre degradation rates with fuel-corrected regression',
  'Evaluate pit stop performance with consistency scoring',
  'Study team aerodynamic philosophy via speed decomposition',
  'Assess practice long run pace and short run qualifying simulations',
  'Explore circuit characteristics across all 24 Grand Prix venues',
  'Monitor session progression from FP1 through FP3',
] as const

export default function PlatformCapabilities() {
  return (
    <section>
      {/* Section header — matches analytical page pattern */}
      <div className="border-l-4 border-f1red pl-4">
        <h3 className="font-heading text-xl font-bold uppercase tracking-tight text-white">
          What You Can Explore
        </h3>
      </div>

      {/* 2-column capability grid */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
        {CAPABILITIES.map((capability) => (
          <div
            key={capability}
            className="flex items-start gap-3 rounded-lg border border-f1gray/30 bg-f1gray/10 px-4 py-3"
          >
            {/* Red dot bullet */}
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-f1red" />
            <span className="text-sm leading-relaxed text-gray-300">
              {capability}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}
