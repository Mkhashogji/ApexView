import { useQuery } from '@tanstack/react-query'
import { fetchTelemetry } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching telemetry data.
 * 
 * Cache strategy: 30 seconds stale time (telemetry is static and large, cache aggressively)
 */
export function useTelemetryQuery(
  sessionId: string, 
  drivers: string[],
  sessionPart?: string
) {
  return useQuery({
    queryKey: queryKeys.telemetry.list(sessionId, drivers, sessionPart),
    queryFn: () => fetchTelemetry(sessionId, drivers, sessionPart),
    staleTime: 30000, // 30 seconds
    enabled: Boolean(sessionId && drivers.length > 0), // Only fetch if we have valid params
  })
}

