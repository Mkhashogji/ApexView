import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchLongRuns } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { PracticeLongRunResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching long run pace data.
 * Returns pre-computed box plot statistics per driver-stint.
 */
export function useLongRunQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
  enabled: boolean = true,
) {
  return useQuery<PracticeLongRunResponse>({
    queryKey: queryKeys.practice.longRuns(sessionId ?? '', fuelEffect),
    queryFn: () => fetchLongRuns(sessionId!, fuelEffect),
    enabled: !!sessionId && enabled,
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000, // 30 minutes
    placeholderData: keepPreviousData,
  })
}
