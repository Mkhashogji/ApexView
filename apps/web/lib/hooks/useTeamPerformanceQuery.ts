import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchTeamPerformance } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { TeamPerformanceResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching team performance quadrant data.
 * Returns per-team top speed and mean speed with field-average deltas
 * and deterministic insight data.
 *
 * Accepts optional fuelEffect so mean speed uses fuel-corrected lap times.
 */
export function useTeamPerformanceQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
  enabled: boolean = true,
) {
  return useQuery<TeamPerformanceResponse>({
    queryKey: queryKeys.race.teamPerformance(sessionId ?? '', fuelEffect),
    queryFn: () => fetchTeamPerformance(sessionId!, fuelEffect),
    enabled: enabled && !!sessionId,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}
