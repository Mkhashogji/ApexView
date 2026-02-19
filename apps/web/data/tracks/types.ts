/**
 * Track Intelligence Data Types
 * 
 * These interfaces define the structure for comprehensive track data
 * displayed on the Track Intelligence page. This editorial content
 * supplements the core API track data (sectors, DRS zones, corners).
 */

// =============================================================================
// Circuit Overview
// =============================================================================

export interface CircuitOverview {
  circuitName: string
  country: string
  location: string
  grandPrixName: string
  circuitType: 'Permanent' | 'Street' | 'Semi-Permanent'
  firstGrandPrix: number
  description: string
}

// =============================================================================
// Circuit Statistics
// =============================================================================

export interface LapLength {
  km: number
  miles: number
}

export interface RaceDistance {
  km: number
  miles: number
}

export interface LapRecord {
  time: string
  driver: string | null
  year: number | null
}

export interface TyreSpecs {
  camberLimits: {
    front: string
    rear: string
  }
  minStartingPressures: {
    front: string
    rear: string
  }
}

export interface CircuitStats {
  lapLength: LapLength
  raceDistance: RaceDistance
  numberOfLaps: number
  numberOfCorners: number
  drsZones: number
  lapRecord: LapRecord
  tyreSpecs?: TyreSpecs
}

// =============================================================================
// Circuit Characteristics (Pirelli Ratings)
// =============================================================================

export type CharacteristicRating = 1 | 2 | 3 | 4 | 5

export interface CircuitCharacteristics {
  traction: CharacteristicRating
  tyreStress: CharacteristicRating
  asphaltGrip: CharacteristicRating
  asphaltAbrasion: CharacteristicRating
  braking: CharacteristicRating
  lateral: CharacteristicRating
  downforce: CharacteristicRating
  trackEvolution: CharacteristicRating
}

export type EnergyLevel = 'Minimum' | 'Low' | 'Medium' | 'High' | 'Maximum'

export interface EnergyProfile {
  longitudinal: EnergyLevel
  lateral: EnergyLevel
}

// =============================================================================
// Sector Breakdown
// =============================================================================

export interface SectorBreakdown {
  sector: 1 | 2 | 3
  color: string  // Hex color for visual display
  corners: string  // e.g., "T1-T5"
  description: string
  keyFeatures: string[]
  criticalCorners: string[]
}

// =============================================================================
// DRS Zone Details
// =============================================================================

export interface DRSZoneDetail {
  zone: number
  detectionPoint: string
  activationPoint: string
  deactivationPoint: string
  description: string
  effectiveness: 'Low' | 'Medium' | 'High' | 'Very High'
}

// =============================================================================
// Technical Insights
// =============================================================================

export interface AerodynamicSetup {
  wingLevel: 'Low' | 'Medium-Low' | 'Medium' | 'Medium-High' | 'High' | 'Maximum'
  explanation: string
}

export interface TyreManagement {
  compounds: string[]
  allocation: string
  primaryWearMechanism: string
  explanation: string
  strategicNote?: string
}

export interface SurfaceCharacteristics {
  resurfaced?: number
  impact?: string
  gripLevel: string
}

export interface TechnicalInsights {
  aerodynamicSetup: AerodynamicSetup
  tyreManagement: TyreManagement
  surfaceCharacteristics: SurfaceCharacteristics
}

// =============================================================================
// Overtaking Analysis
// =============================================================================

export interface OvertakingAnalysis {
  difficulty: 'Very Low' | 'Low' | 'Medium' | 'High' | 'Very High'
  primaryZone: string
  secondaryZones: string[]
  factors: string[]
  recommendation: string
}

// =============================================================================
// Weather Profile
// =============================================================================

export interface TypicalWeather {
  conditions: string
  airTemperature: {
    max: string
    min: string
    raceTime: string
  }
  rainProbability: string
  wind: string
  humidity: string
}

export interface SessionConditions {
  fp1?: string
  fp2?: string
  fp3?: string
  sprintQuali?: string
  sprint?: string
  qualifying?: string
  race?: string
}

export interface WeatherProfile {
  typical: TypicalWeather
  sessionConditions: SessionConditions
  impact: string
}

// =============================================================================
// Benchmark Lap Times
// =============================================================================

export interface PolePosition {
  year: number
  time: string
  driver?: string
  session?: string
  note?: string
}

export interface QualifyingPosition {
  position: number
  driver: string
  time: string
}

export interface QualifyingReference {
  year: number
  top5: QualifyingPosition[]
}

export interface SectorBenchmark {
  sector: 1 | 2 | 3
  time: string
  driver: string
}

export interface SectorBenchmarks {
  year: number
  session: string
  sectors: SectorBenchmark[]
  overallIdealLap: string
}

export interface RacePaceGap {
  driver: string
  gap: string
}

export interface RacePaceBenchmark {
  year: number
  fastestDriver: string
  meanLapTime: string
  gaps: RacePaceGap[]
}

export interface TopSpeedReference {
  qualifying: {
    fastest: { driver: string; speed: string }
    range: string
  }
  race: {
    withDRS: string
    withoutDRS: string
  }
}

