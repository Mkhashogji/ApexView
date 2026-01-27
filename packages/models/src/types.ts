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
  /** True if zone crosses start/finish line (endPoint < activationPoint) */
  wrapAround?: boolean
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

// =============================================================================
// Phase 2: Scaled Delta Types
// =============================================================================

/** Request for scaled delta calculation */
export interface ScaledDeltaRequest {
  sessionId: string
  referenceDriver: string
  compareDrivers: string[]
  sessionPart?: string
}

/** Single driver comparison result with scaling metadata */
export interface ScaledDeltaDriverResult {
  referenceDriver: string
  compareDriver: string
  distance: number[]       // Common distance grid (meters)
  delta: number[]          // Scaled delta (matches official timing)
  rawDelta: number[]       // Original telemetry-derived delta
  officialGap: number      // Official timing gap (ground truth from FIA)
  telemetryGap: number     // Raw telemetry-calculated gap
  scalingFactor: number    // Multiplier: officialGap / telemetryGap
  confidence: number       // 0-1 score based on scaling factor deviation
}

/** Complete response from scaled delta endpoint */
export interface ScaledDeltaResponse {
  sessionId: string
  referenceDriver: string
  results: ScaledDeltaDriverResult[]
  metadata: {
    sessionPart?: string
    driversAnalyzed: number
    driversFailed?: number
    errors?: string[]
  }
}

// =============================================================================
// Phase 3: Corner Analysis Types
// =============================================================================

/** Input for a corner to analyze */
export interface CornerInput {
  cornerNumber: number
  name?: string
  apexDistance: number
  cornerType: 'left' | 'right'
}

/** Cause of time gain/loss at a corner */
export type CornerCause = 'braking' | 'apex' | 'exit' | 'multiple' | 'unknown'

/** Confidence level for corner analysis */
export type CornerConfidence = 'high' | 'medium' | 'low'

/** Result of analyzing a single corner */
export interface CornerResult {
  cornerNumber: number
  name?: string
  apexDistance: number
  brakeDistance: number
  zoneStart: number
  zoneEnd: number
  deltaChange: number  // positive = compare driver slower
  cause: CornerCause
  confidence: CornerConfidence
}

/** Corner analysis result for a single driver comparison */
export interface CornerAnalysisDriverResult {
  compareDriver: string
  cornerResults: CornerResult[]
  totalDeltaChange: number
  cornersGaining: number
  cornersLosing: number
}

/** Request for corner analysis */
export interface CornerAnalysisRequest {
  sessionId: string
  referenceDriver: string
  compareDrivers: string[]
  corners: CornerInput[]
  sessionPart?: string
}

/** Complete response from corner analysis endpoint */
export interface CornerAnalysisResponse {
  sessionId: string
  referenceDriver: string
  results: CornerAnalysisDriverResult[]
  metadata: {
    sessionPart?: string
    driversAnalyzed: number
    cornersAnalyzed: number
    driversFailed?: number
    errors?: string[]
  }
}

// =============================================================================
// Phase 7: Performance Insights Types (Unified Endpoint)
// =============================================================================

/** Request for unified performance insights (orchestrates Phases 2-5) */
export interface PerformanceInsightsRequest {
  session_id: string
  reference_driver: string
  compare_drivers: string[]
  corners: CornerInput[]
  mode?: 'engineer' | 'driver'
  session_part?: string | null
  circuit_name?: string
  include_telemetry?: boolean
}

/** Complete response from performance insights orchestrator */
export interface PerformanceInsightsResponse {
  session_id: string
  reference_driver: string
  circuit_name?: string
  mode: string
  results: DriverPerformanceResult[]
  session_percentiles?: SessionPercentiles
  total_drivers_requested: number
  total_drivers_processed: number
  total_corners: number
  phase_timing: PhaseTimingInfo[]
  total_duration_ms: number
  errors: string[]
  warnings: string[]
}

/** Complete performance analysis for a single driver comparison */
export interface DriverPerformanceResult {
  driver: string
  // Phase 2: Scaled Delta
  official_gap: number
  scaling_confidence: number
  delta?: number[]
  distance?: number[]
  // Phase 3: Corner Analysis Summary
  corners_gaining: number
  corners_losing: number
  total_corner_delta: number
  corner_results: PerformanceCornerResult[]
  // Phase 4: Technique Profile
  technique_profile?: TechniqueProfile
  // Phase 5: Natural Language Insight
  insight?: NaturalLanguageInsight
}

/** Corner result detail for performance insights */
export interface PerformanceCornerResult {
  corner_number: number
  name?: string
  apex_distance: number
  brake_distance: number
  zone_start: number
  zone_end: number
  delta_change: number
  cause: CornerCause
  confidence: CornerConfidence
}

/** Driver technique profile from Phase 4 */
export interface TechniqueProfile {
  driver: string
  reference_driver: string
  braking: TechniqueDimension
  apex: TechniqueDimension
  exit: TechniqueDimension
  consistency: TechniqueDimension
  top_gaining_corners: string[]
  top_losing_corners: string[]
  style_summary: string
  overall_confidence: number
  total_corners_analyzed: number
}

/** Single dimension of technique profile */
export interface TechniqueDimension {
  level: DimensionLevel
  descriptor: string
  percentile: number
  raw_value: number
  corner_count: number
  avg_confidence: number
}

/** Natural language insight from Phase 5 */
export interface NaturalLanguageInsight {
  driver: string
  reference_driver: string
  mode: 'engineer' | 'driver'
  confidence_level: 'high' | 'medium' | 'low' | 'insufficient'
  summary: string
  dimension_insights: DimensionInsightDetail[]
  corner_insights: CornerInsightDetail[]
  opportunity_text: string
  hedging_prefix: string
  total_corners: number
  session_context: Record<string, string>
  style_summary: string
}

/** Dimension insight detail */
export interface DimensionInsightDetail {
  dimension: DimensionType
  level: DimensionLevel
  percentile: number
  text: string
  raw_value_ms: number
  corner_count: number
}

/** Corner insight detail */
export interface CornerInsightDetail {
  corner_name: string
  delta_ms: number
  direction: 'gaining' | 'losing'
  cause: string
  text: string
  confidence: string
}

/** Session percentile boundaries for technique classification */
export interface SessionPercentiles {
  braking_p30: number
  braking_p70: number
  apex_p30: number
  apex_p70: number
  exit_p30: number
  exit_p70: number
  consistency_p30: number
  consistency_p70: number
  driver_count: number
}

/** Timing information for a single phase execution */
export interface PhaseTimingInfo {
  phase: string
  duration_ms: number
  success: boolean
  error?: string
}

// UI Helper Types for Phase 7
export type InsightMode = 'engineer' | 'driver'
export type DimensionType = 'braking' | 'apex' | 'exit' | 'consistency'
export type DimensionLevel = 'strong' | 'neutral' | 'weak'

