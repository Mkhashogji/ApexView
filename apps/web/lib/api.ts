import { Session, Lap, Telemetry, DeltaData, SectorComparison } from '@/../../packages/models/src/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(url: string): Promise<T> {
  try {
    const response = await fetch(url)
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

export async function fetchSessions(season: number, round: number): Promise<Session[]> {
  return fetchApi<Session[]>(`${API_BASE_URL}/sessions?season=${season}&round=${round}`)
}

export async function fetchLaps(sessionId: string, drivers: string[]): Promise<Lap[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  return fetchApi<Lap[]>(`${API_BASE_URL}/laps?session=${sessionId}&${driverParams}`)
}

export async function fetchTelemetry(sessionId: string, drivers: string[]): Promise<Telemetry[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  return fetchApi<Telemetry[]>(`${API_BASE_URL}/telemetry?session=${sessionId}&${driverParams}`)
}

export async function fetchDelta(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[]
): Promise<DeltaData[]> {
  const compareParams = compareDrivers.map(d => `compare_drivers=${d}`).join('&')
  return fetchApi<DeltaData[]>(
    `${API_BASE_URL}/telemetry/delta?session=${sessionId}&reference_driver=${referenceDriver}&${compareParams}`
  )
}

export async function fetchSectors(sessionId: string, drivers: string[]): Promise<SectorComparison[]> {
  const driverParams = drivers.map(d => `drivers=${d}`).join('&')
  return fetchApi<SectorComparison[]>(`${API_BASE_URL}/laps/sectors?session=${sessionId}&${driverParams}`)
}

export async function fetchTrack(round: number) {
  return fetchApi(`${API_BASE_URL}/track/${round}`)
}

export { ApiError }

