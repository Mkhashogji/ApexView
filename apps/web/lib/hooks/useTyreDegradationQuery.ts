import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchTyreDegradation } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { TyreDegradationResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching tyre degradation analysis data.
 * Returns per-compound, per-driver regression data for scatter plots.
 *
 * Mode changes trigger a refetch (different backend computation).
 * Driver filtering is done client-side — no refetch needed.
 */
export function useTyreDegradationQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
  mode: string = 'driver',
  enabled: boolean = true,
) {
  return useQuery<TyreDegradationResponse>({
    queryKey: queryKeys.race.tyreDeg(sessionId ?? '', fuelEffect, mode),
    queryFn: () => fetchTyreDegradation(sessionId!, fuelEffect, mode),
    enabled: enabled && !!sessionId,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}
