'use client'

import { useState } from 'react'
import { DriverPerformanceResult, PerformanceCornerResult } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { formatDelta } from '@/lib/formatters'

interface CornerBreakdownPanelProps {
  /** Performance results from unified Phase 6 endpoint */
  results: DriverPerformanceResult[]
  /** Reference driver for display */
  referenceDriver: string
  /** Whether data is loading */
  isLoading?: boolean
  /** Error message if fetch failed */
  error?: string
}

type SortField = 'corner' | 'delta' | 'cause'
type SortDirection = 'asc' | 'desc'

/**
 * Displays Phase 3 corner-by-corner analysis.
 *
 * Shows:
 * - Time gained/lost at each corner (delta change)
 * - Primary cause (braking, apex, exit, multiple)
 * - Confidence level (high, medium, low)
 * - Summary totals
 *
 * Features:
 * - Color-coded delta values (green = gaining, red = losing)
 * - Confidence badges
 * - Sortable table columns
 * - Driver selector for multi-driver analysis
 */
export function CornerBreakdownPanel({
  results,
  referenceDriver,
  isLoading,
  error,
}: CornerBreakdownPanelProps) {
  const [selectedDriverIndex, setSelectedDriverIndex] = useState(0)
  const [sortField, setSortField] = useState<SortField>('corner')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [showGuide, setShowGuide] = useState(false)

  // Loading state
  if (isLoading) {
    return (
      <div className="card-panel animate-pulse">
        <h3 className="card-panel-header">Corner Analysis</h3>
        <div className="space-y-3">
          <div className="h-4 bg-f1gray/30 rounded w-3/4" />
          <div className="h-4 bg-f1gray/30 rounded w-1/2" />
          <div className="h-4 bg-f1gray/30 rounded w-2/3" />
          <div className="h-4 bg-f1gray/30 rounded w-full" />
          <div className="h-4 bg-f1gray/30 rounded w-5/6" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="card-panel border-red-500/30 bg-red-500/5">
        <h3 className="card-panel-header text-red-400">Corner Analysis</h3>
        <p className="text-sm text-red-400/80">{error}</p>
      </div>
    )
  }

  // Empty state
  if (!results || results.length === 0) {
    return (
      <div className="card-panel">
        <h3 className="card-panel-header">Corner Analysis</h3>
        <p className="text-sm text-gray-500">
          Select drivers to compare corner performance against {referenceDriver}
        </p>
      </div>
    )
  }

  const currentResult = results[selectedDriverIndex]
  if (!currentResult) {
    return null
  }

  const driverInfo = getDriverInfo(currentResult.driver)
  const teamColor = getTeamColor(currentResult.driver)

  // Sort corner results
  const sortedCorners = [...currentResult.corner_results].sort((a, b) => {
    let comparison = 0
    switch (sortField) {
      case 'corner':
        comparison = a.corner_number - b.corner_number
        break
      case 'delta':
        comparison = Math.abs(b.delta_change) - Math.abs(a.delta_change)
        break
      case 'cause':
        comparison = a.cause.localeCompare(b.cause)
        break
    }
    return sortDirection === 'asc' ? comparison : -comparison
  })

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="text-gray-600 ml-1">↕</span>
    }
    return (
      <span className="text-f1red ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
    )
  }

  return (
    <div className="card-panel">
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-panel-header mb-0">Corner Analysis</h3>

        {/* Driver selector for multi-driver results */}
        {results.length > 1 && (
          <select
            value={selectedDriverIndex}
            onChange={(e) => setSelectedDriverIndex(Number(e.target.value))}
            className="bg-f1gray/30 border border-f1gray/50 rounded px-2 py-1 text-sm"
          >
            {results.map((r, i) => (
              <option key={r.driver} value={i}>
                {r.driver}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Driver Summary */}
      <div className="flex items-center gap-4 mb-4 p-3 bg-f1gray/10 rounded-lg">
        <div className="flex items-center gap-2">
          <div
            className="w-1 h-8 rounded"
            style={{ backgroundColor: teamColor }}
          />
          <div>
            <span className="font-medium">{currentResult.driver}</span>
            <span className="text-gray-500 text-xs ml-2">
              {driverInfo?.fullName}
            </span>
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-gray-500">Total:</span>
            <span
              className={`font-mono ml-2 ${
                currentResult.total_corner_delta > 0.005
                  ? 'text-delta-positive'
                  : currentResult.total_corner_delta < -0.005
                    ? 'text-delta-negative'
                    : 'text-gray-400'
              }`}
            >
              {formatDelta(currentResult.total_corner_delta)}
            </span>
          </div>
          <div className="border-l border-f1gray/30 pl-4">
            <span className="text-delta-negative">{currentResult.corners_gaining}</span>
            <span className="text-gray-500 mx-1">/</span>
            <span className="text-delta-positive">{currentResult.corners_losing}</span>
            <span className="text-gray-500 text-xs ml-1">(gaining/losing)</span>
          </div>
        </div>
      </div>

      {/* Corner Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-f1gray/30">
              <th
                className="text-left py-2 px-2 text-gray-400 font-medium cursor-pointer hover:text-white"
                onClick={() => handleSort('corner')}
              >
                Corner <SortIcon field="corner" />
              </th>
              <th className="text-left py-2 px-2 text-gray-400 font-medium hidden sm:table-cell">
                Name
              </th>
              <th
                className="text-right py-2 px-2 text-gray-400 font-medium cursor-pointer hover:text-white"
                onClick={() => handleSort('delta')}
              >
                Δ Time <SortIcon field="delta" />
              </th>
              <th
                className="text-center py-2 px-2 text-gray-400 font-medium cursor-pointer hover:text-white"
                onClick={() => handleSort('cause')}
              >
                Cause <SortIcon field="cause" />
              </th>
              <th className="text-center py-2 px-2 text-gray-400 font-medium">
                Confidence
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedCorners.map((corner) => (
              <CornerRow key={corner.corner_number} corner={corner} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-f1gray/20">
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
          <span>
            <span className="text-delta-negative">Green</span> = {currentResult.driver} gaining time
          </span>
          <span>
            <span className="text-delta-positive">Red</span> = {currentResult.driver} losing time
          </span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 mt-2">
          <span><strong>Cause:</strong> braking, apex, exit, or multiple phases</span>
        </div>
      </div>

      {/* How to read this panel */}
      <button
        onClick={() => setShowGuide(!showGuide)}
        className="flex items-center gap-2 mt-4 text-sm text-gray-500 hover:text-gray-300 transition-colors"
        type="button"
        aria-expanded={showGuide}
      >
        <span
          className={`inline-block transition-transform duration-200 ${showGuide ? 'rotate-90' : ''}`}
        >
          &#9656;
        </span>
        How to read this panel
      </button>
      {showGuide && (
        <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] p-4 space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Understanding the Table</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                <span className="text-gray-400 font-medium">Corner (T1, T2...):</span> Each numbered turn on the circuit, with the analysis zone extending from brake point through apex to exit.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Δ Time:</span> Time gained (green/negative) or lost (red/positive) by the comparison driver at this corner.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Cause:</span> The primary driving phase where the difference originated. Braking = corner entry deceleration. Apex = mid-corner minimum speed. Exit = corner exit acceleration. Multiple = a secondary phase contributed more than 30% of the primary phase&apos;s time difference, meaning the gap cannot be attributed to one phase alone.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Confidence:</span> How closely the two brake detection methods agreed at this corner. High = the brake signal and deceleration refinement aligned within 20 metres. Medium = aligned within 40 metres. Low = diverged beyond 40 metres, meaning zone boundaries are approximate.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">How Corner Zones Are Detected</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                Brake points are identified using a two-stage physics-based approach. First, the system finds where the brake signal clearly activates (&gt;50%). Then it refines backward using deceleration calculated from speed changes (v&#178; kinematics), searching for where heavy deceleration first begins — typically where deceleration crosses a circuit-specific threshold (around -5 m/s&#178;, tuned per circuit from -4.0 to -6.5 m/s&#178;). This captures the true onset of braking rather than relying solely on brake pedal pressure.
              </p>
              <p>
                The apex is detected as the point of minimum speed within the corner zone. The exit is identified when the driver either sustains positive acceleration (3+ consecutive data points above 2.0 m/s&#178;) or recovers to 85% of their pre-braking speed.
              </p>
              <p>
                The &quot;multiple&quot; cause is assigned when the second-most-significant phase exceeds 30% of the primary phase&apos;s magnitude. For example, a corner where 65% of the time difference came from braking and 35% from apex would be labelled &quot;multiple&quot;, since the apex contribution is substantial relative to braking.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Limitations</h4>
            <div className="text-sm text-gray-500/80 italic space-y-1.5">
              <p>
                Corner analysis quality varies by circuit. Circuits with distinct, separated braking zones produce clearer results than circuits with high-speed flowing corners where zones overlap.
              </p>
              <p>
                The analysis uses publicly available speed and brake data to infer deceleration. Team-internal systems have access to higher-resolution brake pressure, individual brake temperatures, and damper data that enable more precise zone detection. Subtle technique differences (trail braking depth, brake bias adjustments) may not be fully captured from public telemetry.
              </p>
              <p>
                Confidence is relative to this session only. A &quot;high&quot; confidence rating means the brake signal and deceleration data aligned closely at that corner — it does not guarantee the attribution is absolutely correct.
              </p>
              <p>
                When this panel shows no data, it indicates the telemetry quality was insufficient for reliable corner-level analysis.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Individual corner row component
 */
function CornerRow({ corner }: { corner: PerformanceCornerResult }) {
  const isGaining = corner.delta_change < -0.005
  const isLosing = corner.delta_change > 0.005
  const isNeutral = !isGaining && !isLosing

  // Delta color
  const deltaColor = isGaining
    ? 'text-delta-negative'
    : isLosing
      ? 'text-delta-positive'
      : 'text-gray-400'

  // Confidence badge colors
  const confidenceBadge = {
    high: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-red-500/20 text-red-400 border-red-500/30',
  }[corner.confidence]

  // Cause badge styling
  const causeBadge = {
    braking: 'bg-orange-500/20 text-orange-400',
    apex: 'bg-blue-500/20 text-blue-400',
    exit: 'bg-purple-500/20 text-purple-400',
    multiple: 'bg-pink-500/20 text-pink-400',
    unknown: 'bg-gray-500/20 text-gray-400',
  }[corner.cause]

  // Row highlight based on delta magnitude
  const rowHighlight = isGaining
    ? 'bg-green-500/5'
    : isLosing
      ? 'bg-red-500/5'
      : ''

  return (
    <tr className={`border-b border-f1gray/10 hover:bg-f1gray/10 ${rowHighlight}`}>
      {/* Corner Number */}
      <td className="py-2 px-2">
        <span className="font-medium">T{corner.corner_number}</span>
      </td>

      {/* Corner Name */}
      <td className="py-2 px-2 text-gray-400 hidden sm:table-cell">
        {corner.name || '-'}
      </td>

      {/* Delta Change */}
      <td className={`py-2 px-2 text-right font-mono ${deltaColor}`}>
        {formatDelta(corner.delta_change)}
      </td>

      {/* Cause */}
      <td className="py-2 px-2 text-center">
        <span className={`px-2 py-0.5 rounded text-xs ${causeBadge}`}>
          {corner.cause}
        </span>
      </td>

      {/* Confidence */}
      <td className="py-2 px-2 text-center">
        <span
          className={`px-2 py-0.5 rounded border text-xs ${confidenceBadge}`}
        >
          {corner.confidence}
        </span>
      </td>
    </tr>
  )
}
