import { useQuery } from '@tanstack/react-query'
import { fetchDelta } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching delta analysis.
 * 
 * Cache strategy: 30 seconds stale time (delta is computed, cache to avoid recomputation)
 */
export function useDeltaQuery(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[]
) {
  return useQuery({
    queryKey: queryKeys.delta.analysis(sessionId, referenceDriver, compareDrivers),
    queryFn: () => fetchDelta(sessionId, referenceDriver, compareDrivers),
    staleTime: 30000, // 30 seconds
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0),
  })
}

