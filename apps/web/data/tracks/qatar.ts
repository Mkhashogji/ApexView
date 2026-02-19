import type { TrackIntelligence } from './types'

/**
 * Qatar Grand Prix - Lusail International Circuit
 * Round 23 of the 2025 FIA Formula 1 World Championship
 * 
 * A tyre-critical circuit characterized by consecutive medium-speed corners
 * with minimal straights for cooling. Demands exceptional lateral load management.
 */
export const qatarTrackIntelligence: TrackIntelligence = {
  circuitId: 'lusail',
  round: 23,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Lusail International Circuit',
    country: 'Qatar',
    location: 'Lusail, Qatar',
    grandPrixName: 'Qatar Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 2021,
    description:
      'The Lusail International Circuit is a flowing permanent track characterized by many consecutive medium-speed corners with minimal straights for tyre cooling. Resurfaced in 2023, the circuit became over 2.7 seconds per lap faster, dramatically increasing tyre stress. Known as a "tyre-shredding track," Qatar demands exceptional lateral load management and punishes cars that struggle with sustained cornering. Overtaking is limited to a single DRS zone, making qualifying position and tyre strategy critical to race success.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.419,
      miles: 3.367,
    },
    raceDistance: {
      km: 308.611,
      miles: 191.702,
    },
    numberOfLaps: 57,
    numberOfCorners: 16,
    drsZones: 1,
    lapRecord: {
      time: '1:22.384',
      driver: 'Lando Norris',
      year: 2024,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-2.75°',
        rear: '-1.50°',
      },
      minStartingPressures: {
        front: '28.0 psi',
        rear: '23.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,
    tyreStress: 5,       // Maximum - critical characteristic
    asphaltGrip: 4,
    asphaltAbrasion: 2,
    braking: 3,
    lateral: 5,          // Maximum - defining trait of Qatar
    downforce: 4,
    trackEvolution: 4,
  },

  energyProfile: {
    longitudinal: 'Minimum',  // Low traction/braking demands
    lateral: 'Maximum',       // Extreme lateral forces
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000',  // Red
      corners: 'T1-T5',
      description:
        'Contains the end of the only DRS zone with strong braking into Turn 1. Features two medium-speed corners leading to a short straight, followed by two more medium-speed corners. Character similar to Bahrain Sector 1.',
      keyFeatures: [
        'Primary overtaking zone at T1',
        'Heavy braking into T1',
        'Medium-speed corner sequence',
        'DRS zone termination point',
      ],
      criticalCorners: [
        'T1 - Heavy braking zone',
        'T4-T5 - Medium-speed complex',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T6-T10',
      description:
        'The slowest section of the circuit featuring a slow corner at Turn 6 followed by several consecutive medium-speed corners. Turn 10 leads to a short full-throttle section.',
      keyFeatures: [
        'Slowest sector',
        'Technical corner sequence',
        'Mechanical grip dependent',
        'Short acceleration zone after T10',
      ],
      criticalCorners: [
        'T6 - Slowest corner',
        'T10 - Exit onto short straight',
      ],
    },
    {
      sector: 3,
      color: '#FFD700',  // Yellow/Gold
      corners: 'T11-T16',
      description:
        'Contains the fastest non-full-throttle corners (T12-T14). High-speed sections contribute less to overall lap time but cause significant tyre wear due to sustained lateral loads. Includes a short straight and the beginning of the main straight.',
      keyFeatures: [
        'Highest speed corners',
        'Maximum tyre stress zone',
        'Critical for tyre preservation',
        'Leads onto main straight',
      ],
      criticalCorners: [
        'T12-T14 - High-speed complex (tyre critical)',
        'T16 - Final corner onto main straight',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Before T16',
      activationPoint: 'Main straight',
      deactivationPoint: 'T1 braking zone',
      description:
        'Single DRS zone on the main straight. Medium-high downforce wings make DRS effect stronger than typical, similar to Zandvoort. Primary and only realistic overtaking opportunity.',
      effectiveness: 'High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium-High',
      explanation:
        'Teams run medium-high load wings. Maximum downforce configurations create excessive drag on the main straight and make overtaking nearly impossible. The compromise between corner performance and straight-line speed is critical.',
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C2 (Medium)', 'C3 (Soft)'],
      allocation: 'Hardest available',
      primaryWearMechanism: 'Lateral forces',
      explanation:
        'Tyre wear is dominated by sustained high lateral forces through consecutive corners, not longitudinal (traction/braking) forces. No significant straights exist for tyre cooling. Following another car in dirty air dramatically increases tyre temperature and accelerates degradation.',
      strategicNote: 'Overtake quickly, or your stint is ruined.',
    },
    surfaceCharacteristics: {
      resurfaced: 2023,
      impact: 'Over 2.7 seconds per lap faster than previous surface',
      gripLevel: 'High initial grip with high abrasion',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'High',
    primaryZone: 'Turn 1 (end of main straight)',
    secondaryZones: [],
    factors: [
      'Only one DRS-assisted straight limits passing opportunities',
      'Medium-high downforce wings enhance DRS effectiveness',
      'Following in dirty air severely increases tyre degradation',
      'Track position is crucial - being stuck behind costs tyre life',
      'Strategic undercuts often more effective than on-track passes',
    ],
    recommendation:
      'Qualifying position and pit strategy are more important than raw race pace for achieving results.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Sunny and dry',
      airTemperature: {
        max: '28°C',
        min: '19°C',
        raceTime: '21-22°C',
      },
      rainProbability: '0% (virtually no rain expected)',
      wind: 'Light northerly winds',
      humidity: 'Low to moderate',
    },
    sessionConditions: {
      fp1: '26-25°C, light-moderate northerly wind',
      sprintQuali: '22°C, light-moderate northerly wind',
      sprint: '25°C, light northerly wind',
      qualifying: '21°C, light northerly wind',
      race: '22-21°C, light north-to-northeast wind',
    },
    impact:
      'Consistent conditions throughout weekend allow for reliable setup optimization. Cooler evening temperatures for qualifying and race reduce tyre stress slightly compared to practice sessions.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:22.384',
      driver: null,
      year: null,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:23.778',
        note: 'Pre-resurface',
      },
      {
        year: 2024,
        time: '1:21.012',
        session: 'Sprint Qualifying',
        note: 'Post-resurface',
      },
      {
        year: 2025,
        time: '1:19.387',
        driver: 'PIA',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:19.387' },
        { position: 2, driver: 'NOR', time: '1:19.495' },
        { position: 3, driver: 'VER', time: '1:19.651' },
        { position: 4, driver: 'RUS', time: '1:19.662' },
        { position: 5, driver: 'ANT', time: '1:19.846' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Sprint Qualifying',
      sectors: [
        { sector: 1, time: '29.403s', driver: 'RUS' },
        { sector: 2, time: '27.074s', driver: 'PIA' },
        { sector: 3, time: '23.423s', driver: 'PIA' },
      ],
      overallIdealLap: '1:19.900',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'PIA',
        meanLapTime: '84.90s',
        gaps: [
          { driver: 'NOR', gap: '+0.34s' },
          { driver: 'VER', gap: '+0.40s' },
          { driver: 'SAI', gap: '+0.86s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '84.62s',
        gaps: [
          { driver: 'NOR', gap: '+0.15s' },
          { driver: 'LEC', gap: '+0.35s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'VER', speed: '330 km/h' },
        range: '324-330 km/h',
      },
      race: {
        withDRS: 'Up to 345 km/h (in traffic)',
        withoutDRS: '314-316 km/h (frontrunners)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop strategy standard',
      factors: [
        'High tyre degradation necessitates multiple stops',
        'Safety Car timing can dramatically alter optimal strategy',
        'Early SC can enable single-stop if timed correctly',
      ],
    },
    keyStrategicFactors: [
      'Qualifying position critical due to limited overtaking',
      'Tyre management more important than raw pace',
      'Undercut potential is high given tyre sensitivity',
      'Pit lane congestion during Safety Car costs significant time',
      'Track position > pure speed at this circuit',
    ],
    safetyCarLikelihood: 'Moderate - tight corners and barriers',
    historicalNotes: [
      '2025: SC on Lap 7 triggered strategic divergence',
      'Teams staying out during SC lost significant track position',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Tyre Critical',
      icon: 'tyre',
      description: 'Maximum tyre stress circuit - lateral forces destroy tyres',
    },
    {
      tag: 'Limited Overtaking',
      icon: 'overtake',
      description: 'Single DRS zone makes qualifying position crucial',
    },
    {
      tag: 'Medium-High Downforce',
      icon: 'aero',
      description: 'Balanced setup between corner speed and straight-line pace',
    },
    {
      tag: 'Flowing Layout',
      icon: 'track',
      description: 'Consecutive medium-speed corners with no cooling straights',
    },
    {
      tag: 'Strategy Dependent',
      icon: 'strategy',
      description: 'Pit timing and tyre choice often decide results',
    },
  ],

  fuelEffectPerKg: 0.032,
}
