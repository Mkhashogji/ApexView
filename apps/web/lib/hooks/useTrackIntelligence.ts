import { useTrackQuery } from './useTrackQuery'
import { getTrackIntelligence, hasTrackIntelligence, type TrackIntelligence } from '@/data/tracks'
import type { Track } from '@/../../packages/models/src/types'

/**
 * Combined hook for Track Intelligence page.
 * 
 * Combines:
 * - Core track data from API (sectors, DRS zones, corners for telemetry overlays)
 * - Editorial content from static files (descriptions, insights, benchmarks)
 * 
 * @param round - Race weekend round number
 * @param season - Season year (defaults to 2025)
 */
export function useTrackIntelligence(round: number, season: number = 2025) {
  // API track data (core metadata for charts)
  const apiQuery = useTrackQuery(round, season)
  
  // Static editorial data (rich descriptions and analysis)
  const editorialData = getTrackIntelligence(round)
  const hasEditorial = hasTrackIntelligence(round)
  
  return {
    // API data
    apiData: apiQuery.data as Track | undefined,
    isLoading: apiQuery.isLoading,
    isError: apiQuery.isError,
    error: apiQuery.error,
    
    // Editorial data
    editorial: editorialData as TrackIntelligence | undefined,
    hasEditorial,
    
    // Combined status
    isComplete: hasEditorial && apiQuery.isSuccess,
    
    // Refetch API data
    refetch: apiQuery.refetch,
  }
}

/**
 * Type for the return value of useTrackIntelligence
 */
export type UseTrackIntelligenceResult = ReturnType<typeof useTrackIntelligence>
