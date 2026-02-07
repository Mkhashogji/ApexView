import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchCornerAnalysis } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { CornerAnalysisResponse, Corner } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching corner-by-corner analysis (Phase 3).
 *
 * Requires track corner data to be passed in. The hook is disabled
 * when corners are undefined or empty.
 */
export function useCornerAnalysisQuery(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[] | undefined,
  sessionPart?: string
) {
  return useQuery<CornerAnalysisResponse>({
    queryKey: queryKeys.ml.cornerAnalysis(sessionId, referenceDriver, compareDrivers, sessionPart),
    queryFn: () => fetchCornerAnalysis(sessionId, referenceDriver, compareDrivers, corners!, sessionPart),
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0 && corners && corners.length > 0),
    retry: 1,
    placeholderData: keepPreviousData,
  })
}
