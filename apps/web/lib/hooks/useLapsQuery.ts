import { useQuery } from '@tanstack/react-query'
import { fetchLaps } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching lap data.
 * 
 * Cache strategy: 30 seconds stale time (lap data is static for historical sessions)
 */
export function useLapsQuery(sessionId: string, drivers: string[]) {
  return useQuery({
    queryKey: queryKeys.laps.list(sessionId, drivers),
    queryFn: () => fetchLaps(sessionId, drivers),
    staleTime: 30000, // 30 seconds
    enabled: Boolean(sessionId && drivers.length > 0), // Only fetch if we have valid params
  })
}

