import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchRacePace } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { RacePaceResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching race pace distribution data.
 * Returns pre-computed box plot statistics per driver.
 */
export function useRacePaceQuery(
  sessionId: string | undefined,
  fuelEffect?: number
) {
  return useQuery<RacePaceResponse>({
    queryKey: queryKeys.race.pace(sessionId ?? '', fuelEffect),
    queryFn: () => fetchRacePace(sessionId!, fuelEffect),
    enabled: !!sessionId,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  })
}
