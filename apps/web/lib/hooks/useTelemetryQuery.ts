import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchTelemetry } from '@/lib/api'
import { queryKeys } from './queryKeys'

/**
 * React Query hook for fetching telemetry data.
 */
export function useTelemetryQuery(
  sessionId: string,
  drivers: string[],
  sessionPart?: string
) {
  return useQuery({
    queryKey: queryKeys.telemetry.list(sessionId, drivers, sessionPart),
    queryFn: () => fetchTelemetry(sessionId, drivers, sessionPart),
    enabled: Boolean(sessionId && drivers.length > 0),
    placeholderData: keepPreviousData,
  })
}

