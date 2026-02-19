import type { TrackIntelligence } from './types'

/**
 * Singapore Grand Prix - Marina Bay Street Circuit
 * Round 18 of the 2025 FIA Formula 1 World Championship
 * 
 * The only permanent night race on the F1 calendar, held under floodlights since 2008.
 * Requires maximum downforce (highest on calendar) despite being a street circuit. The
 * extreme heat and humidity make this one of the most physically demanding races.
 * 2023 layout change reduced corners from 23 to 19 and added a 4th DRS zone.
 */
export const singaporeTrackIntelligence: TrackIntelligence = {
  circuitId: 'marina_bay',
  round: 18,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Marina Bay Street Circuit',
    country: 'Singapore',
    location: 'Marina Bay, Singapore',
    grandPrixName: 'Singapore Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 2008,
    description:
      'The Marina Bay Street Circuit is the only permanent night race on the Formula 1 calendar, held under 1,500 floodlights since its inaugural race in 2008. The circuit winds through Singapore\'s iconic Marina Bay district, passing landmarks like the Singapore Flyer, Esplanade, and the city\'s glittering skyline. A 2023 layout change reduced corners from 23 to 19 by removing two chicanes, adding a 4th DRS zone on Raffles Avenue and improving overall flow. Despite having 4 DRS zones (most on the calendar), overtaking remains extremely difficult — second only to Monaco. The extreme heat and humidity (heat index often exceeding 31°C) combined with the bumpy street surface makes this one of F1\'s most physically demanding races, with drivers losing up to 3kg during the event.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.940,
      miles: 3.069,
    },
    raceDistance: {
      km: 306.143,
      miles: 190.207,
    },
    numberOfLaps: 62,
    numberOfCorners: 19,
    drsZones: 4,
    lapRecord: {
      time: '1:33.808',
      driver: 'Lewis Hamilton',
      year: 2025,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-2.00°',
      },
      minStartingPressures: {
        front: '22.0 psi',
        rear: '20.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,              // High - critical for 19 corners
    tyreStress: 2,            // Low-Medium - moderate thermal demands
    asphaltGrip: 3,           // Medium - street surface with evolution
    asphaltAbrasion: 3,       // Medium - balanced wear
    braking: 5,               // MAXIMUM - paramount, 10 corners in 1st/2nd gear
    lateral: 2,               // Low - slow corners don't generate sustained loads
    downforce: 5,             // MAXIMUM - highest on calendar
    trackEvolution: 5,        // MAXIMUM - street surface rubbers in substantially
  },

  energyProfile: {
    longitudinal: 'High',     // Heavy braking demands
    lateral: 'Low',           // Slow corners limit lateral forces
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#E53935',  // Red
      corners: 'T1-T6',
      description:
        'Main straight into technical sequence featuring 2 DRS zones including the longest on the circuit. Mix of medium-speed and slow corners with two full-throttle sections separated by a medium-speed left-hander. The heavily-loaded wings make DRS extremely effective here.',
      keyFeatures: [
        'Contains 2 DRS zones (including longest on circuit)',
        'Mix of medium-speed and slow corners',
        'Two full-throttle sections',
        'High DRS effectiveness with max-downforce wings',
        'Critical corner entry precision required',
      ],
      criticalCorners: [
        'T1 - Heavy braking from 290+ km/h, key overtaking zone',
        'T2-T3 - Technical sequence setting up DRS zone',
        'T5 - Medium-speed left leading to second DRS',
      ],
    },
    {
      sector: 2,
      color: '#1E88E5',  // Blue
      corners: 'T7-T13',
      description:
        'The slowest and most technical sector featuring a succession of slow right-hand corners. Braking and traction are absolutely crucial — downforce aids stability more than cornering speed as corners are too slow for significant aero benefit. Contains the shortest DRS zone. Engine operates at lower rev range (~13,000rpm).',
      keyFeatures: [
        'Slowest sector on circuit',
        'Succession of slow right-hand corners',
        'Shortest DRS zone on circuit',
        'Braking and traction paramount',
        'Engine operates at ~13,000rpm',
      ],
      criticalCorners: [
        'T7 - Heavy braking into technical complex',
        'T8-T10 - Slow right-hand sequence, rear stability critical',
        'T13 - Exit crucial for Sector 3 approach',
      ],
    },
    {
      sector: 3,
      color: '#FDD835',  // Yellow
      corners: 'T14-T19',
      description:
        'Similar character to Sector 2 but quicker overall with more full-throttle time. The 2023 layout change removed two chicanes here, creating a long straight on Raffles Avenue with the 4th DRS zone. Improved flow compared to original configuration with better overtaking opportunities.',
      keyFeatures: [
        'Quicker than Sector 2',
        'More full-throttle time',
        '2023 layout added long Raffles Avenue straight',
        '4th DRS zone creates overtaking opportunity',
        'Late apex technique essential',
      ],
      criticalCorners: [
        'T14 - Entry to flowing section',
        'T17 - Raffles Boulevard corner',
        'T19 - Final corner onto main straight, exit speed critical',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Before Turn 19',
      activationPoint: 'Start of main straight',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'Primary DRS zone along the main straight leading into Turn 1. The longest DRS zone on the circuit. Combined with maximum downforce wings, DRS is highly effective here, providing significant speed gain.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 2',
      activationPoint: 'Before Turn 4',
      deactivationPoint: 'Turn 5 braking zone',
      description:
        'Second DRS zone in Sector 1. Provides additional straight-line speed advantage but the following corner limits overtaking completion.',
      effectiveness: 'Medium',
    },
    {
      zone: 3,
      detectionPoint: 'After Turn 7',
      activationPoint: 'Before Turn 8 complex',
      deactivationPoint: 'Turn 8 entry',
      description:
        'The shortest DRS zone on the circuit, located in the slow Sector 2. Limited effectiveness due to short distance and slow-speed corners following.',
      effectiveness: 'Low',
    },
    {
      zone: 4,
      detectionPoint: 'After Turn 16',
      activationPoint: 'Raffles Avenue straight',
      deactivationPoint: 'Turn 17 braking zone',
      description:
        'Added in 2023 layout change when chicanes were removed. Creates a genuine overtaking opportunity on Raffles Avenue. The new long straight makes this an effective zone despite being in Sector 3.',
      effectiveness: 'High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Maximum',
      explanation:
        'Singapore demands the highest downforce configuration on the calendar — non-negotiable. The short straights minimize drag penalty while maximum downforce aids brake stability and mechanical grip through the slow corners. Mercedes ran extreme max downforce with very vertical upper plane and deep lower plane with gurney flaps. Red Bull and Racing Bulls showed excellent traction (53%+ throttle time). Ferrari tested a medium-high alternative in FP2 but reverted to max downforce for qualifying. Alpine ran the least loaded wings but had the worst overall pace despite highest top speeds (317 km/h).',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard soft-bias allocation',
      primaryWearMechanism: 'Thermal cycling and traction wear from slow corners',
      explanation:
        'Tyre management at Singapore is relatively straightforward due to low degradation. The Medium compound showed excellent durability — Carlos Sainz completed 50 laps on a single set with remarkable tyre management. The Hard showed a slight overall edge in race conditions with very low degradation (40+ laps comfortable). The Soft offered no significant advantage over Medium and degraded rapidly after 10 laps, making it primarily a qualifying compound.',
      strategicNote: 'One-stop on Medium-Hard dominant. Soft tyres offer minimal race advantage.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Low initial grip with massive track evolution',
      impact: 'Street surface rubbers in substantially through the weekend. Grip levels increase dramatically from FP1 to race, but offline grip remains poor.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Very High',
    primaryZone: 'Turn 1 (end of main straight with DRS Zone 1)',
    secondaryZones: ['Turn 4 (DRS Zone 2)', 'Turn 17 (Raffles Avenue DRS Zone 4)'],
    factors: [
      '4 DRS zones (most on calendar) but still second hardest to overtake after Monaco',
      'Narrow street circuit with walls limiting alternative lines',
      'Slow corners make following easier but passing harder',
      'Track position absolutely paramount for race result',
      'Qualifying performance critical — grid position often determines race finish',
      'DRS highly effective due to max-downforce wings but passing still difficult',
      'Undercut potential strong but track position remains king',
    ],
    recommendation:
      'Despite having 4 DRS zones, Singapore remains the second-hardest circuit for overtaking after Monaco. Track position is paramount — qualifying is effectively half the race. The undercut is strong but the premium on clean air makes staying ahead the optimal strategy. Focus all efforts on qualifying performance.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot, humid, occasional thunderstorms',
      airTemperature: {
        max: '33°C',
        min: '27°C',
        raceTime: '30°C',
      },
      rainProbability: 'Moderate (tropical climate)',
      wind: 'Light',
      humidity: 'Extreme (80-95%)',
    },
    sessionConditions: {
      fp1: '30-31°C, mostly cloudy, 40% rain chance',
      fp2: '30-31°C, mostly cloudy, 40% rain chance',
      fp3: '30-31°C, mostly cloudy, 20% rain chance',
      qualifying: '30°C, mostly cloudy, 20% rain chance',
      race: '30°C, partly cloudy, 20% rain chance',
    },
    impact:
      'Singapore\'s extreme heat and humidity create the most physically demanding conditions alongside Monaco. Heat index regularly exceeds 31°C (FIA heat hazard threshold), allowing teams to add cooling systems (+5kg allowance) or 0.5kg ballast. Drivers lose up to 3kg body weight during the race. The night race format provides stable track temperatures but the floodlights create unique lighting conditions. Track evolution is substantial as the street surface rubbers in.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:33.808',
      driver: 'Lewis Hamilton',
      year: 2025,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:30.984',
        driver: 'SAI',
      },
      {
        year: 2024,
        time: '1:29.525',
        driver: 'NOR',
      },
      {
        year: 2025,
        time: '1:29.158',
        driver: 'RUS',
        note: 'Track record',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'RUS', time: '1:29.158' },
        { position: 2, driver: 'VER', time: '1:29.340' },
        { position: 3, driver: 'PIA', time: '1:29.524' },
        { position: 4, driver: 'ANT', time: '1:29.537' },
        { position: 5, driver: 'NOR', time: '1:29.586' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '26.860s', driver: 'ALO' },
        { sector: 2, time: '38.010s', driver: 'VER' },
        { sector: 3, time: '25.597s', driver: 'STR' },
      ],
      overallIdealLap: '1:30.467',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'RUS',
        meanLapTime: '96.63s',
        gaps: [
          { driver: 'PIA', gap: '+0.04s' },
          { driver: 'VER', gap: '+0.06s' },
          { driver: 'NOR', gap: '+0.10s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '97.04s',
        gaps: [
          { driver: 'VER', gap: '+0.41s' },
          { driver: 'PIA', gap: '+0.68s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'ANT', speed: '317 km/h' },
        range: '312-317 km/h',
      },
      race: {
        withDRS: 'Up to 323 km/h',
        withoutDRS: '295 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop strategy dominant (Medium → Hard)',
      factors: [
        'Single-stop strongly favored — two-stop did not provide advantage',
        'Optimal pit window: Laps 20-28',
        'Early stop window: Laps 12-18 for soft runners or undercut attempts',
        'Pit lane time loss approximately 24 seconds',
        'Undercut effective (1.5-2s per lap on fresh tyres) but track position still paramount',
        'Safety Car probability moderate (street circuit with walls)',
        'Medium compound showed exceptional durability (Sainz: 50 laps)',
      ],
    },
    keyStrategicFactors: [
      'Track position paramount — overtaking extremely difficult (2nd hardest after Monaco)',
      'Qualifying performance critical — grid position often determines race finish',
      'Single-stop on Medium-Hard optimal for frontrunners',
      'Soft tyres offer minimal advantage, degrade rapidly after 10 laps',
      'Hard compound showed slight overall edge with very low degradation',
      'Two-stop strategies did not pay off (Hamilton, Hulkenberg)',
      'Verstappen\'s Soft-Medium compromised by forced early stop (used 3-lap old softs)',
      'Tyre management essential in extreme heat/humidity conditions',
    ],
    safetyCarLikelihood: 'Moderate - street circuit with walls, historical incidents common',
    historicalNotes: [
      '2025: Russell wins from pole (+5.430s), first Singapore GP with zero retirements',
      '2025: McLaren clinched Constructors\' Championship (650 points, 10th title)',
      '2025: Williams DSQ from qualifying (both cars) for DRS rear wing infringement',
      '2025: Hamilton received 5s penalty for track limits, set lap record 1:33.808',
      '2024: Norris wins dominant from pole',
      '2023: Major layout change — 23 to 19 corners, added 4th DRS zone',
      '2019: Vettel\'s final F1 victory (won via undercut on Leclerc/Hamilton)',
      '2008: Inaugural F1 night race (Crashgate scandal revealed 2009)',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Night Race',
      icon: 'night',
      description: 'Only permanent F1 night race, held under 1,500 floodlights since 2008',
    },
    {
      tag: 'Maximum Downforce',
      icon: 'gauge',
      description: 'Highest downforce requirement on calendar (5/5) — non-negotiable setup',
    },
    {
      tag: 'Extreme Heat',
      icon: 'thermometer',
      description: 'Heat index >31°C triggers FIA protocols, drivers lose up to 3kg during race',
    },
    {
      tag: 'Overtaking Difficulty',
      icon: 'lock',
      description: 'Second hardest after Monaco despite 4 DRS zones — qualifying is critical',
    },
    {
      tag: 'Street Circuit',
      icon: 'track',
      description: 'Marina Bay city center with iconic skyline, bumpy surface, wall proximity',
    },
  ],

  fuelEffectPerKg: 0.036,
}
