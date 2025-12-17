import { useQuery } from '@tanstack/react-query'
import { fetchSectors } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching sector data.
 * 
 * Cache strategy: 30 seconds stale time
 */
export function useSectorsQuery(
  sessionId: string, 
  drivers: string[],
  sessionPart?: string
) {
  return useQuery({
    queryKey: queryKeys.sectors.list(sessionId, drivers, sessionPart),
    queryFn: () => fetchSectors(sessionId, drivers, sessionPart),
    staleTime: 30000, // 30 seconds
    enabled: Boolean(sessionId && drivers.length > 0),
  })
}

