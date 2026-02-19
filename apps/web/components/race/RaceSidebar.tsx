'use client'

interface RaceSidebarProps {
  fuelCorrected: boolean
  onFuelCorrectedChange: (value: boolean) => void
}

/**
 * Left sidebar for the Race page.
 * Contains fuel correction toggle. GP selection is handled
 * by RaceWeekendSelector in the global navigation bar.
 */
export function RaceSidebar({
  fuelCorrected,
  onFuelCorrectedChange,
}: RaceSidebarProps) {
  return (
    <aside className="w-full lg:w-72 lg:flex-shrink-0 lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
      <div className="card-panel space-y-6">
        {/* Fuel Correction Toggle */}
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-3">
            Pace Correction
          </h3>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={fuelCorrected}
              onChange={(e) => onFuelCorrectedChange(e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-f1red
                         focus:ring-f1red focus:ring-offset-0"
            />
            <span className="text-sm text-gray-300">
              Fuel-corrected lap times
            </span>
          </label>
          <p className="text-xs text-gray-500 mt-2">
            {fuelCorrected
              ? 'Showing pace normalised to empty tank equivalent'
              : 'Showing raw lap times as recorded on track'}
          </p>
        </div>
      </div>
    </aside>
  )
}
