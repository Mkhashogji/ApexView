import { useQuery } from '@tanstack/react-query'
import { fetchCornerAnalysis } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { CornerAnalysisResponse, Corner } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching corner-by-corner analysis.
 *
 * Uses Phase 3's corner analysis which:
 * - Detects braking zones using telemetry
 * - Defines corner zones (brake start to apex + exit)
 * - Shows WHERE time is gained/lost at each corner
 * - Attributes cause (braking, apex, exit, multiple)
 * - Provides confidence levels based on brake detection quality
 *
 * Cache strategy: 60 seconds stale time (matches scaled delta
 * because this analysis depends on the same base calculation)
 *
 * Note: Requires track corner data to be passed in. The hook is disabled
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
    staleTime: 60000, // 60 seconds - matches scaled delta cache time
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0 && corners && corners.length > 0),
    retry: 1, // Only retry once for ML endpoints
  })
}