export interface SprintReference {
  year: number
  sprintPole: {
    driver: string
    time: string
    note?: string
  }
  sprintWinner: {
    driver: string
    team: string
    note?: string
  }
}

export interface BenchmarkLapTimes {
  lapRecord: LapRecord
  polePositions: PolePosition[]
  qualifyingReference: QualifyingReference
  sprintReference?: SprintReference
  sectorBenchmarks: SectorBenchmarks
  racePaceBenchmarks: RacePaceBenchmark[]
  topSpeedReference: TopSpeedReference
}

// =============================================================================
// Strategic Insights
// =============================================================================

export interface PitStopWindow {
  typical: string
  factors: string[]
}

export interface StrategicInsights {
  pitStopWindow: PitStopWindow
  keyStrategicFactors: string[]
  safetyCarLikelihood: string
  historicalNotes: string[]
}

// =============================================================================
// Defining Characteristics
// =============================================================================

export type CharacteristicIcon = 
  | 'tyre'
  | 'overtake'
  | 'aero'
  | 'track'
  | 'strategy'
  | 'braking'
  | 'weather'
  | 'elevation'
  // Abu Dhabi specific icons
  | 'trophy'      // Season Finale
  | 'sliders'     // Setup Flexible
  | 'balanced'    // Complete Track
  | 'twilight'    // Twilight Race
  // Las Vegas specific icons
  | 'aeroLow'     // Lowest Downforce (flat wing profile)
  | 'speed'       // Extreme Top Speed
  | 'evolution'   // Maximum Track Evolution
  | 'night'       // Night Race
  // Mexico specific icons
  | 'gauge'       // Maximum Downforce (gauge/dial icon)
  | 'zap'         // Engine Challenge (lightning bolt for power/cooling)
  // USA specific icons
  | 'rotate'      // Counter-Clockwise Direction
  // Singapore specific icons
  | 'lock'        // Overtaking Difficulty (padlock)
  | 'thermometer' // Extreme Heat
  // Belgium specific icons
  | 'balance'     // Ultimate Aero Compromise (scales/balance icon)
  | 'courage'     // Eau Rouge Test of Courage (mountain/climb icon)
  | 'lateral'     // Lateral Force Maximum (arrows pushing sideways)
  | 'power'       // Power Unit Endurance (engine/power icon)
  // Austria specific icons
  | 'clock'       // Shortest Lap (timer/stopwatch)
  | 'mountain'    // High Altitude (mountain peak)
  | 'route'       // Fewest Corners (simple path)
  | 'flag'        // Overtaking Paradise (checkered flag)
  // Canada specific icons
  | 'wind'           // Low Downforce (airflow)
  | 'arrowLeftRight' // Overtaking Friendly (bidirectional)
  | 'alertTriangle'  // Wall of Champions (warning)
  | 'target'         // Strategy Critical (crosshair)
  | 'cloudRain'      // Weather Variable (rain cloud)
  // China specific icons
  | 'arrow-right'    // Mega Straight (long straight indicator)
  | 'trending-up'    // Track Evolution (grip improvement)
  | 'map'            // Circuit Layout Symbol (shàng character)
  // Australia specific icons
  | 'cloud-rain'     // Weather Lottery (unpredictable Melbourne weather)
  | 'circle'         // Soft Compound Venue (tyre compound indicator)

export interface DefiningCharacteristic {
  tag: string
  icon: CharacteristicIcon
  description: string
}

// =============================================================================
// Complete Track Intelligence Interface
// =============================================================================

export interface TrackIntelligence {
  /** Unique circuit identifier matching API */
  circuitId: string
  
  /** Round number in current season */
  round: number
  
  /** Circuit overview and introduction */
  circuitOverview: CircuitOverview
  
  /** Key statistics (lap length, corners, etc.) */
  circuitStats: CircuitStats
  
  /** Pirelli-style characteristic ratings (1-5) */
  circuitCharacteristics: CircuitCharacteristics
  
  /** Energy demand profile */
  energyProfile: EnergyProfile
  
  /** Detailed breakdown of all three sectors */
  sectors: [SectorBreakdown, SectorBreakdown, SectorBreakdown]
  
  /** DRS zone details with effectiveness */
  drsZones: DRSZoneDetail[]
  
  /** Technical setup insights */
  technicalInsights: TechnicalInsights
  
  /** Overtaking difficulty and zones */
  overtakingAnalysis: OvertakingAnalysis
  
  /** Weather expectations */
  weatherProfile: WeatherProfile
  
  /** Benchmark lap times and pace references */
  benchmarkLapTimes: BenchmarkLapTimes
  
  /** Strategic considerations */
  strategicInsights: StrategicInsights
  
  /** Summary characteristic tags */
  definingCharacteristics: DefiningCharacteristic[]

  /** Fuel effect per kilogram in seconds. Used for race pace fuel correction.
   *  Range: 0.028-0.036 s/kg depending on circuit characteristics. */
  fuelEffectPerKg?: number
}
