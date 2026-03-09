import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchProgression } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { PracticeProgressionResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching session progression data.
 * Returns cross-session gap-to-best for each driver across FP1/FP2/FP3.
 *
 * Weekend-level query (year + round), not session-specific.
 */
export function useSessionProgressionQuery(
  year: number,
  round: number,
  enabled: boolean = true,
) {
  return useQuery<PracticeProgressionResponse>({
    queryKey: queryKeys.practice.progression(year, round),
    queryFn: () => fetchProgression(year, round),
    enabled: year > 0 && round > 0 && enabled,
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000,
    placeholderData: keepPreviousData,
  })
}
