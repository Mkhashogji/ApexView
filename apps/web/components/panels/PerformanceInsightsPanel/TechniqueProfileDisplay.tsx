'use client'

import type { TechniqueProfile } from '@/../../packages/models/src/types'
import { DimensionBar } from './DimensionBar'

interface TechniqueProfileDisplayProps {
  /** Technique profile data from Phase 4 */
  profile: TechniqueProfile
  /** Whether to show delta values (default: true) */
  showDeltas?: boolean
}

/**
 * Display all five dimension bars together:
 * - Braking (corner entry)
 * - Apex (mid-corner)
 * - Exit (corner exit)
 * - Consistency (lap-to-lap variation)
 * - Straight-Line (5th dimension, optional)
 */
export function TechniqueProfileDisplay({
  profile,
  showDeltas = true,
}: TechniqueProfileDisplayProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Technique Profile
      </h4>

      <div className="space-y-2">
        {/* Corner Dimensions */}
        <DimensionBar
          dimension="braking"
          percentile={profile.braking.percentile}
          level={profile.braking.level}
          delta={showDeltas ? profile.braking.raw_value : undefined}
        />
        <DimensionBar
          dimension="apex"
          percentile={profile.apex.percentile}
          level={profile.apex.level}
          delta={showDeltas ? profile.apex.raw_value : undefined}
        />
        <DimensionBar
          dimension="exit"
          percentile={profile.exit.percentile}
          level={profile.exit.level}
          delta={showDeltas ? profile.exit.raw_value : undefined}
        />
        <DimensionBar
          dimension="consistency"
          percentile={profile.consistency.percentile}
          level={profile.consistency.level}
          // Consistency doesn't have a delta value in the same sense
        />

        {/* 5th Dimension: Straight-Line Performance */}
        {profile.straight_line && (
          <>
            <div className="border-t border-f1gray/30 my-2 pt-2">
              <span className="text-xs text-gray-500">Straight-Line Performance</span>
            </div>
            <DimensionBar
              dimension="straight_line"
              percentile={profile.straight_line.percentile}
              level={profile.straight_line.level}
              delta={showDeltas ? profile.straight_line.raw_delta : undefined}
            />
            {/* Primary Factor Badge */}
            <div className="flex items-center gap-2 ml-24 mt-1">
              <span className="text-xs text-gray-500">Factor:</span>
              <StraightLineFactorBadge factor={profile.straight_line.primary_factor} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}

/** Primary factor badge component */
function StraightLineFactorBadge({ factor }: { factor: string }) {
  const badgeStyles: Record<string, string> = {
    aero_efficiency: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    exit_traction: 'bg-green-500/20 text-green-400 border-green-500/30',
    high_drag: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    poor_traction: 'bg-red-500/20 text-red-400 border-red-500/30',
    balanced: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }

  const labels: Record<string, string> = {
    aero_efficiency: 'Aero Efficiency',
    exit_traction: 'Exit Traction',
    high_drag: 'High Drag',
    poor_traction: 'Poor Traction',
    balanced: 'Balanced',
  }

  return (
    <span className={`px-2 py-0.5 rounded border text-xs ${badgeStyles[factor] || badgeStyles.balanced}`}>
      {labels[factor] || factor}
    </span>
  )
}
