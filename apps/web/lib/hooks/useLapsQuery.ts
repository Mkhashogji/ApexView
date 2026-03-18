import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchLaps } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching lap data.
 */
export function useLapsQuery(sessionId: string, drivers: string[]) {
  return useQuery({
    queryKey: queryKeys.laps.list(sessionId, drivers),
    queryFn: () => fetchLaps(sessionId, drivers),
    enabled: Boolean(sessionId && drivers.length > 0),
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}

