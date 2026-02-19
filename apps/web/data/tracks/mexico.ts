import type { TrackIntelligence } from './types'

/**
 * Mexican Grand Prix - Autódromo Hermanos Rodríguez
 * Round 20 of the 2025 FIA Formula 1 World Championship
 * 
 * The highest altitude circuit on the calendar at 2,285m elevation. Mexico presents
 * a unique paradox: maximum downforce despite producing the season's highest top speeds.
 * The 22% reduced air density at altitude means aero surfaces must work harder.
 */
export const mexicoTrackIntelligence: TrackIntelligence = {
  circuitId: 'rodriguez',
  round: 20,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Autódromo Hermanos Rodríguez',
    country: 'Mexico',
    location: 'Mexico City, Mexico',
    grandPrixName: 'Mexican Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1963,
    description:
      'The Autódromo Hermanos Rodríguez is the highest altitude circuit on the Formula 1 calendar at 2,285 meters above sea level. Named after Mexican racing brothers Ricardo and Pedro Rodríguez, the track returned to F1 in 2015 after a 23-year absence. The extreme altitude creates a unique paradox: teams must run maximum downforce configurations despite the circuit producing some of the season\'s highest top speeds. The 22% reduced air density means aerodynamic surfaces generate significantly less downforce and engines produce less power, yet the thin air also reduces drag, enabling remarkable straight-line speeds. The iconic Foro Sol stadium section creates an unparalleled atmosphere with 60,000 fans witnessing cars navigate the final corners.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.304,
      miles: 2.674,
    },
    raceDistance: {
      km: 305.584,
      miles: 189.854,
    },
    numberOfLaps: 71,
    numberOfCorners: 17,
    drsZones: 3,
    lapRecord: {
      time: '1:17.774',
      driver: 'Valtteri Bottas',
      year: 2021,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '23.5 psi',
        rear: '21.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,
    tyreStress: 2,            // Low tyre stress due to thin air
    asphaltGrip: 2,
    asphaltAbrasion: 2,
    braking: 3,
    lateral: 2,
    downforce: 5,             // MAXIMUM - required at altitude
    trackEvolution: 5,        // MAXIMUM - significant grip evolution
  },

  energyProfile: {
    longitudinal: 'Medium',
    lateral: 'Medium',
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
        'Opens with heavy braking into Turn 1 after the long main straight. The sector features a mix of medium-speed corners requiring good traction. Turn 1 is a key overtaking zone with DRS Zone 3 assistance. The Esses (T4-T6) demand precise car placement and smooth inputs.',
      keyFeatures: [
        'Primary braking zone at T1',
        'DRS Zone 3 ends here',
        'Esses complex (T4-T6)',
        'Traction critical through mid-speed corners',
      ],
      criticalCorners: [
        'T1 - Heavy braking after main straight, key overtaking zone',
        'T4-T6 - Esses requiring rhythm and precision',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T7-T11',
      description:
        'The most technical sector featuring the challenging Esses complex (T7-T11). This flowing section rewards commitment and car balance. Drivers must carry speed through the linked corners while managing tyre temperature in the thin air. Exit of T11 is crucial for DRS Zone 1.',
      keyFeatures: [
        'Technical Esses complex',
        'Flow-dependent sector',
        'Balance between apex speed and exit traction',
        'Sets up DRS Zone 1',
      ],
      criticalCorners: [
        'T7-T9 - First Esses sequence',
        'T10-T11 - Exit critical for DRS Zone 1 straight',
      ],
    },
    {
      sector: 3,
      color: '#FFFF00',  // Yellow
      corners: 'T12-T17',
      description:
        'The spectacular stadium section through the Foro Sol. Features the long straight with DRS Zone 2 leading into the Peraltada (T12), then navigates through the baseball stadium with 60,000 fans creating an electric atmosphere. The final corners require precision before the main straight.',
      keyFeatures: [
        'DRS Zone 2 straight',
        'Iconic Foro Sol stadium',
        'Peraltada entry (T12)',
        '60,000 fans in stadium section',
        'Sets up main straight',
      ],
      criticalCorners: [
        'T12 - Peraltada entry after DRS straight',
        'T13-T15 - Stadium complex',
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
      detectionPoint: 'After Turn 11',
      activationPoint: 'Before Turn 12 (Peraltada)',
      deactivationPoint: 'Turn 12 braking zone',
      description:
        'Short DRS zone leading into the Peraltada corner. Creates passing opportunities into the entry of the stadium section. Effectiveness reduced by thin air but still provides meaningful slipstream advantage.',
      effectiveness: 'Medium',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 15',
      activationPoint: 'Start of pit straight section',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'The main DRS zone along the start/finish straight. Combined with DRS Zone 3, creates the primary overtaking opportunity at Turn 1. Top speeds can exceed 360 km/h despite the altitude.',
      effectiveness: 'High',
    },
    {
      zone: 3,
      detectionPoint: 'Before Turn 3',
      activationPoint: 'After Turn 3',
      deactivationPoint: 'Turn 4 entry',
      description:
        'Auxiliary DRS zone in Sector 1. Helps extend passing opportunities from the main straight or sets up moves into the Esses section.',
      effectiveness: 'Medium',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Maximum',
      explanation:
        'Mexico demands the highest downforce configuration of the season. The 22% reduced air density at 2,285m altitude means aerodynamic surfaces produce significantly less downforce — teams must compensate by running maximum wing angles. This creates Mexico\'s famous paradox: despite maximum downforce settings, cars achieve some of the highest top speeds of the year because the thin air also dramatically reduces drag.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Soft-bias allocation',
      primaryWearMechanism: 'Thermal degradation minimal; sliding wear in thin air',
      explanation:
        'Tyre wear at Mexico is unusually low due to the thin air reducing both aerodynamic load and grip. The lack of air resistance means tyres work less hard despite maximum wing angles. Degradation is minimal, enabling extended stints and one-stop strategies. The challenge is maintaining tyre temperature rather than managing wear.',
      strategicNote: 'One-stop is the standard strategy. Soft-Medium or Medium-Hard combinations both viable.',
    },
    surfaceCharacteristics: {
      resurfaced: 2023,
      impact: 'Smoother surface after 2023 resurfacing reduced graining issues',
      gripLevel: 'Low initial grip with significant evolution over the weekend',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (end of main straight with DRS Zone 2/3)',
    secondaryZones: ['Turn 12 (Peraltada entry with DRS Zone 1)', 'Turn 4 (into Esses)'],
    factors: [
      'Three DRS zones provide multiple opportunities',
      'DRS effectiveness reduced by thin air (~15% less efficient)',
      'High top speeds create large speed differentials',
      'Turn 1 is the primary overtaking spot with heavy braking',
      'Stadium section visibility can aid defensive driving',
      'Track position remains important despite passing opportunities',
    ],
    recommendation:
      'Overtaking is achievable at Mexico but requires commitment. The three DRS zones compensate for reduced aero efficiency at altitude. Focus on strong exits from T11 and T17 to maximize DRS advantage. Turn 1 heavy braking zone provides the best opportunity for completed passes.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Warm, sunny with potential afternoon showers',
      airTemperature: {
        max: '28°C',
        min: '14°C',
        raceTime: '22-25°C',
      },
      rainProbability: 'Moderate (afternoon thunderstorms possible)',
      wind: 'Light to moderate',
      humidity: 'Moderate to high',
    },
    sessionConditions: {
      fp1: '24°C, sunny',
      fp2: '25°C, partly cloudy',
      fp3: '23°C, overcast',
      qualifying: '24°C, dry',
      race: '25°C, sunny, track temp >52°C',
    },
    impact:
      'Mexico experiences warm conditions with potential for afternoon thunderstorms. Track temperatures can exceed 52°C, creating significant thermal challenges despite low air density. The altitude affects engine cooling — teams must balance performance with thermal management. Late afternoon rain is always a possibility during race weekend.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:17.774',
      driver: 'Valtteri Bottas',
      year: 2021,
    },
    polePositions: [
      {
        year: 2019,
        time: '1:14.758',
        driver: 'VER',
        note: 'Track record',
      },
      {
        year: 2023,
        time: '1:17.166',
        driver: 'LEC',
      },
      {
        year: 2024,
        time: '1:15.946',
        driver: 'SAI',
      },
      {
        year: 2025,
        time: '1:15.586',
        driver: 'NOR',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:15.586' },
        { position: 2, driver: 'LEC', time: '1:15.848' },
        { position: 3, driver: 'HAM', time: '1:15.938' },
        { position: 4, driver: 'RUS', time: '1:16.034' },
        { position: 5, driver: 'VER', time: '1:16.070' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '26.916s', driver: 'NOR' },
        { sector: 2, time: '29.114s', driver: 'NOR' },
        { sector: 3, time: '19.556s', driver: 'NOR' },
      ],
      overallIdealLap: '1:15.586',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR (Two-Stop Strategy)',
        meanLapTime: '82.06s',
        gaps: [
          { driver: 'PIA', gap: '+0.15s (Three-Stop Strategy)' },
          { driver: 'BEA', gap: '+0.19s (Three-Stop Strategy)' },
          { driver: 'HAM', gap: '+0.19s (Three-Stop Strategy)' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'SAI',
        meanLapTime: '81.08s',
        gaps: [
          { driver: 'NOR', gap: '+0.05s' },
          { driver: 'LEC', gap: '+0.16s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'RUS', speed: '352 km/h' },
        range: '342-352 km/h',
      },
      race: {
        withDRS: 'Up to 366 km/h',
        withoutDRS: '324 km/h',
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
        'Very low tyre degradation due to thin air',
        'Single stop on Medium-Hard or Soft-Medium optimal',
        'Pit lane time loss approximately 22-23 seconds',
        'Track position valuable despite overtaking opportunities',
        'Late safety car can enable fresh tyre gambits',
      ],
    },
    keyStrategicFactors: [
      'Minimal tyre degradation enables long stints',
      'Engine cooling is critical at altitude — power reduced ~20%',
      'Maximum downforce setup despite high top speeds',
      'Three DRS zones partially offset reduced aero efficiency',
      'Track evolution is massive — qualifying position can be misleading',
      'Altitude affects turbo performance and ICE output',
    ],
    safetyCarLikelihood: 'Moderate - permanent circuit with run-off but stadium section narrow',
    historicalNotes: [
      '2025: NOR wins from pole, fastest lap RUS 1:20.052',
      '2024: SAI wins, Verstappen P6 due to penalties',
      '2023: VER dominant victory',
      '2022: VER wins with Red Bull 1-3',
      '2021: VER wins, Bottas sets current lap record 1:17.774',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Extreme Altitude',
      icon: 'elevation',
      description: 'Highest circuit at 2,285m — 22% reduced air density affects everything',
    },
    {
      tag: 'Maximum Downforce',
      icon: 'gauge',
      description: 'Paradox: max wings required despite producing highest top speeds',
    },
    {
      tag: 'Stadium Atmosphere',
      icon: 'trophy',
      description: 'Iconic Foro Sol with 60,000 fans in the stadium section',
    },
    {
      tag: 'Engine Challenge',
      icon: 'zap',
      description: 'Cooling critical and ~20% power reduction in thin air',
    },
    {
      tag: 'High Evolution',
      icon: 'tyre',
      description: 'Maximum track evolution reshapes competitive order through weekend',
    },
  ],

  fuelEffectPerKg: 0.031,
}
