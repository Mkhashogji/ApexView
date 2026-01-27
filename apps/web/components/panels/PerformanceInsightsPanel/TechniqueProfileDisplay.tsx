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
 * Display all four dimension bars together:
 * - Braking
 * - Apex
 * - Exit
 * - Consistency
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
      </div>
    </div>
  )
}
