import type { TrackIntelligence } from './types'

/**
 * United States Grand Prix - Circuit of the Americas (COTA)
 * Round 19 of the 2025 FIA Formula 1 World Championship
 * 
 * The first purpose-built Formula 1 circuit in the United States (2012). COTA features
 * the iconic 133-foot climb to Turn 1 and a Silverstone-inspired Esses section. The
 * counter-clockwise direction creates asymmetric tyre wear patterns.
 */
export const usaTrackIntelligence: TrackIntelligence = {
  circuitId: 'americas',
  round: 19,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit of the Americas',
    country: 'United States',
    location: 'Austin, Texas, USA',
    grandPrixName: 'United States Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 2012,
    description:
      'The Circuit of the Americas (COTA) is the first purpose-built Formula 1 circuit in the United States, opening in 2012. Designed by Hermann Tilke with input from MotoGP legend Kevin Schwantz, the track incorporates iconic corner concepts from circuits worldwide — Silverstone\'s Maggotts-Becketts complex inspires the flowing Esses (T2-T6), while Istanbul Park\'s famous Turn 8 influenced COTA\'s multi-apex corner. The circuit features a dramatic 133-foot (41m) elevation climb to Turn 1, creating one of the most spectacular braking zones on the calendar. The counter-clockwise direction is unusual for F1 and creates asymmetric physical demands on drivers. Texas October heat regularly pushes track temperatures above 45°C, challenging both machinery and drivers.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.513,
      miles: 3.426,
    },
    raceDistance: {
      km: 308.728,
      miles: 191.856,
    },
    numberOfLaps: 56,
    numberOfCorners: 20,
    drsZones: 2,
    lapRecord: {
      time: '1:36.169',
      driver: 'Charles Leclerc',
      year: 2019,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '24.0 psi',
        rear: '22.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,
    tyreStress: 4,
    asphaltGrip: 3,
    asphaltAbrasion: 3,
    braking: 3,
    lateral: 4,              // High lateral forces through Esses
    downforce: 4,            // Medium-High downforce required
    trackEvolution: 4,       // High evolution in Texas heat
  },

  energyProfile: {
    longitudinal: 'Medium',
    lateral: 'High',
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000',  // Red
      corners: 'T1-T6',
      description:
        'Opens with the dramatic 133-foot elevation climb to Turn 1 — one of F1\'s most spectacular braking zones. After the hairpin, drivers navigate "The Snake" (T2-T6), a series of fast, flowing corners inspired by Silverstone\'s Maggotts-Becketts complex. Rhythm and commitment are essential; lifting costs significant lap time.',
      keyFeatures: [
        'Heavy braking uphill into T1 from 320+ km/h',
        '"The Snake" Esses (T2-T6) — Silverstone-inspired',
        'Trail braking technique essential',
        'High-speed stability critical',
        'Primary overtaking zone at T1',
      ],
      criticalCorners: [
        'T1 - 133ft climb, heavy braking, key overtaking zone',
        'T2-T6 - Fast flowing Esses requiring commitment and rhythm',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T7-T11',
      description:
        'Continues the flowing character with the multi-apex Turn 8 (inspired by Istanbul\'s famous corner), then transitions to the tight T11 hairpin. The exit of T11 is crucial — it sets up the longest straight and the main DRS-assisted overtaking opportunity into T12.',
      keyFeatures: [
        'Multi-apex T8 inspired by Istanbul Park',
        'T11 hairpin exit critical for straight-line speed',
        'Sets up main DRS straight',
        'Battery deployment strategy important',
        'Slow-speed traction out of T11 essential',
      ],
      criticalCorners: [
        'T8 - Multi-apex requiring commitment',
        'T11 - Hairpin, exit speed crucial for DRS straight',
      ],
    },
    {
      sector: 3,
      color: '#FFFF00',  // Yellow
      corners: 'T12-T20',
      description:
        'The tyre-killing sector. Heavy braking into T12 hairpin after the DRS straight, followed by a technical complex including the 180-degree extended left-hander (T15-T16) that significantly raises tyre temperatures. Very difficult to follow in dirty air. Exit of T20 crucial for main straight.',
      keyFeatures: [
        'Secondary DRS braking zone at T12',
        '180° T15-T16 complex raises tyre temps',
        'Extremely difficult to follow in dirty air',
        'Tyre management critical',
        'T20 exit determines main straight speed',
      ],
      criticalCorners: [
        'T12 - Heavy braking, secondary overtaking zone',
        'T15-T16 - Extended 180° left-hander, tyre killer',
        'T20 - Final corner, exit speed critical',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'After Turn 20',
      activationPoint: 'Start of main straight',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'The primary DRS zone along the main straight leading into Turn 1. Combined with the dramatic uphill braking zone, this creates the best overtaking opportunity on the circuit. Cars arrive at 320+ km/h before heavy braking.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 11',
      activationPoint: 'Start of back straight',
      deactivationPoint: 'Turn 12 braking zone',
      description:
        'The longer of the two straights leads into the T12 hairpin. Heavy braking combined with DRS creates strong overtaking opportunities. Exit of T11 is critical for maximizing speed advantage.',
      effectiveness: 'Very High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'High',
      explanation:
        'COTA requires medium-high to high downforce despite two long DRS straights. The fast corners through the Esses (T2-T6) and the demanding Sector 3 complex require substantial downforce. Red Bull, Mercedes, and McLaren all ran very loaded wings in 2025, prioritizing Sector 3 performance. Williams and Racing Bulls opted for slightly lower drag. Aston Martin notably ran split strategies with Alonso on lower drag and Stroll on higher downforce (5 km/h difference).',
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C3 (Medium)', 'C4 (Soft)'],
      allocation: '2-step gap between Hard and Medium',
      primaryWearMechanism: 'Thermal degradation from high lateral loads and Texas heat',
      explanation:
        'The 2-step gap between compounds (C1 to C3) proved problematic in 2025. The Hard (C1) was too hard for conditions — only 3 total stints used it all weekend. Medium and Soft showed similar degradation profiles with approximately 30-lap life. Track temperatures exceeded 46°C during the race, accelerating thermal degradation.',
      strategicNote: 'One-stop with Medium-Soft or Soft-Medium optimal. Avoid the Hard compound.',
    },
    surfaceCharacteristics: {
      resurfaced: 2022,
      impact: 'Good grip levels with significant evolution in Texas heat',
      gripLevel: 'Medium grip with high track evolution throughout sessions',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (uphill braking from main straight with DRS Zone 1)',
    secondaryZones: ['Turn 12 (DRS Zone 2 into hairpin)', 'Turn 1 late braking'],
    factors: [
      'Two effective DRS zones create genuine passing opportunities',
      'Dramatic uphill braking into T1 rewards brave late-braking',
      'T12 hairpin provides secondary overtaking chance',
      'Dirty air impact severe in Sector 3 technical complex',
      'Track position important due to dirty air in Esses',
      'Counter-clockwise direction affects overtaking dynamics',
    ],
    recommendation:
      'Overtaking is achievable at COTA primarily at T1 and T12. The uphill braking into Turn 1 rewards committed late-braking but increases lock-up risk. Defending through the Esses is effective due to severe dirty air impact on following cars. Focus on strong T11 and T20 exits to maximize DRS advantage.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot, sunny, low humidity',
      airTemperature: {
        max: '32°C',
        min: '18°C',
        raceTime: '28-30°C',
      },
      rainProbability: 'Low (20% chance in October)',
      wind: 'Light to moderate',
      humidity: 'Low to moderate',
    },
    sessionConditions: {
      fp1: '28°C, sunny',
      sprintQuali: '30°C, sunny',
      sprint: '29°C, sunny',
      fp2: '27°C, partly cloudy',
      qualifying: '28°C, sunny',
      race: '30°C, sunny, 46°C track temp',
    },
    impact:
      'Texas October heat creates extreme conditions for both drivers and machinery. Track temperatures regularly exceed 45°C, requiring additional driver cooling systems. The heat affects tyre compound selection — the Hard (C1) was too hard to generate temperature in 2025. Engine and brake cooling become critical. Rain is rare but possible.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:36.169',
      driver: 'Charles Leclerc',
      year: 2019,
    },
    polePositions: [
      {
        year: 2019,
        time: '1:32.029',
        driver: 'BOT',
        note: 'Track record',
      },
      {
        year: 2023,
        time: '1:34.723',
        driver: 'LEC',
      },
      {
        year: 2024,
        time: '1:32.330',
        driver: 'NOR',
      },
      {
        year: 2025,
        time: '1:32.510',
        driver: 'VER',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:32.510' },
        { position: 2, driver: 'NOR', time: '1:32.801' },
        { position: 3, driver: 'LEC', time: '1:32.807' },
        { position: 4, driver: 'RUS', time: '1:32.826' },
        { position: 5, driver: 'HAM', time: '1:32.912' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '24.891s', driver: 'VER' },
        { sector: 2, time: '37.134s', driver: 'NOR' },
        { sector: 3, time: '30.093s', driver: 'VER' },
      ],
      overallIdealLap: '1:32.118',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '99.21s',
        gaps: [
          { driver: 'NOR', gap: '+0.08s' },
          { driver: 'LEC', gap: '+0.24s' },
          { driver: 'HAM', gap: '+0.42s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'LEC',
        meanLapTime: '98.94s',
        gaps: [
          { driver: 'SAI', gap: '+0.18s' },
          { driver: 'NOR', gap: '+0.26s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'ANT', speed: '329 km/h' },
        range: '321-329 km/h',
      },
      race: {
        withDRS: 'Up to 342 km/h (Stroll)',
        withoutDRS: '310-313 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop strategy dominant',
      factors: [
        'Medium and Soft show similar degradation (~30 lap life)',
        'Hard compound (C1) too hard for conditions — avoid',
        'Pit lane time loss approximately 21.5 seconds',
        'Undercut effective: 1.5-2.0 seconds per lap on fresh tyres',
        'VSC/SC probability moderate (VSC deployed Lap 7 in 2025)',
        'Track position premium due to dirty air in Sector 3',
      ],
    },
    keyStrategicFactors: [
      'One-stop on Medium-Soft or Soft-Medium optimal',
      'Hard (C1) ineffective — only 3 stints used all weekend',
      'Track temperature critical — exceeded 46°C in 2025 race',
      'T11 exit crucial for defensive racing into T12',
      'Late pit for fastest lap viable (Antonelli Lap 33)',
      'Sprint format affects tyre allocation for race',
    ],
    safetyCarLikelihood: 'Moderate - permanent circuit with run-off but incidents possible',
    historicalNotes: [
      '2025: VER wins (+7.959s), Antonelli fastest lap 1:37.577 (Lap 33)',
      '2025 Sprint: McLaren double DNF (Piastri-Norris collision T1), Sainz P3 for Williams',
      '2024: Leclerc wins for Ferrari',
      '2019: Bottas sets track record 1:32.029; Leclerc sets lap record 1:36.169',
      '2018: Räikkönen ends 113-race win drought',
      '2012: Hamilton wins inaugural race',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Complete Test',
      icon: 'balanced',
      description: 'All-rounder circuit testing straights, fast corners, slow corners, and elevation — exposes any car weakness',
    },
    {
      tag: 'Extreme Heat',
      icon: 'weather',
      description: 'Texas October heat pushes track temps above 45°C, challenging drivers and machinery',
    },
    {
      tag: 'American F1 Home',
      icon: 'trophy',
      description: 'First purpose-built F1 circuit in USA (2012), FIA Grade 1 facility designed by Tilke',
    },
    {
      tag: 'Counter-Clockwise',
      icon: 'rotate',
      description: 'Unusual anti-clockwise direction creates asymmetric tyre wear and physical demands',
    },
    {
      tag: 'Elevation Drama',
      icon: 'elevation',
      description: '133-foot (41m) climb to Turn 1 creates spectacular uphill braking zone',
    },
  ],
}

