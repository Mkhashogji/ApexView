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
    list: (sessionId: string, drivers: string[]) => 
      ['telemetry', 'list', sessionId, { drivers: drivers.sort() }] as const,
  },
  delta: {
    all: ['delta'] as const,
    analysis: (sessionId: string, referenceDriver: string, compareDrivers: string[]) =>
      ['delta', 'analysis', sessionId, referenceDriver, { compareDrivers: compareDrivers.sort() }] as const,
  },
  sectors: {
    all: ['sectors'] as const,
    list: (sessionId: string, drivers: string[]) =>
      ['sectors', 'list', sessionId, { drivers: drivers.sort() }] as const,
  },
  track: {
    all: ['track'] as const,
    detail: (round: number) => 
      ['track', 'detail', round] as const,
  },
} as const

