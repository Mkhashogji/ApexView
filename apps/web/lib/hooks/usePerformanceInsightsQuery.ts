/**
 * React Query hook for fetching unified performance insights.
 *
 * This hook calls the Phase 6 unified endpoint which orchestrates:
 * - Phase 2: Scaled delta analysis
 * - Phase 3: Corner-by-corner breakdown
 * - Phase 4: Technique profiling
 * - Phase 5: Natural language insights
 */

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchPerformanceInsights } from '@/lib/api'
import { queryKeys } from './queryKeys'
import type { Corner, PerformanceInsightsResponse, InsightMode } from '@/../../packages/models/src/types'

interface UsePerformanceInsightsOptions {
  sessionId: string
  referenceDriver: string
  compareDrivers: string[]
  corners: Corner[] | undefined
  mode?: InsightMode
  sessionPart?: string
  trackLength?: number
}

/**
 * Fetch unified performance insights from the ML service.
 *
 * @param sessionId - Session identifier (e.g., '2025_24_Qualifying')
 * @param referenceDriver - Reference driver code (e.g., 'VER')
 * @param compareDrivers - Array of driver codes to compare
 * @param corners - Track corner definitions (from track intelligence)
 * @param mode - Insight mode: 'engineer' (metrics-heavy) or 'driver' (actionable)
 * @param sessionPart - Qualifying session part filter (Q1, Q2, Q3)
 * @returns React Query result with PerformanceInsightsResponse
 */
export function usePerformanceInsightsQuery({
  sessionId,
  referenceDriver,
  compareDrivers,
  corners,
  mode = 'engineer',
  sessionPart,
  trackLength,
}: UsePerformanceInsightsOptions) {
  return useQuery<PerformanceInsightsResponse, Error>({
    queryKey: queryKeys.ml.performanceInsights(
      sessionId,
      referenceDriver,
      compareDrivers,
      mode,
      sessionPart
    ),
    queryFn: () =>
      fetchPerformanceInsights(
        sessionId,
        referenceDriver,
        compareDrivers,
        corners!,
        mode,
        sessionPart,
        trackLength
      ),
    // Only enable when all required data is present
    enabled:
      !!sessionId &&
      !!referenceDriver &&
      compareDrivers.length > 0 &&
      !!corners &&
      corners.length > 0,
    placeholderData: keepPreviousData,
  })
}
