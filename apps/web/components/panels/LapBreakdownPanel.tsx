'use client'

import { useState } from 'react'
import { LapBreakdown, StraightSegment } from '@/../../packages/models/src/types'
import { formatDelta, getDeltaColorClass } from '@/lib/formatters'

interface LapBreakdownPanelProps {
  /** Lap breakdown data showing corners + straights = official gap */
  breakdown: LapBreakdown
  /** Comparison driver code for display */
  compDriver: string
  /** Optional additional CSS classes */
  className?: string
}

/**
 * Displays the 5th Dimension: Lap Breakdown
 *
 * Shows how corner deltas + straight deltas = official gap,
 * providing mathematical closure and answering "where did the time go?"
 *
 * Features:
 * - Visual corners + straights = official equation
 * - Track coverage percentage bar
 * - Reconciliation status (checkmark if within 5ms tolerance)
 * - Educational insight text
 */
export function LapBreakdownPanel({
  breakdown,
  compDriver,
  className = ''
}: LapBreakdownPanelProps) {
  const [showGuide, setShowGuide] = useState(false)

  const {
    corner_total,
    straight_total,
    official_gap,
    track_coverage,
    reconciliation_valid,
    reconciliation_error,
    insight_text,
    straight_segments
  } = breakdown

  // Helper for delta color classes
  const getDeltaClass = (value: number) => {
    if (value > 0.005) return 'text-delta-positive'  // losing time (red)
    if (value < -0.005) return 'text-delta-negative' // gaining time (green)
    return 'text-gray-400'
  }

  return (
    <div className={`card-panel ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-panel-header mb-0">Lap Time Breakdown</h3>
        <span className="text-xs text-gray-500">{compDriver} vs Reference</span>
      </div>

      {/* Three-column breakdown: Corners + Straights = Official */}
      <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr] gap-2 items-center mb-6">
        {/* Corners */}
        <div className="text-center p-4 rounded-lg bg-f1gray/20 border border-f1gray/30">
          <div className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
            Corners
          </div>
          <div className={`text-2xl font-bold font-mono ${getDeltaClass(corner_total)}`}>
            {formatDelta(corner_total)}
          </div>
        </div>

        {/* Plus sign */}
        <div className="text-gray-500 text-2xl font-light">+</div>

        {/* Straights */}
        <div className="text-center p-4 rounded-lg bg-f1gray/20 border border-f1gray/30">
          <div className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
            Straights
          </div>
          <div className={`text-2xl font-bold font-mono ${getDeltaClass(straight_total)}`}>
            {formatDelta(straight_total)}
          </div>
        </div>

        {/* Equals sign */}
        <div className="text-gray-500 text-2xl font-light">=</div>

        {/* Official Gap */}
        <div className="text-center p-4 rounded-lg bg-f1gray/30 border border-f1gray/50">
          <div className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
            Official Gap
          </div>
          <div className="flex items-center justify-center gap-2">
            <span className={`text-2xl font-bold font-mono ${getDeltaClass(official_gap)}`}>
              {formatDelta(official_gap)}
            </span>
            {reconciliation_valid && (
              <span className="text-green-500 text-lg" title="Reconciled within 5ms">
                ✓
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Track Coverage Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-500 mb-2">
          <span>Track Coverage</span>
          <span>
            Corners: {(track_coverage * 100).toFixed(1)}% |
            Straights: {((1 - track_coverage) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-3 bg-f1gray/30 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${track_coverage * 100}%` }}
            title={`Corners: ${(track_coverage * 100).toFixed(1)}%`}
          />
          <div
            className="h-full bg-purple-500 transition-all duration-300"
            style={{ width: `${(1 - track_coverage) * 100}%` }}
            title={`Straights: ${((1 - track_coverage) * 100).toFixed(1)}%`}
          />
        </div>
        <div className="flex justify-between text-xs mt-1">
          <span className="text-blue-400 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
            Corners
          </span>
          <span className="text-purple-400 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" />
            Straights
          </span>
        </div>
      </div>

      {/* Straight Segments Table (collapsed by default) */}
      {straight_segments && straight_segments.length > 0 && (
        <details className="mb-4">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400 mb-2">
            View {straight_segments.length} straight segment{straight_segments.length > 1 ? 's' : ''}
          </summary>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-f1gray/30">
                  <th className="text-left py-1 px-2 text-gray-500">Segment</th>
                  <th className="text-right py-1 px-2 text-gray-500">Length</th>
                  <th className="text-right py-1 px-2 text-gray-500">Delta</th>
                  <th className="text-center py-1 px-2 text-gray-500">Factor</th>
                </tr>
              </thead>
              <tbody>
                {straight_segments.map((seg) => (
                  <StraightSegmentRow key={seg.segment_number} segment={seg} />
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}

      {/* Educational Insight */}
      {insight_text && (
        <div className="p-3 rounded-lg bg-blue-900/20 border border-blue-800/30">
          <div className="flex gap-2">
            <span className="text-blue-400 flex-shrink-0">ℹ</span>
            <p className="text-xs text-gray-400 leading-relaxed">{insight_text}</p>
          </div>
        </div>
      )}

      {/* Reconciliation Warning (if not valid) */}
      {!reconciliation_valid && (
        <div className="mt-3 p-2 rounded-lg bg-yellow-900/20 border border-yellow-800/30">
          <div className="flex gap-2">
            <span className="text-yellow-400">⚠</span>
            <p className="text-xs text-yellow-400/80">
              Reconciliation error: {(reconciliation_error * 1000).toFixed(0)}ms
              (exceeds 5ms tolerance). Data quality may affect accuracy.
            </p>
          </div>
        </div>
      )}

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
            <h4 className="text-sm font-semibold text-gray-300 mb-2">The Equation</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                The headline equation — Corners + Straights = Official Gap — is the mathematical validation check for the analysis. If the sum of corner deltas and straight-line deltas matches the official gap (within 5ms tolerance), it confirms the analysis accounts for all time across the full lap.
              </p>
              <p>
                The green checkmark (✓) means internal consistency — the numbers add up. The warning icon (⚠) with a reconciliation error means the analysis could not fully account for all time, which typically indicates data quality issues at this circuit.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Track Coverage</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                The coverage bar shows what percentage of the lap is classified as corners vs straights. This split is defined by corner zone boundaries. A higher corner percentage means more of the lap is under detailed corner-by-corner analysis.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Straight Segments</h4>
            <div className="text-sm text-gray-500 space-y-1.5">
              <p>
                Each straight shows a time delta and a &quot;primary factor&quot; classification — Aero Efficiency, Exit Traction, High Drag, Poor Traction, or Balanced. These are inferred from telemetry speed and acceleration patterns and indicate setup tendencies rather than definitive diagnoses.
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Limitations</h4>
            <div className="text-sm text-gray-500/80 italic space-y-1.5">
              <p>
                Internal consistency (✓) does not guarantee accuracy — errors in individual corner attributions could cancel each other out while the total still matches.
              </p>
              <p>
                Straight-line primary factors are derived from publicly available speed data. The actual cause of a speed difference could be engine mode, DRS usage, battery deployment, or aerodynamic configuration — none of which are individually identifiable from speed traces alone.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Individual straight segment row
 */
function StraightSegmentRow({ segment }: { segment: StraightSegment }) {
  const getDeltaClass = (value: number) => {
    if (value > 0.005) return 'text-delta-positive'
    if (value < -0.005) return 'text-delta-negative'
    return 'text-gray-400'
  }

  // Factor badge colors (matching StraightLinePrimaryFactor from backend)
  const factorBadge = {
    aero_efficiency: 'bg-cyan-500/20 text-cyan-400',
    exit_traction: 'bg-green-500/20 text-green-400',
    traction: 'bg-orange-500/20 text-orange-400',  // Legacy
    poor_traction: 'bg-red-500/20 text-red-400',
    high_drag: 'bg-orange-500/20 text-orange-400',
    drag: 'bg-red-500/20 text-red-400',  // Legacy
    balanced: 'bg-gray-500/20 text-gray-400',
  }[segment.primary_factor] || 'bg-gray-500/20 text-gray-400'

  // Human-readable factor names
  const factorLabel = {
    aero_efficiency: 'Aero',
    exit_traction: 'Exit Traction',
    traction: 'Traction',  // Legacy
    poor_traction: 'Poor Traction',
    high_drag: 'High Drag',
    drag: 'Drag',  // Legacy
    balanced: 'Balanced',
  }[segment.primary_factor] || segment.primary_factor

  return (
    <tr className="border-b border-f1gray/10 hover:bg-f1gray/10">
      <td className="py-1 px-2 text-gray-300">{segment.name}</td>
      <td className="py-1 px-2 text-right text-gray-400 font-mono">
        {segment.length.toFixed(0)}m
      </td>
      <td className={`py-1 px-2 text-right font-mono ${getDeltaClass(segment.delta_change)}`}>
        {formatDelta(segment.delta_change)}
      </td>
      <td className="py-1 px-2 text-center">
        <span className={`px-2 py-0.5 rounded text-xs ${factorBadge}`}>
          {factorLabel}
        </span>
      </td>
    </tr>
  )
}
