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

// ============================================================================
// Qualifying Session Types
// ============================================================================

/** Qualifying session part (Q1/Q2/Q3 or SQ1/SQ2/SQ3 for sprint) */
export type QualifyingSessionPart = 'Q1' | 'Q2' | 'Q3' | 'SQ1' | 'SQ2' | 'SQ3'

/** Theoretical best lap calculation */
export interface TheoreticalBestLap {
  driver: string
  bestSector1: number
  bestSector2: number
  bestSector3: number
  theoreticalTime: number  // Sum of best sectors
  actualBestTime: number
  potentialGain: number  // actualBestTime - theoreticalTime
}

// ============================================================================
// ML Service Response Types
// ============================================================================

/** Individual insight from ML analysis */
export interface MLInsight {
  type: 'similarity' | 'cluster' | 'braking' | 'sector' | 'speed' | 'consistency' | 'error' | 'default'
  message: string
  confidence?: 'high' | 'medium' | 'low'
  drivers?: string[]
  data?: Record<string, unknown>
}

/** Response from /ml/insights/{session_id} endpoint */
export interface MLInsightsResponse {
  session_id: string
  drivers: string[]
  insights: MLInsight[]
  clusters?: ClusteringResponse
}

/** Feature-level similarity scores */
export interface FeatureScores {
  speed?: number
  throttle?: number
  brake?: number
  gear?: number
  overall?: number
}

/** Response from /ml/lap-similarity endpoint */
export interface LapSimilarityResponse {
  session_id: string
  driver1: string
  driver2: string
  similarity: number  // 0-1 overall similarity score
  feature_scores: FeatureScores
  metadata?: {
    num_points?: number
    distance_range?: [number, number]
  }
}

/** Individual driver cluster assignment */
export interface DriverCluster {
  driver: string
  cluster: number
  pca_x?: number  // PCA projection for visualization
  pca_y?: number
}

/** Response from /ml/driver-style-clustering endpoint */
export interface ClusteringResponse {
  session_id: string
  clusters: DriverCluster[]
  cluster_descriptions: Record<string, string>  // e.g., { "0": "Aggressive braking style" }
  explained_variance?: number[]  // PCA explained variance
  metadata?: {
    n_clusters: number
    drivers_analyzed: number
  }
}

