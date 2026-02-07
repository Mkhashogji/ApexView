import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchSessions } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching sessions.
 */
export function useSessionsQuery(season: number, round: number) {
  return useQuery({
    queryKey: queryKeys.sessions.list(season, round),
    queryFn: () => fetchSessions(season, round),
    enabled: Boolean(season && round),
    placeholderData: keepPreviousData,
  })
}

