import type { TrackIntelligence } from './types'

/**
 * Las Vegas Grand Prix - Las Vegas Strip Circuit
 * Round 22 of the 2025 FIA Formula 1 World Championship
 * 
 * A unique high-speed street circuit that winds through one of the world's most iconic
 * entertainment districts. Unlike any other city circuit on the calendar, Las Vegas demands
 * extreme drag reduction due to its insanely long full-throttle sections.
 */
export const lasVegasTrackIntelligence: TrackIntelligence = {
  circuitId: 'las_vegas',
  round: 22,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Las Vegas Strip Circuit',
    country: 'United States',
    location: 'Paradise, Nevada, USA',
    grandPrixName: 'Las Vegas Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 2023,
    description:
      'The Las Vegas Strip Circuit is a unique, high-speed street circuit that winds through one of the world\'s most iconic entertainment districts. Unlike any other city circuit on the calendar, Las Vegas demands extreme drag reduction due to its insanely long full-throttle sections — no other street track requires this level of low-downforce configuration. The track\'s relatively high altitude (660m) further reduces air density, making downforce even scarcer while enabling some of the highest top speeds of the season. The circuit combines spectacular high-speed straights along the famous Strip with technical slow-speed sections, creating a unique challenge where braking stability on cold tyres becomes critical after the long straights.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 6.201,
      miles: 3.853,
    },
    raceDistance: {
      km: 309.958,
      miles: 192.650,
    },
    numberOfLaps: 50,
    numberOfCorners: 17,
    drsZones: 2,
    lapRecord: {
      time: '1:34.876',
      driver: 'Lando Norris',
      year: 2024,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '28.0 psi',
        rear: '26.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 2,
    tyreStress: 4,
    asphaltGrip: 1,        // Low initial grip on street surface
    asphaltAbrasion: 2,
    braking: 3,            // Heavy braking zones after long straights
    lateral: 2,            // Low lateral loads
    downforce: 1,          // MINIMUM - unique among city circuits
    trackEvolution: 5,     // MAXIMUM - street surface improves dramatically
  },

  energyProfile: {
    longitudinal: 'Low',      // Low traction/braking demand overall
    lateral: 'Low',           // Minimal lateral forces
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
        'Opens with a slow left-hander (Turn 1) leading into a much faster right-hander. Contains the shorter of the two DRS straights. Balance between cornering and straight-line speed is critical. Braking stability into Turn 1 is challenging due to cold tyres coming off the main straight.',
      keyFeatures: [
        'First DRS zone location',
        'Mixed character sector',
        'Critical T1 braking zone',
        'Cold tyre management essential',
      ],
      criticalCorners: [
        'T1 - Slow left-hander, challenging on cold tyres',
        'T5 - Right-hander leading to DRS zone',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T6-T13',
      description:
        'The slowest sector, featuring several consecutive slow corners. However, remains relatively quick for a city circuit. Contains a full-throttle section from Turn 9 to Turn 11. The technical nature rewards precise car placement and good traction. Teams running more downforce can gain time here but sacrifice it on the straights.',
      keyFeatures: [
        'Slowest sector overall',
        'Technical corner sequence',
        'Full-throttle T9-T11 section',
        'Downforce trade-off zone',
      ],
      criticalCorners: [
        'T6-T7 - Technical complex requiring precision',
        'T12-T13 - Exit onto Sector 3 straight',
      ],
    },
    {
      sector: 3,
      color: '#FFFF00',  // Yellow
      corners: 'T14-T17',
      description:
        'The fastest sector by far, featuring two very long straights — the first with DRS — separated by a slow chicane (Turns 14-16). This is the primary overtaking zone. The DRS straight runs along the iconic Las Vegas Strip, passing the Bellagio, Paris, and Caesars Palace. Top speeds exceeding 360 km/h are achievable with DRS and slipstream.',
      keyFeatures: [
        'Primary overtaking zone',
        'Main DRS straight along the Strip',
        'Top speeds over 360 km/h possible',
        'Iconic casino landmarks',
      ],
      criticalCorners: [
        'T14 - Heavy braking from Strip straight',
        'T14-T16 - Slow chicane complex',
        'T17 - Final corner onto main straight',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'After Turn 5',
      activationPoint: 'Before Turn 6 chicane',
      deactivationPoint: 'Turn 6 braking zone',
      description:
        'The shorter of the two DRS zones, located in Sector 1. Provides a speed advantage but the following chicane makes completing passes difficult. Often used to set up moves for the main straight.',
      effectiveness: 'Medium',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 13',
      activationPoint: 'Start of Strip straight',
      deactivationPoint: 'Turn 14 braking zone',
      description:
        'The primary overtaking zone running along the iconic Las Vegas Strip. This 1.9 km straight combined with heavy braking into Turn 14 creates the best passing opportunity on the circuit. Top speeds exceeding 360 km/h achievable with DRS and slipstream.',
      effectiveness: 'Very High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Low',
      explanation:
        'Las Vegas requires the lowest downforce configuration of any city circuit on the calendar. Teams ran practically horizontal lower wing planes in 2025 to maximize straight-line speed. Ferrari and Sauber opted for extreme low drag, while McLaren and Red Bull used a V-shaped lower plane retaining some downforce. Mercedes ran higher load for better braking stability. The 11 km/h top speed spread across the field demonstrated multiple viable setup philosophies.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard mid-range compounds',
      primaryWearMechanism: 'Thermal cycling from cold straights to slow corners',
      explanation:
        'Tyre management at Las Vegas is unique due to thermal cycling — tyres cool significantly on the long straights then heat rapidly in the slow sections. Hard tyres significantly outperformed Mediums by approximately 0.5s/lap in 2025. Antonelli completed 48 laps on a single Hard set recovering P17 to P3, demonstrating excellent durability.',
      strategicNote: 'One-stop strategies are standard. Hards are the optimal race tyre.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Very low initial grip with massive evolution',
      impact: 'Street surface has minimal rubber initially. Track evolution is the highest on the calendar — expect major lap time improvements throughout the weekend.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Low',
    primaryZone: 'Turn 14 (end of Strip straight with DRS Zone 2)',
    secondaryZones: ['Turn 6 (DRS Zone 1)', 'Turn 1 (off main straight)'],
    factors: [
      'Two effective DRS zones provide multiple passing opportunities',
      '1.9 km Strip straight creates massive speed differentials',
      'Heavy braking into T14 is the primary overtaking spot',
      'DRS trains can form but are less problematic than at other circuits',
      'Low-grip surface makes defending difficult',
      'Qualifying position less critical than at most street circuits',
    ],
    recommendation:
      'Overtaking is very achievable at Las Vegas. The combination of two DRS zones and extremely long straights makes this one of the best circuits for racing action. Focus on optimizing straight-line speed.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Cold, dry, desert night',
      airTemperature: {
        max: '17°C',
        min: '8°C',
        raceTime: '12-14°C',
      },
      rainProbability: 'Low but possible (40% in 2025 qualifying)',
      wind: 'Light to moderate',
      humidity: 'Low (desert climate)',
    },
    sessionConditions: {
      fp1: '14°C, partly cloudy',
      fp2: '12°C, cloudy (red flag for drain cover issue)',
      fp3: '14°C, rain',
      qualifying: '12°C, wet throughout',
      race: '14°C, dry, clear skies',
    },
    impact:
      'Las Vegas is the coldest race weekend on the calendar. The night race format means track temperature drops significantly. Cold tyres after long straights create braking challenges. 2025 qualifying was held in wet conditions — rare for Las Vegas — producing times approximately 15 seconds slower than dry conditions.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:34.876',
      driver: 'Lando Norris',
      year: 2024,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:32.726',
        driver: 'LEC',
      },
      {
        year: 2024,
        time: '1:32.312',
        driver: 'RUS',
        note: 'Track record',
      },
      {
        year: 2025,
        time: '1:47.934',
        driver: 'NOR',
        note: 'Wet conditions',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:47.934' },
        { position: 2, driver: 'VER', time: '1:48.257' },
        { position: 3, driver: 'SAI', time: '1:48.296' },
        { position: 4, driver: 'RUS', time: '1:48.803' },
        { position: 5, driver: 'PIA', time: '1:48.961' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '26.258s', driver: 'RUS' },
        { sector: 2, time: '31.225s', driver: 'NOR' },
        { sector: 3, time: '35.817s', driver: 'HUL' },
      ],
      overallIdealLap: '1:33.300',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '95.21s',
        gaps: [
          { driver: 'NOR', gap: '+0.38s' },
          { driver: 'PIA', gap: '+0.46s' },
          { driver: 'LEC', gap: '+0.47s' },
          { driver: 'ANT', gap: '+0.49s' },
          { driver: 'RUS', gap: '+0.50s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'RUS',
        meanLapTime: '97.52s',
        gaps: [
          { driver: 'HAM', gap: '+0.02s' },
          { driver: 'SAI', gap: '+0.15s' },
          { driver: 'LEC', gap: '+0.18s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'LAW', speed: '318 km/h' },
        range: '184-318 km/h (Spread due to Extreme wet conditions and varying tire choices)',
      },
      race: {
        withDRS: 'Up to 364 km/h (BEA & HAM in traffic)',
        withoutDRS: '340 km/h (VER - led entire race without using DRS)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop strategy standard',
      factors: [
        'Hard tyres showed excellent durability (40+ laps possible)',
        'Minimal degradation enables long stints',
        'Pit lane time loss approximately 21-22 seconds',
        'Undercut potential moderate due to track evolution',
        'One-stop on Hards is optimal for most conditions',
      ],
    },
    keyStrategicFactors: [
      'Qualifying position less critical than most tracks — overtaking is possible',
      'Hards significantly outperform Mediums (~0.5s/lap advantage)',
      'Single-stop strategies viable with minimal degradation',
      'Cold tyre braking critical — balance drag reduction against stability',
      'Track evolution massive — cars improve significantly as rubber builds',
      'Skid plate wear can be problematic on low-grip surface',
    ],
    safetyCarLikelihood: 'Moderate - street circuit with barriers',
    historicalNotes: [
      '2025: Both McLaren cars DSQ for excessive skid plate wear',
      '2025: Antonelli recovered P17→P3 on single set of Hards (48 laps)',
      '2025: VER led every lap, never used DRS',
      '2024: Russell won after leading 49 of 50 laps',
      '2023: Verstappen won inaugural race',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Lowest Downforce',
      icon: 'aeroLow',
      description: 'Minimum wing levels — unique among city circuits for extreme low-drag setup',
    },
    {
      tag: 'Extreme Top Speed',
      icon: 'speed',
      description: '360+ km/h achievable with DRS along the iconic Las Vegas Strip',
    },
    {
      tag: 'Maximum Evolution',
      icon: 'evolution',
      description: 'Street surface grip improves dramatically as rubber is laid down',
    },
    {
      tag: 'Braking Critical',
      icon: 'braking',
      description: 'Cold tyres after 1.9 km straights challenge braking stability into T14',
    },
    {
      tag: 'Overtaking Friendly',
      icon: 'overtake',
      description: 'Two DRS zones create multiple genuine passing opportunities',
    },
    {
      tag: 'Night Race',
      icon: 'night',
      description: 'Racing under the neon lights of Las Vegas — coldest weekend on calendar',
    },
  ],
}
