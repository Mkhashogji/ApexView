import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchSectorAnalysis } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { PracticeSectorAnalysisResponse } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching practice sector analysis data.
 * Returns per-driver sector breakdown, theoretical best laps,
 * and speed trap readings.
 */
export function useSectorAnalysisQuery(
  sessionId: string | undefined,
  enabled: boolean = true,
) {
  return useQuery<PracticeSectorAnalysisResponse>({
    queryKey: queryKeys.practice.sectorAnalysis(sessionId ?? ''),
    queryFn: () => fetchSectorAnalysis(sessionId!),
    enabled: !!sessionId && enabled,
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000, // 30 minutes
    placeholderData: keepPreviousData,
  })
}
