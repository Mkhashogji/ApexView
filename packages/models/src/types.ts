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
// Analysis Service Response Types
// ============================================================================

/** Individual insight from telemetry analysis */
export interface AnalysisInsight {
  type: 'similarity' | 'cluster' | 'braking' | 'sector' | 'speed' | 'consistency' | 'error' | 'default'
  message: string
  confidence?: 'high' | 'medium' | 'low'
  drivers?: string[]
  data?: Record<string, unknown>
}

/** Response from /analysis/insights/{session_id} endpoint */
export interface AnalysisInsightsResponse {
  session_id: string
  drivers: string[]
  insights: AnalysisInsight[]
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

/** Response from /analysis/lap-similarity endpoint */
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

/** Response from /analysis/driver-style-clustering endpoint */
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
// Straight-Line Performance Types (5th Dimension)
// =============================================================================

/** Primary factor for straight-line performance */
export type StraightLineFactor = 'aero_efficiency' | 'traction' | 'balanced' | 'drag'

/** Delta information for a straight section between corners */
export interface StraightSegment {
  segment_number: number
  name: string                    // e.g., "T6 → T10"
  start_distance: number          // meters
  end_distance: number            // meters
  delta_change: number            // seconds (positive = comp slower)
  length: number                  // meters
  primary_factor: StraightLineFactor
}

/** Complete breakdown of lap time delta into corners and straights */
export interface LapBreakdown {
  corner_total: number            // Sum of all corner deltas (seconds)
  straight_total: number          // Sum of all straight deltas (seconds)
  official_gap: number            // Official timing gap (seconds)
  track_coverage: number          // Corner distance / track length (0-1)
  straight_segments: StraightSegment[]
  reconciliation_valid: boolean   // corners + straights ≈ official gap
  reconciliation_error: number    // Absolute error (seconds)
  insight_text: string            // Educational explanation
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
  track_length?: number  // Required for lap breakdown (5th dimension)
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
  // Phase 2: Extended fields for ScalingMetadataPanel
  telemetry_gap?: number
  scaling_factor?: number
  raw_delta?: number[]
  // Phase 3: Corner Analysis Summary
  corners_gaining: number
  corners_losing: number
  total_corner_delta: number
  corner_results: PerformanceCornerResult[]
  // 5th Dimension: Lap Breakdown (corners + straights = official)
  lap_breakdown?: LapBreakdown
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

/** Driver technique profile from Phase 4 (now with 5 dimensions) */
export interface TechniqueProfile {
  driver: string
  reference_driver: string
  braking: TechniqueDimension
  apex: TechniqueDimension
  exit: TechniqueDimension
  consistency: TechniqueDimension
  straight_line?: StraightLineDimension  // 5th dimension (optional for backward compatibility)
  top_gaining_corners: string[]
  top_losing_corners: string[]
  style_summary: string
  overall_confidence: number
  total_corners_analyzed: number
}

/** 5th Dimension: Straight-line performance analysis */
export interface StraightLineDimension {
  level: DimensionLevel
  descriptor: string
  percentile: number
  raw_delta: number  // Total straight-line delta in seconds (negative = faster)
  primary_factor: StraightLinePrimaryFactor
  segment_count: number
  top_gaining_straights: string[]
  top_losing_straights: string[]
  avg_confidence: number
}

/** Primary factors explaining straight-line performance */
export type StraightLinePrimaryFactor = 
  | 'aero_efficiency'
  | 'exit_traction'
  | 'high_drag'
  | 'poor_traction'
  | 'balanced'

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

/** Session percentile boundaries for technique classification (including 5th dimension) */
export interface SessionPercentiles {
  braking_p30: number
  braking_p70: number
  apex_p30: number
  apex_p70: number
  exit_p30: number
  exit_p70: number
  consistency_p30: number
  consistency_p70: number
  straight_line_p30?: number  // 5th dimension percentiles
  straight_line_p70?: number
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
export type DimensionType = 'braking' | 'apex' | 'exit' | 'consistency' | 'straight_line'
export type DimensionLevel = 'strong' | 'neutral' | 'weak'

// =============================================================================
// Race Page Types (Phase 1)
// =============================================================================

export type LapClassification =
  | 'RACING'
  | 'IN_LAP'
  | 'OUT_LAP'
  | 'SAFETY_CAR'
  | 'VSC'
  | 'RED_FLAG'
  | 'FORMATION'
  | 'ANOMALY'

export interface RaceLapData {
  lapNumber: number
  driver: string
  team?: string
  position?: number
  lapTime?: number
  sector1Time?: number
  sector2Time?: number
  sector3Time?: number
  compound?: TyreCompound
  tyreLife?: number
  stint?: number
  classification: LapClassification
  isWarmUp: boolean
  fuelCorrectedTime?: number
  inTraffic: boolean
  gapToCarAhead?: number
  isPersonalBest: boolean
  trackStatus?: string
  pitInTime?: number
  pitOutTime?: number
  cumulativeTime?: number
}

export interface RaceStintData {
  driver: string
  team?: string
  stintNumber: number
  compound?: TyreCompound
  startLap: number
  endLap: number
  lapCount: number
}

export interface PitStopData {
  driver: string
  team?: string
  stopNumber: number
  lapNumber: number
  pitLaneTime?: number
  isAnomaly: boolean
}

// =============================================================================
// Race Page Types (Phase 4: Pit Stop Analysis)
// =============================================================================

export interface TeamPitStopAggregate {
  team: string
  averagePitLaneTime: number
  stopCount: number
  consistency: number | null
  consistencyType: 'iqr' | 'range' | null
}

export interface DriverPitStopAggregate {
  driver: string
  team: string
  averagePitLaneTime: number
  stopCount: number
}

export interface GapToFastest {
  team: string
  gapToFastest: number
}

export interface PitStopQuickestInsight {
  team: string
  averageTime: number
  percentageFaster: number
  gridAverage: number
}

export interface PitStopConsistencyInsight {
  team: string
  consistency: number
  consistencyType: 'iqr' | 'range'
}

export interface PitStopInsights {
  quickest: PitStopQuickestInsight | null
  mostConsistent: PitStopConsistencyInsight | null
}

export interface AnomalyNote {
  driver: string
  team: string
  stopNumber: number
  lapNumber: number
  pitLaneTime: number | null
}

export interface PitStopAnalysisResponse {
  stops: PitStopData[]
  teamAggregates: TeamPitStopAggregate[]
  driverAggregates: DriverPitStopAggregate[]
  gapToFastest: GapToFastest[]
  gridAverage: number
  fastestTeam: string | null
  insights: PitStopInsights
  anomalyNotes: AnomalyNote[]
}

export interface DriverPaceData {
  driver: string
  team?: string
  minTime: number
  q1: number
  median: number
  mean: number
  q3: number
  maxTime: number
  outliers: number[]
  gapToFastest: number
  tyreStrategy: string[]
  consistencyScore?: number
  lapsInTraffic: number
  totalRacingLaps: number
  finishingPosition?: number
  status?: string
}

export interface RacePaceResponse {
  sessionId: string
  drivers: DriverPaceData[]
}

// =============================================================================
// Race Page Types (Phase 3: Tyre Degradation)
// =============================================================================

export interface RegressionLineData {
  startX: number
  startY: number
  endX: number
  endY: number
  slope: number
  intercept: number
  rSquared: number
}

export interface DegradationDataPoint {
  tyreAge: number
  fuelAdjustedTime: number
  rawTime: number
  lapNumber: number
  driver: string
  team: string
  stintNumber: number
}

export interface DriverDegradationData {
  identifier: string
  team: string
  dataPoints: DegradationDataPoint[]
  regression: RegressionLineData | null
  wearRate: number | null
  usableLapCount: number
  totalStintLaps: number
  warmUpLapsExcluded: number
}

export interface CompoundDegradation {
  compound: TyreCompound
  drivers: DriverDegradationData[]
}

export interface TyreDegradationResponse {
  sessionId: string
  mode: 'driver' | 'team'
  compounds: CompoundDegradation[]
  compoundOrder: string[]
}

// =============================================================================
// Race Page Types (Phase 5: Team Performance Quadrant)
// =============================================================================

export interface TeamPerformanceData {
  team: string
  topSpeed: number                    // km/h (mean of SpeedST)
  meanSpeed: number                   // km/h (track_length / fuel_corrected_time * 3.6)
  topSpeedDelta: number               // km/h vs field average
  meanSpeedDelta: number              // km/h vs field average
}

export interface TeamPerformanceFieldAverages {
  topSpeed: number
  meanSpeed: number
}

export interface TeamPerfInsightEntry {
  team: string
  value: number
  delta: number
}

export interface TeamPerformanceInsights {
  fastestOnStraights: TeamPerfInsightEntry | null
  highestMeanSpeed: TeamPerfInsightEntry | null
}

export interface TeamPerformanceResponse {
  sessionId: string
  teams: TeamPerformanceData[]
  fieldAverages: TeamPerformanceFieldAverages
  insights: TeamPerformanceInsights
}


// =============================================================================
// Practice Page Types (Phase 1: Long Run Pace)
// =============================================================================

export type PracticeLapClassification =
  | 'RACING'
  | 'IN_LAP'
  | 'OUT_LAP'
  | 'RED_FLAG'
  | 'ANOMALY'

export interface PracticeStintStats {
  lowerfence: number
  q1: number
  median: number
  q3: number
  upperfence: number
  mean: number
  stdDev: number
}

export interface PracticeLapPoint {
  lapNumber: number
  lapTime: number
  compound?: string
  tyreLife?: number
  inTraffic: boolean
}

export interface PracticeLongRunStint {
  driver: string
  team?: string
  stintNumber: number
  displayStintNumber: number
  compound?: string
  validLapCount: number
  totalLapCount: number
  stats: PracticeStintStats
  averageTime: number
  gapToFastest: number
  degradationHint?: number | null
  cleanAirPct: number
  lapTimes: PracticeLapPoint[]
}

export interface PracticeLongRunResponse {
  sessionId: string
  fuelCorrected: boolean
  stints: PracticeLongRunStint[]
  sessionBestAverage?: number | null
  totalLongRunsDetected: number
  stintsFilteredCount: number
}

export interface PracticeSessionsResponse {
  year: number
  roundNum: number
  sessions: string[]
}

// =============================================================================
// Practice Page Types (Phase 2: Short Run / Best Lap)
// =============================================================================

export interface PracticeShortRunDriver {
  driver: string
  team: string
  bestLapTime: number
  compound: string
  tyreLife: number
  gapToP1: number
  stintCount: number
  position: number
  // Session verification (null when unavailable)
  sessionBestTime: number | null
  sessionBestSource: string | null // 'fastf1_flag' | 'computed_minimum'
  sessionBestFromShortRun: boolean | null
  sessionBestCompound: string | null
}

export interface PracticeShortRunResponse {
  sessionId: string
  fuelCorrected: boolean
  drivers: PracticeShortRunDriver[]
  sessionBestLap: number | null
  totalDrivers: number
  verificationAvailable: boolean
}

// =============================================================================
// Practice Page Types (Sector Analysis)
// =============================================================================

export interface PracticeSectorDriver {
  driver: string
  team: string
  position: number
  lapTime: number
  sector1: number | null
  sector2: number | null
  sector3: number | null
  bestSector1: number | null
  bestSector2: number | null
  bestSector3: number | null
  theoreticalBest: number | null
  potentialGain: number | null
  compound: string | null
}

export interface PracticeSectorSummary {
  fastestSector1: number | null
  fastestSector1Driver: string | null
  fastestSector2: number | null
  fastestSector2Driver: string | null
  fastestSector3: number | null
  fastestSector3Driver: string | null
  theoreticalBestTime: number | null
  actualBestTime: number | null
  theoreticalGain: number | null
}

export interface PracticeSpeedTrapDriver {
  driver: string
  team: string
  speedTrap: number | null
  speedI1: number | null
  speedI2: number | null
  speedFl: number | null
}

export interface PracticeSectorAnalysisResponse {
  sessionId: string
  drivers: PracticeSectorDriver[]
  summary: PracticeSectorSummary
  speedTraps: PracticeSpeedTrapDriver[]
  totalDrivers: number
}

// =============================================================================
// Practice Page Types (Phase 3: Session Progression)
// =============================================================================

export interface PracticeProgressionEntry {
  session: string                 // 'FP1' | 'FP2' | 'FP3'
  bestLapTime: number             // Raw lap time in seconds
  compound: string                // Tyre compound
  tyreLife: number                // Tyre age at best lap
  gapToSessionBest: number        // Seconds behind session P1 (0 for P1)
  source: string                  // 'fastf1_flag' | 'computed_minimum'
}

export interface PracticeProgressionDriver {
  driver: string                  // 3-letter abbreviation
  team: string                    // Full team name
  sessions: PracticeProgressionEntry[]  // 1–3 entries
}

export interface PracticeProgressionResponse {
  year: number
  roundNum: number
  availableSessions: string[]     // e.g. ['FP1', 'FP2', 'FP3']
  isSprintWeekend: boolean
  drivers: PracticeProgressionDriver[]
  totalDrivers: number
}

