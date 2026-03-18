'use client'

import { DriverPerformanceResult } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { useState } from 'react'
import { formatDelta } from '@/lib/formatters'

interface ScalingMetadataPanelProps {
  /** Performance results from unified Phase 6 endpoint */
  results: DriverPerformanceResult[]
  /** Reference driver for display */
  referenceDriver: string
  /** Whether data is loading */
  isLoading?: boolean
  /** Error message if fetch failed */
  error?: string
}

/**
 * Displays Phase 2 scaling metadata for delta calculations.
 *
 * Shows:
 * - Official gap (ground truth from FIA timing)
 * - Telemetry gap (calculated from speed traces)
 * - Scaling factor (correction applied)
 * - Confidence score (data quality indicator)
 *
 * This provides transparency about how delta values are calculated
 * and allows users to understand the accuracy of the analysis.
 */
export function ScalingMetadataPanel({
  results,
  referenceDriver,
  isLoading,
  error,
}: ScalingMetadataPanelProps) {
  const [showGuide, setShowGuide] = useState(false)

  // Loading state
  if (isLoading) {
    return (
      <div className="card-panel animate-pulse">
        <h3 className="card-panel-header">Scaled Delta Analysis</h3>
        <div className="space-y-3">
          <div className="h-4 bg-f1gray/30 rounded w-3/4" />
          <div className="h-4 bg-f1gray/30 rounded w-1/2" />
          <div className="h-4 bg-f1gray/30 rounded w-2/3" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="card-panel border-red-500/30 bg-red-500/5">
        <h3 className="card-panel-header text-red-400">Scaled Delta Analysis</h3>
        <p className="text-sm text-red-400/80">{error}</p>
      </div>
    )
  }

  // Empty state
  if (!results || results.length === 0) {
    return (
      <div className="card-panel">
        <h3 className="card-panel-header">Scaled Delta Analysis</h3>
        <p className="text-sm text-gray-500">
          Select drivers to compare against {referenceDriver}
        </p>
      </div>
    )
  }

  return (
    <div className="card-panel">
      <h3 className="card-panel-header">Scaled Delta Analysis</h3>

      {/* Explanation */}
      <p className="text-xs text-gray-500 mb-4">
        Delta values are scaled to match official F1 timing while preserving where on track time is
        gained or lost.
      </p>

      {/* Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-f1gray/30">
              <th className="text-left py-2 px-2 text-gray-400 font-medium">Driver</th>
              <th className="text-right py-2 px-2 text-gray-400 font-medium">Official</th>
              <th className="text-right py-2 px-2 text-gray-400 font-medium">Telemetry</th>
              <th className="text-right py-2 px-2 text-gray-400 font-medium">Scale</th>
              <th className="text-right py-2 px-2 text-gray-400 font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => {
              const driverInfo = getDriverInfo(result.driver)
              const teamColor = getTeamColor(result.driver)
              const confidence = result.scaling_confidence ?? 0
              const confidencePercent = Math.round(confidence * 100)

              // Determine confidence color
              const confidenceColor =
                confidence >= 0.8
                  ? 'text-green-400'
                  : confidence >= 0.6
                    ? 'text-yellow-400'
                    : 'text-red-400'

              // Determine confidence bar color
              const confidenceBarColor =
                confidence >= 0.8
                  ? 'bg-green-500'
                  : confidence >= 0.6
                    ? 'bg-yellow-500'
                    : 'bg-red-500'

              return (
                <tr
                  key={result.driver}
                  className="border-b border-f1gray/10 hover:bg-f1gray/5"
                >
                  {/* Driver */}
                  <td className="py-2 px-2">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-1 h-4 rounded"
                        style={{ backgroundColor: teamColor }}
                      />
                      <span className="font-medium">{result.driver}</span>
                      <span className="text-gray-500 text-xs hidden sm:inline">
                        {driverInfo?.fullName}
                      </span>
                    </div>
                  </td>

                  {/* Official Gap */}
                  <td className="py-2 px-2 text-right font-mono">
                    <span
                      className={result.official_gap > 0 ? 'text-delta-positive' : 'text-delta-negative'}
                    >
                      {formatDelta(result.official_gap)}
                    </span>
                  </td>

                  {/* Telemetry Gap */}
                  <td className="py-2 px-2 text-right font-mono text-gray-400">
                    {formatDelta(result.telemetry_gap ?? 0)}
                  </td>

                  {/* Scaling Factor */}
                  <td className="py-2 px-2 text-right font-mono text-gray-300">
                    {(result.scaling_factor ?? 0).toFixed(3)}x
                  </td>

                  {/* Confidence */}
                  <td className="py-2 px-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {/* Confidence bar */}
                      <div className="w-12 h-1.5 bg-f1gray/30 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${confidenceBarColor}`}
                          style={{ width: `${confidencePercent}%` }}
                        />
                      </div>
                      <span className={`font-mono text-xs ${confidenceColor}`}>
                        {confidencePercent}%
                      </span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-f1gray/20">
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
          <span>
            <strong>Official:</strong> FIA timing (ground truth)
          </span>
          <span>
            <strong>Telemetry:</strong> Calculated from speed data
          </span>
          <span>
            <strong>Scale:</strong> Correction multiplier applied
          </span>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Confidence is based on how close the scaling factor is to 1.0. Values close to 1.0
          indicate telemetry closely matches official timing.
        </p>
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
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Understanding the Columns</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                <span className="text-gray-400 font-medium">Official gap:</span> The FIA-published time difference. This is ground truth — all analysis is anchored to this value.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Telemetry gap:</span> Time difference calculated from speed trace integration. Often differs slightly from official timing due to telemetry sampling resolution and distance normalisation.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Scale factor:</span> The multiplier applied to align telemetry deltas with official timing. 1.000x = perfect agreement. Values between 0.95x–1.05x indicate good data quality.
              </p>
              <p>
                <span className="text-gray-400 font-medium">Confidence:</span> How close the scale factor is to 1.0, expressed as a percentage. Green (80%+) = reliable. Yellow (60-79%) = treat with some caution. Red (&lt;60%) = significant data quality limitations.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">What This Tells You</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                A confidence score close to 100% means the telemetry data closely matches what the official timing system recorded. A lower score means the publicly available telemetry has gaps or inconsistencies with official timing at this circuit.
              </p>
              <p>
                The delta curve in the chart above uses this scaling — its shape comes from telemetry, but its magnitude is corrected to match the official gap. Higher confidence means the shape is more trustworthy.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Limitations</h4>
            <p className="text-gray-500/80 italic text-sm">
              Telemetry data is sourced from publicly broadcast car data, not team-internal high-resolution sensors. Teams have access to additional channels (ride height, aero load, individual brake temperatures, energy deployment) that are not publicly available. The scale factor quantifies how well the available public data represents the actual on-track performance.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
