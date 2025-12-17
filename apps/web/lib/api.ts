import { 
  Session, 
  Lap, 
  Telemetry, 
  DeltaData, 
  SectorComparison, 
  Track,
  MLInsightsResponse,
  LapSimilarityResponse,
  ClusteringResponse,
} from '@/../../packages/models/src/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Generic fetch helper with error handling
 */
async function fetchApi<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      throw new ApiError(response.status, `API request failed: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * POST helper for ML endpoints
 */
async function postApi<T>(url: string, body: object): Promise<T> {
  return fetchApi<T>(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
}

// ============================================================================
// Session & Lap Data
// ============================================================================

export async function fetchSessions(season: number, round: number): Promise<Session[]> {
  return fetchApi<Session[]>(`${API_BASE_URL}/sessions?season=${season}&round=${round}`)
}

export async function fetchLaps(sessionId: string, drivers: string[]): Promise<Lap[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  return fetchApi<Lap[]>(`${API_BASE_URL}/laps?session=${sessionId}&${driverParams}`)
}

// ============================================================================
// Telemetry Data
// ============================================================================

export async function fetchTelemetry(
  sessionId: string, 
  drivers: string[],
  sessionPart?: string
): Promise<Telemetry[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  const sessionPartParam = sessionPart ? `&session_part=${sessionPart}` : ''
  return fetchApi<Telemetry[]>(`${API_BASE_URL}/telemetry?session=${sessionId}&${driverParams}${sessionPartParam}`)
}

export async function fetchDelta(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  sessionPart?: string
): Promise<DeltaData[]> {
  const compareParams = compareDrivers.map(d => `compare_drivers=${d}`).join('&')
  const sessionPartParam = sessionPart ? `&session_part=${sessionPart}` : ''
  return fetchApi<DeltaData[]>(
    `${API_BASE_URL}/telemetry/delta?session=${sessionId}&reference_driver=${referenceDriver}&${compareParams}${sessionPartParam}`
  )
}

export async function fetchSectors(
  sessionId: string, 
  drivers: string[],
  sessionPart?: string
): Promise<SectorComparison[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  const sessionPartParam = sessionPart ? `&session_part=${sessionPart}` : ''
  return fetchApi<SectorComparison[]>(`${API_BASE_URL}/laps/sectors?session=${sessionId}&${driverParams}${sessionPartParam}`)
}

// ============================================================================
// Track Data
// ============================================================================

export async function fetchTrack(round: number, season: number = 2025): Promise<Track> {
  return fetchApi<Track>(`${API_BASE_URL}/track/${round}?season=${season}`)
}

// ============================================================================
// ML Service Endpoints
// ============================================================================

/**
 * Fetch combined ML insights for a session.
 * Includes clustering data and automated insights.
 */
export async function fetchMLInsights(
  sessionId: string, 
  drivers: string[]
): Promise<MLInsightsResponse> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  return fetchApi<MLInsightsResponse>(
    `${API_BASE_URL}/ml/insights/${sessionId}?${driverParams}`
  )
}

/**
 * Calculate lap similarity between two drivers.
 * Uses cosine similarity on telemetry features (speed, throttle, brake).
 */
export async function fetchLapSimilarity(
  sessionId: string,
  driver1: string,
  driver2: string
): Promise<LapSimilarityResponse> {
  return postApi<LapSimilarityResponse>(`${API_BASE_URL}/ml/lap-similarity`, {
    session_id: sessionId,
    driver1,
    driver2,
  })
}

/**
 * Cluster drivers by driving style.
 * Uses PCA + KMeans on telemetry features.
 */
export async function fetchDriverClustering(
  sessionId: string,
  drivers: string[],
  nClusters: number = 3
): Promise<ClusteringResponse> {
  return postApi<ClusteringResponse>(`${API_BASE_URL}/ml/driver-style-clustering`, {
    session_id: sessionId,
    drivers,
    n_clusters: nClusters,
  })
}

export { ApiError }

