import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchShortRuns } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { PracticeShortRunResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching short run best lap data.
 * Returns ranked drivers with best lap from qualifying simulation stints.
 */
export function useShortRunQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
  enabled: boolean = true,
) {
  return useQuery<PracticeShortRunResponse>({
    queryKey: queryKeys.practice.shortRuns(sessionId ?? '', fuelEffect),
    queryFn: () => fetchShortRuns(sessionId!, fuelEffect),
    enabled: !!sessionId && enabled,
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000, // 30 minutes
    placeholderData: keepPreviousData,
  })
}
