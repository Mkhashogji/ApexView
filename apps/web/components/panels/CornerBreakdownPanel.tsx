'use client'

import { useState } from 'react'
import { CornerAnalysisDriverResult, CornerResult } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { formatDelta } from '@/lib/formatters'

interface CornerBreakdownPanelProps {
  /** Corner analysis results from Phase 3 */
  results: CornerAnalysisDriverResult[]
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

  const driverInfo = getDriverInfo(currentResult.compareDriver)
  const teamColor = getTeamColor(currentResult.compareDriver)

  // Sort corner results
  const sortedCorners = [...currentResult.cornerResults].sort((a, b) => {
    let comparison = 0
    switch (sortField) {
      case 'corner':
        comparison = a.cornerNumber - b.cornerNumber
        break
      case 'delta':
        comparison = Math.abs(b.deltaChange) - Math.abs(a.deltaChange)
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
              <option key={r.compareDriver} value={i}>
                {r.compareDriver}
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
            <span className="font-medium">{currentResult.compareDriver}</span>
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
                currentResult.totalDeltaChange > 0.005
                  ? 'text-delta-positive'
                  : currentResult.totalDeltaChange < -0.005
                    ? 'text-delta-negative'
                    : 'text-gray-400'
              }`}
            >
              {formatDelta(currentResult.totalDeltaChange)}
            </span>
          </div>
          <div className="border-l border-f1gray/30 pl-4">
            <span className="text-delta-negative">{currentResult.cornersGaining}</span>
            <span className="text-gray-500 mx-1">/</span>
            <span className="text-delta-positive">{currentResult.cornersLosing}</span>
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
              <CornerRow key={corner.cornerNumber} corner={corner} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-f1gray/20">
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
          <span>
            <span className="text-delta-negative">Green</span> = {currentResult.compareDriver} gaining time
          </span>
          <span>
            <span className="text-delta-positive">Red</span> = {currentResult.compareDriver} losing time
          </span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 mt-2">
          <span><strong>Cause:</strong> braking, apex, exit, or multiple phases</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Individual corner row component
 */
function CornerRow({ corner }: { corner: CornerResult }) {
  const isGaining = corner.deltaChange < -0.005
  const isLosing = corner.deltaChange > 0.005
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
        <span className="font-medium">T{corner.cornerNumber}</span>
      </td>

      {/* Corner Name */}
      <td className="py-2 px-2 text-gray-400 hidden sm:table-cell">
        {corner.name || '-'}
      </td>

      {/* Delta Change */}
      <td className={`py-2 px-2 text-right font-mono ${deltaColor}`}>
        {formatDelta(corner.deltaChange)}
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
