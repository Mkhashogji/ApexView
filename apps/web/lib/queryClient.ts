import { QueryClient } from '@tanstack/react-query'

/**
 * Global React Query client with optimized cache settings for F1 data.
 *
 * F1 session data is immutable for historical events, so we use generous
 * cache times. This ensures switching back to a previously visited round
 * loads instantly from memory without a network request.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes — data is immutable for completed sessions
      gcTime: 30 * 60 * 1000, // 30 minutes — keep cached rounds for instant back-navigation
      refetchOnWindowFocus: false, // Don't refetch on window focus for analysis data
      refetchOnMount: false, // Don't refetch on component remount if data is fresh
      retry: 2, // Retry failed requests twice
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
})

