import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchPitStops } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { PitStopAnalysisResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching pit stop analysis data.
 * Returns pre-computed team/driver aggregates, gap-to-fastest,
 * and template-based insight data.
 *
 * No fuel_effect or mode parameters — pit stop analysis is
 * independent of fuel correction and has no driver/team toggle.
 */
export function usePitStopsQuery(
  sessionId: string | undefined,
  enabled: boolean = true,
) {
  return useQuery<PitStopAnalysisResponse>({
    queryKey: queryKeys.race.pitStops(sessionId ?? ''),
    queryFn: () => fetchPitStops(sessionId!),
    enabled: enabled && !!sessionId,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}
