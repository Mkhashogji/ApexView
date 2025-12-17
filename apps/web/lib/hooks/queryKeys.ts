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
  // ML Service query keys
  ml: {
    all: ['ml'] as const,
    insights: (sessionId: string, drivers: string[]) =>
      ['ml', 'insights', sessionId, { drivers: drivers.sort() }] as const,
    similarity: (sessionId: string, driver1: string, driver2: string) =>
      ['ml', 'similarity', sessionId, { drivers: [driver1, driver2].sort() }] as const,
    clustering: (sessionId: string, drivers: string[], nClusters: number) =>
      ['ml', 'clustering', sessionId, { drivers: drivers.sort(), nClusters }] as const,
  },
} as const

