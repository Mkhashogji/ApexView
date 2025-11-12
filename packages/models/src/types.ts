/**
 * Shared TypeScript types for F1 Engineering App
 */

export type SessionType = 
  | 'Practice'
  | 'Qualifying'
  | 'Sprint Qualifying'
  | 'Sprint'
  | 'Race'

export interface Session {
  sessionId: string
  sessionType: SessionType
  sessionName: string
  season: number
  round: number
  isSprintWeekend: boolean
  date?: string
  circuitName?: string
}

export interface Lap {
  lapNumber: number
  driver: string
  lapTime: number
  sector1Time?: number
  sector2Time?: number
  sector3Time?: number
  compound?: TyreCompound
  tyreAge?: number
  isPersonalBest: boolean
}

export interface Telemetry {
  driver: string
  lapNumber: number
  distance: number[]
  speed: number[]
  throttle: number[]
  brake: number[]
  gear: number[]
  rpm?: number[]
  drs?: number[]
}

export type TyreCompound = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET'

export interface Stint {
  stintNumber: number
  compound: TyreCompound
  startLap: number
  endLap: number
  lapCount: number
}

export interface SectorInfo {
  sectorNumber: number
  startDistance: number
  endDistance: number
}

export interface DRSZone {
  zoneNumber: number
  detectionPoint: number
  activationPoint: number
  endPoint: number
}

export interface Track {
  circuitName: string
  round: number
  season: number
  length: number  // meters
  sectors: SectorInfo[]
  drsZones: DRSZone[]
  corners?: Corner[]
  elevationData?: ElevationPoint[]
}

export interface Corner {
  cornerNumber: number
  name?: string
  distance: number
  type: 'left' | 'right'
  angle?: number  // degrees
}

export interface ElevationPoint {
  distance: number
  elevation: number  // meters
}

export interface DriverInfo {
  abbreviation: string
  fullName: string
  team: string
  teamColor: string
  number: number
}

export interface DeltaData {
  referenceDriver: string
  compareDriver: string
  distance: number[]
  delta: number[]  // seconds, positive = compare driver is slower
}

export interface SectorComparison {
  driver: string
  sector1: number  // seconds
  sector2: number  // seconds
  sector3: number  // seconds
  totalTime: number  // seconds
}

