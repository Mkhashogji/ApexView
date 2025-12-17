import { useQuery } from '@tanstack/react-query'
import { fetchTrack } from '@/lib/api'
import { queryKeys } from './queryKeys'
import { Track } from '@/../../packages/models/src/types'

/**
 * React Query hook for fetching track information.
 * Includes circuit layout, sectors, DRS zones, corners, and elevation data.
 * 
 * Cache strategy: 5 minutes (track data is static for a season)
 */
export function useTrackQuery(round: number, season: number = 2025) {
  return useQuery<Track>({
    queryKey: queryKeys.track.detail(round),
    queryFn: () => fetchTrack(round, season),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes (track data rarely changes)
    enabled: Boolean(round > 0),
  })
}

/**
 * Helper hook to get DRS zones for chart annotations
 */
export function useDRSZones(round: number) {
  const { data: track, ...rest } = useTrackQuery(round)
  
  return {
    drsZones: track?.drsZones ?? [],
    ...rest,
  }
}

/**
 * Helper hook to get corner information for chart annotations
 */
export function useCorners(round: number) {
  const { data: track, ...rest } = useTrackQuery(round)
  
  return {
    corners: track?.corners ?? [],
    ...rest,
  }
}

/**
 * Helper hook to get sector boundaries for chart annotations
 */
export function useSectorBoundaries(round: number) {
  const { data: track, ...rest } = useTrackQuery(round)
  
  return {
    sectors: track?.sectors ?? [],
    trackLength: track?.length ?? 0,
    ...rest,
  }
}
