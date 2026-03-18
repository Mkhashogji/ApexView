/**
 * Query key factory for React Query.
 * Provides consistent, type-safe query keys across the application.
 */
export const queryKeys = {
  sessions: {
    all: ['sessions'] as const,
    list: (season: number, round: number) => 
      ['sessions', 'list', { season, round }] as const,
    detail: (sessionId: string) => 
      ['sessions', 'detail', sessionId] as const,
  },
  laps: {
    all: ['laps'] as const,
    list: (sessionId: string, drivers: string[]) => 
      ['laps', 'list', sessionId, { drivers: drivers.sort() }] as const,
  },
  telemetry: {
    all: ['telemetry'] as const,
    list: (sessionId: string, drivers: string[], sessionPart?: string) => 
      ['telemetry', 'list', sessionId, { drivers: drivers.sort(), sessionPart }] as const,
  },
  delta: {
    all: ['delta'] as const,
    analysis: (sessionId: string, referenceDriver: string, compareDrivers: string[], sessionPart?: string) =>
      ['delta', 'analysis', sessionId, referenceDriver, { compareDrivers: compareDrivers.sort(), sessionPart }] as const,
  },
  sectors: {
    all: ['sectors'] as const,
    list: (sessionId: string, drivers: string[], sessionPart?: string) =>
      ['sectors', 'list', sessionId, { drivers: drivers.sort(), sessionPart }] as const,
  },
  track: {
    all: ['track'] as const,
    detail: (round: number) => 
      ['track', 'detail', round] as const,
  },
  // Race Analysis query keys
  race: {
    all: ['race'] as const,
    pace: (sessionId: string, fuelEffect?: number) =>
      ['race', 'pace', sessionId, { fuelEffect }] as const,
    tyreDeg: (sessionId: string, fuelEffect?: number, mode?: string) =>
      ['race', 'tyreDeg', sessionId, { fuelEffect, mode }] as const,
    pitStops: (sessionId: string) =>
      ['race', 'pitStops', sessionId] as const,
    teamPerformance: (sessionId: string, fuelEffect?: number) =>
      ['race', 'teamPerformance', sessionId, { fuelEffect }] as const,
  },
  // Practice Analysis query keys
  practice: {
    all: ['practice'] as const,
    sessions: (year: number, round: number) =>
      ['practice', 'sessions', { year, round }] as const,
    longRuns: (sessionId: string, fuelEffect?: number) =>
      ['practice', 'longRuns', sessionId, { fuelEffect }] as const,
    shortRuns: (sessionId: string, fuelEffect?: number) =>
      ['practice', 'shortRuns', sessionId, { fuelEffect }] as const,
    sectorAnalysis: (sessionId: string) =>
      ['practice', 'sectorAnalysis', sessionId] as const,
    circuitSVG: (round: number) =>
      ['practice', 'circuitSVG', round] as const,
    progression: (year: number, round: number) =>
      ['practice', 'progression', { year, round }] as const,
  },
  // Analysis Service query keys
  analysis: {
    all: ['analysis'] as const,
    insights: (sessionId: string, drivers: string[]) =>
      ['analysis', 'insights', sessionId, { drivers: drivers.sort() }] as const,
    similarity: (sessionId: string, driver1: string, driver2: string) =>
      ['analysis', 'similarity', sessionId, { drivers: [driver1, driver2].sort() }] as const,
    clustering: (sessionId: string, drivers: string[], nClusters: number) =>
      ['analysis', 'clustering', sessionId, { drivers: drivers.sort(), nClusters }] as const,
    scaledDelta: (
      sessionId: string,
      refDriver: string,
      compareDrivers: string[],
      sessionPart?: string
    ) =>
      ['analysis', 'scaledDelta', sessionId, refDriver, { compareDrivers: [...compareDrivers].sort(), sessionPart }] as const,
    cornerAnalysis: (
      sessionId: string,
      refDriver: string,
      compareDrivers: string[],
      sessionPart?: string
    ) =>
      ['analysis', 'cornerAnalysis', sessionId, refDriver, { compareDrivers: [...compareDrivers].sort(), sessionPart }] as const,
    performanceInsights: (
      sessionId: string,
      refDriver: string,
      compareDrivers: string[],
      mode: 'engineer' | 'driver',
      sessionPart?: string
    ) =>
      ['analysis', 'performanceInsights', sessionId, refDriver, { compareDrivers: [...compareDrivers].sort(), mode, sessionPart }] as const,
  },
} as const

