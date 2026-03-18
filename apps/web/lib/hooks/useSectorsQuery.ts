import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchSectors } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching sector data.
 */
export function useSectorsQuery(
  sessionId: string,
  drivers: string[],
  sessionPart?: string
) {
  return useQuery({
    queryKey: queryKeys.sectors.list(sessionId, drivers, sessionPart),
    queryFn: () => fetchSectors(sessionId, drivers, sessionPart),
    enabled: Boolean(sessionId && drivers.length > 0),
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}

