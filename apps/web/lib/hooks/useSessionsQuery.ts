import { useQuery } from '@tanstack/react-query'
import { fetchSessions } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching sessions.
 * 
 * Cache strategy: 2 minutes stale time (sessions rarely change during analysis)
 */
export function useSessionsQuery(season: number, round: number) {
  return useQuery({
    queryKey: queryKeys.sessions.list(season, round),
    queryFn: () => fetchSessions(season, round),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: Boolean(season && round), // Only fetch if params are valid
  })
}

