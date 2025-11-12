import { QueryClient } from '@tanstack/react-query'

/**
 * Global React Query client with optimized cache settings for F1 data.
 * 
 * Cache Strategy:
 * - Session data: 2 minutes (rarely changes during analysis)
 * - Lap data: 30 seconds (semi-static for historical sessions)
 * - Telemetry: 30 seconds (large datasets, cache aggressively)
 * - Delta: 30 seconds (computed data, cache to avoid recomputation)
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds default
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      refetchOnWindowFocus: false, // Don't refetch on window focus for analysis data
      refetchOnMount: false, // Don't refetch on component remount if data is fresh
      retry: 2, // Retry failed requests twice
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
})

