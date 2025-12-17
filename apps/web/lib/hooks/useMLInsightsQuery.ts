import { useQuery } from '@tanstack/react-query'
import { 
  fetchMLInsights, 
  fetchLapSimilarity, 
  fetchDriverClustering 
} from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching ML-powered session insights.
 * Combines clustering data with automated analysis.
 * 
 * Cache strategy: 60 seconds (ML computations are expensive, cache aggressively)
 */
export function useMLInsightsQuery(sessionId: string, drivers: string[]) {
  return useQuery({
    queryKey: queryKeys.ml.insights(sessionId, drivers),
    queryFn: () => fetchMLInsights(sessionId, drivers),
    staleTime: 60000, // 60 seconds
    enabled: Boolean(sessionId && drivers.length >= 2), // Need at least 2 drivers for insights
    retry: 1, // Only retry once for ML endpoints
  })
}

/**
 * React Query hook for fetching lap similarity between two drivers.
 * Computes cosine similarity on telemetry features.
 * 
 * Cache strategy: 60 seconds (similarity scores are static for a given lap pair)
 */
export function useLapSimilarityQuery(
  sessionId: string, 
  driver1: string, 
  driver2: string
) {
  return useQuery({
    queryKey: queryKeys.ml.similarity(sessionId, driver1, driver2),
    queryFn: () => fetchLapSimilarity(sessionId, driver1, driver2),
    staleTime: 60000, // 60 seconds
    enabled: Boolean(sessionId && driver1 && driver2 && driver1 !== driver2),
    retry: 1,
  })
}

/**
 * React Query hook for fetching driver style clustering.
 * Groups drivers by driving characteristics using PCA + KMeans.
 * 
 * Cache strategy: 60 seconds (clustering is computationally expensive)
 */
export function useDriverClusteringQuery(
  sessionId: string, 
  drivers: string[], 
  nClusters: number = 3
) {
  return useQuery({
    queryKey: queryKeys.ml.clustering(sessionId, drivers, nClusters),
    queryFn: () => fetchDriverClustering(sessionId, drivers, nClusters),
    staleTime: 60000, // 60 seconds
    enabled: Boolean(sessionId && drivers.length >= 3), // Need at least 3 drivers for clustering
    retry: 1,
  })
}

/**
 * Combined hook for all ML insights - fetches similarity pairs and clustering
 * Useful for the AIInsights panel that needs multiple ML data sources
 */
export function useAllMLInsights(sessionId: string, drivers: string[]) {
  const insightsQuery = useMLInsightsQuery(sessionId, drivers)
  const clusteringQuery = useDriverClusteringQuery(sessionId, drivers)
  
  // Fetch pairwise similarities for first few driver pairs
  const driverPairs = drivers.slice(0, 4).flatMap((d1, i) => 
    drivers.slice(i + 1, 4).map(d2 => [d1, d2] as const)
  ).slice(0, 3) // Limit to 3 pairs
  
  const similarityQueries = driverPairs.map(([d1, d2]) => 
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useLapSimilarityQuery(sessionId, d1, d2)
  )
  
  return {
    insights: insightsQuery,
    clustering: clusteringQuery,
    similarities: similarityQueries,
    isLoading: insightsQuery.isLoading || clusteringQuery.isLoading || 
               similarityQueries.some(q => q.isLoading),
    isError: insightsQuery.isError || clusteringQuery.isError ||
             similarityQueries.some(q => q.isError),
  }
}
