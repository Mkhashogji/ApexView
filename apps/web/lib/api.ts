import {
  Session,
  Lap,
  Telemetry,
  DeltaData,
  SectorComparison,
  Track,
  Corner,
  MLInsightsResponse,
  LapSimilarityResponse,
  ClusteringResponse,
  ScaledDeltaResponse,
  CornerAnalysisResponse,
  PerformanceInsightsResponse,
  RacePaceResponse,
  TyreDegradationResponse,
  PitStopAnalysisResponse,
  TeamPerformanceResponse,
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
// Race Analysis
// ============================================================================

export async function fetchRacePace(
  sessionId: string,
  fuelEffect?: number
): Promise<RacePaceResponse> {
  const params = new URLSearchParams({ session: sessionId })
  if (fuelEffect !== undefined) {
    params.set('fuel_effect', fuelEffect.toString())
  }
  return fetchApi<RacePaceResponse>(`${API_BASE_URL}/race/pace?${params}`)
}

export async function fetchTyreDegradation(
  sessionId: string,
  fuelEffect?: number,
  mode: string = 'driver',
): Promise<TyreDegradationResponse> {
  const params = new URLSearchParams({ session: sessionId, mode })
  if (fuelEffect !== undefined) {
    params.set('fuel_effect', fuelEffect.toString())
  }
  return fetchApi<TyreDegradationResponse>(
    `${API_BASE_URL}/race/tyre-degradation?${params}`
  )
}

export async function fetchPitStops(
  sessionId: string,
): Promise<PitStopAnalysisResponse> {
  const params = new URLSearchParams({ session: sessionId })
  return fetchApi<PitStopAnalysisResponse>(
    `${API_BASE_URL}/race/pit-stops?${params}`
  )
}

export async function fetchTeamPerformance(
  sessionId: string,
  fuelEffect?: number,
): Promise<TeamPerformanceResponse> {
  const params = new URLSearchParams({ session: sessionId })
  if (fuelEffect !== undefined) {
    params.set('fuel_effect', fuelEffect.toString())
  }
  return fetchApi<TeamPerformanceResponse>(
    `${API_BASE_URL}/race/team-performance?${params}`
  )
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

// =============================================================================
// Phase 2: Scaled Delta API
// =============================================================================

const ML_SERVICE_URL = process.env.NEXT_PUBLIC_ML_SERVICE_URL || 'http://localhost:8501'

/**
 * Fetch scaled delta analysis from ML service.
 *
 * Uses Phase 2's algorithm that:
 * - Calculates delta from telemetry (WHERE time is gained/lost)
 * - Scales to match official timing (correct magnitude)
 * - Returns confidence score and scaling metadata
 */
export async function fetchScaledDelta(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  sessionPart?: string
): Promise<ScaledDeltaResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/ml/scaled-delta`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      reference_driver: referenceDriver,
      compare_drivers: compareDrivers,
      session_part: sessionPart,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, `Scaled delta request failed: ${errorText}`)
  }

  const data = await response.json()

  // Transform snake_case response to camelCase for frontend
  return {
    sessionId: data.session_id,
    referenceDriver: data.reference_driver,
    results: data.results.map((r: Record<string, unknown>) => ({
      referenceDriver: r.reference_driver,
      compareDriver: r.compare_driver,
      distance: r.distance,
      delta: r.delta,
      rawDelta: r.raw_delta,
      officialGap: r.official_gap,
      telemetryGap: r.telemetry_gap,
      scalingFactor: r.scaling_factor,
      confidence: r.confidence,
    })),
    metadata: {
      sessionPart: data.metadata?.session_part,
      driversAnalyzed: data.metadata?.drivers_analyzed,
      driversFailed: data.metadata?.drivers_failed,
      errors: data.metadata?.errors,
    },
  }
}

// =============================================================================
// Phase 3: Corner Analysis API
// =============================================================================

/**
 * Fetch corner-by-corner analysis from ML service.
 *
 * Uses Phase 3's algorithm that:
 * - Detects braking zones using telemetry
 * - Defines corner zones (brake start to apex + exit)
 * - Computes delta change within each zone
 * - Attributes cause (braking, apex, exit, multiple)
 */
export async function fetchCornerAnalysis(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[],
  sessionPart?: string
): Promise<CornerAnalysisResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/ml/corner-analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      reference_driver: referenceDriver,
      compare_drivers: compareDrivers,
      corners: corners.map(c => ({
        corner_number: c.cornerNumber,
        name: c.name,
        apex_distance: c.distance,
        corner_type: c.type,
      })),
      session_part: sessionPart,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, `Corner analysis request failed: ${errorText}`)
  }

  const data = await response.json()

  // Transform snake_case response to camelCase for frontend
  return {
    sessionId: data.session_id,
    referenceDriver: data.reference_driver,
    results: data.results.map((r: Record<string, unknown>) => ({
      compareDriver: r.compare_driver,
      cornerResults: (r.corner_results as Record<string, unknown>[]).map(cr => ({
        cornerNumber: cr.corner_number,
        name: cr.name,
        apexDistance: cr.apex_distance,
        brakeDistance: cr.brake_distance,
        zoneStart: cr.zone_start,
        zoneEnd: cr.zone_end,
        deltaChange: cr.delta_change,
        cause: cr.cause,
        confidence: cr.confidence,
      })),
      totalDeltaChange: r.total_delta_change,
      cornersGaining: r.corners_gaining,
      cornersLosing: r.corners_losing,
    })),
    metadata: {
      sessionPart: data.metadata?.session_part,
      driversAnalyzed: data.metadata?.drivers_analyzed,
      cornersAnalyzed: data.metadata?.corners_analyzed,
      driversFailed: data.metadata?.drivers_failed,
      errors: data.metadata?.errors,
    },
  }
}

// =============================================================================
// Phase 7: Performance Insights API (Unified Endpoint)
// =============================================================================

/**
 * Fetch unified performance insights from Phase 6 endpoint.
 *
 * This single endpoint orchestrates Phases 2-5:
 * - Phase 2: Scaled delta analysis (WHERE time is gained/lost)
 * - Phase 3: Corner-by-corner breakdown (WHY time is gained/lost)
 * - Phase 4: Technique profiling (braking, apex, exit, consistency)
 * - Phase 5: Natural language insights (engineer and driver summaries)
 */
export async function fetchPerformanceInsights(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[],
  mode: 'engineer' | 'driver' = 'engineer',
  sessionPart?: string,
  trackLength?: number
): Promise<PerformanceInsightsResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/ml/performance-insights`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      reference_driver: referenceDriver,
      compare_drivers: compareDrivers,
      corners: corners.map(c => ({
        corner_number: c.cornerNumber,
        name: c.name,
        apex_distance: c.distance,
        corner_type: c.type,
      })),
      mode,
      session_part: sessionPart ?? null,
      include_telemetry: false, // Don't include large arrays for frontend
      track_length: trackLength ?? null,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, `Performance insights request failed: ${errorText}`)
  }

  return response.json()
}

export { ApiError }

