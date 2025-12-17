'use client'

import { QualifyingSessionTabs } from '@/components/filters/QualifyingSessionTabs'
import { DriverMultiSelect } from '@/components/filters/DriverMultiSelect'
import { QualifyingSessionPart } from '@/../../packages/models/src/types'
import { getDriverInfo } from '@/lib/drivers'

interface QualifyingSidebarProps {
  /** Currently selected session part (Q1/Q2/Q3 or SQ1/SQ2/SQ3) */
  sessionPart: QualifyingSessionPart
  /** Callback when session part changes */
  onSessionChange: (session: QualifyingSessionPart) => void
  /** Whether this is a sprint weekend (shows SQ tabs instead of Q) */
  isSprintWeekend: boolean
  /** Currently selected reference driver */
  referenceDriver: string
  /** Callback when reference driver changes */
  onReferenceChange: (driver: string) => void
  /** Currently selected drivers for comparison */
  selectedDrivers: string[]
  /** Callback when driver selection changes */
  onDriversChange: (drivers: string[]) => void
  /** Maximum number of drivers that can be selected */
  maxDrivers?: number
}

/**
 * Left sidebar for the Qualifying page containing:
 * - Session tabs (Q1/Q2/Q3)
 * - Reference driver selector
 * - Driver multi-select
 */
export function QualifyingSidebar({
  sessionPart,
  onSessionChange,
  isSprintWeekend,
  referenceDriver,
  onReferenceChange,
  selectedDrivers,
  onDriversChange,
  maxDrivers = 6,
}: QualifyingSidebarProps) {
  return (
    <aside className="w-full lg:w-72 lg:flex-shrink-0 lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
      <div className="card-panel space-y-6">
        {/* Session Part Tabs */}
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-3">
            Session
          </h3>
          <QualifyingSessionTabs
            selected={sessionPart}
            onChange={onSessionChange}
            isSprintWeekend={isSprintWeekend}
          />
        </div>

        {/* Reference Driver Selector */}
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-3">
            Reference Driver
          </h3>
          <select
            value={referenceDriver}
            onChange={(e) => onReferenceChange(e.target.value)}
            className="w-full rounded-md bg-f1gray/50 px-3 py-2.5 text-sm font-medium focus-ring border border-f1gray/30"
            aria-label="Select reference driver"
          >
            {selectedDrivers.length > 0 ? (
              selectedDrivers.map((driver) => {
                const info = getDriverInfo(driver)
                return (
                  <option key={driver} value={driver}>
                    {driver} - {info?.fullName || driver}
                  </option>
                )
              })
            ) : (
              <option value="" disabled>No drivers selected</option>
            )}
          </select>
          <p className="mt-2 text-xs text-gray-500">
            Delta times are calculated against this driver
          </p>
        </div>

        {/* Divider */}
        <hr className="border-f1gray/30" />

        {/* Driver Selection */}
        <div>
          <DriverMultiSelect
            selected={selectedDrivers}
            onChange={onDriversChange}
            maxDrivers={maxDrivers}
          />
        </div>
      </div>
    </aside>
  )
}
