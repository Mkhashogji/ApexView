import { useQuery } from '@tanstack/react-query'
import { fetchScaledDelta } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { ScaledDeltaResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching scaled delta analysis.
 *
 * Uses Phase 2's delta analysis which:
 * - Shows WHERE time is gained/lost (from telemetry shape)
 * - Matches official timing for HOW MUCH (via scaling)
 * - Includes confidence score and scaling metadata
 *
 * Cache strategy: 60 seconds stale time (longer than regular delta
 * because scaling calculation is computationally expensive)
 */
export function useScaledDeltaQuery(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  sessionPart?: string
) {
  return useQuery<ScaledDeltaResponse>({
    queryKey: queryKeys.ml.scaledDelta(sessionId, referenceDriver, compareDrivers, sessionPart),
    queryFn: () => fetchScaledDelta(sessionId, referenceDriver, compareDrivers, sessionPart),
    staleTime: 60000, // 60 seconds - longer cache for expensive calculation
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0),
    retry: 1, // Only retry once for ML endpoints
  })
}
