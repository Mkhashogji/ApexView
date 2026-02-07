import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchScaledDelta } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { ScaledDeltaResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching scaled delta analysis (Phase 2).
 */
export function useScaledDeltaQuery(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  sessionPart?: string
) {
  return useQuery<ScaledDeltaResponse>({
    queryKey: queryKeys.ml.scaledDelta(sessionId, referenceDriver, compareDrivers, sessionPart),
    queryFn: () => fetchScaledDelta(sessionId, referenceDriver, compareDrivers, sessionPart),
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0),
    retry: 1,
    placeholderData: keepPreviousData,
  })
}
