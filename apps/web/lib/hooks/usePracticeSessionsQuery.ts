import { useQuery } from '@tanstack/react-query'
import { fetchPracticeSessions } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { PracticeSessionsResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching available practice sessions.
 * Returns ["FP1", "FP2", "FP3"] for traditional weekends,
 * ["FP1"] for sprint weekends.
 */
export function usePracticeSessionsQuery(
  year: number,
  round: number,
) {
  return useQuery<PracticeSessionsResponse>({
    queryKey: queryKeys.practice.sessions(year, round),
    queryFn: () => fetchPracticeSessions(year, round),
    enabled: year > 0 && round > 0,
    staleTime: Infinity,
  })
}
