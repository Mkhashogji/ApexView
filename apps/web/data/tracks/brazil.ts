import type { TrackIntelligence } from './types'

/**
 * Brazilian Grand Prix - Autódromo José Carlos Pace (Interlagos)
 * Round 21 of the 2025 FIA Formula 1 World Championship
 * 
 * One of F1's most legendary circuits, known for dramatic races and unpredictable weather.
 * The counter-clockwise direction creates unique physical demands on drivers.
 * Second highest altitude (765m) on the calendar affects aero and engine performance.
 */
export const brazilTrackIntelligence: TrackIntelligence = {
  circuitId: 'interlagos',
  round: 21,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Autódromo José Carlos Pace',
    country: 'Brazil',
    location: 'São Paulo, Brazil',
    grandPrixName: 'Brazilian Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1973,
    description:
      'Interlagos is one of Formula 1\'s most storied venues, located in the Interlagos neighborhood 16km south of São Paulo\'s city center. Named after Brazilian driver José Carlos Pace who died in 1977, this circuit has hosted some of the sport\'s most dramatic moments, including championship deciders and legendary wet-weather drives. The track\'s counter-clockwise direction is unusual on the calendar, subjecting drivers to rightward neck loading throughout the lap. The dramatic 40+ meter elevation change creates a roller-coaster character, while the second highest altitude (765m) after Mexico City affects aerodynamic and engine performance.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.309,
      miles: 2.677,
    },
    raceDistance: {
      km: 305.879,
      miles: 190.066,
    },
    numberOfLaps: 71,
    numberOfCorners: 15,
    drsZones: 2,
    lapRecord: {
      time: '1:10.540',
      driver: 'Valtteri Bottas',
      year: 2018,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '25.0 psi',
        rear: '23.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,
    tyreStress: 3,        
    asphaltGrip: 3,
    asphaltAbrasion: 2,
    braking: 3,
    lateral: 3,
    downforce: 4,         // Medium-high downforce required
    trackEvolution: 5,    // Maximum - very high track evolution
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
      corners: 'T1-T3',
      description:
        'Sector 1 begins with the strongest braking point on the circuit into Turn 1, a downhill left-hander where lockups are common due to the banking unloading the front-left wheel. The sector then flows into the iconic Senna Esses (T2-T3), a fast, flowing sequence requiring precision and full commitment.',
      keyFeatures: [
        'Strongest braking point into T1',
        'Iconic Senna Esses (T2-T3)',
        'Elevation drop intensifies braking',
        'Front-end balance critical',
      ],
      criticalCorners: [
        'T1 - Heavy braking, banking unloads front-left',
        'T2-T3 - Senna Esses, requires full commitment',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T4-T10',
      description:
        'The slowest sector on the circuit, featuring a mix of medium-speed corners (T4-T7) followed by slower, tighter turns (T8-T10). This is where high-downforce setups pay dividends, as drag is not a significant factor. Higher downforce offers practically no drawbacks here.',
      keyFeatures: [
        'Slowest sector overall',
        'Mix of medium and slow corners',
        'High downforce favored',
        'Traction out of T10 crucial',
      ],
      criticalCorners: [
        'T4-T7 - Medium-speed technical sequence',
        'T10 - Exit traction critical for S3 speed',
      ],
    },
    {
      sector: 3,
      color: '#FFD700',  // Yellow/Gold
      corners: 'T11-T15',
      description:
        'A braking point at Turn 12 (Junção) followed by a full-throttle blast through the long, curved section from T13 to T15 (Subida dos Boxes) up to the start/finish line. Lower drag setups and higher engine power translate directly to quicker times here. The uphill run gains 40m of elevation.',
      keyFeatures: [
        'Full-throttle from T13 to finish',
        'Low drag benefits here',
        'DRS Zone 2 on main straight',
        '40m elevation gain uphill',
      ],
      criticalCorners: [
        'T12 (Junção) - Secondary heavy braking zone',
        'T15 - Exit onto main straight critical',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'After Turn 12 (Junção)',
      activationPoint: 'Before Turn 14',
      deactivationPoint: 'Turn 14 entry',
      description:
        'First DRS zone located between Junção and the back straight. Sets up moves for the main straight or enables passes into T1 on the following lap.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 14',
      activationPoint: 'Main straight before T1',
      deactivationPoint: 'T1 braking zone',
      description:
        'Primary overtaking zone on the pit straight. The combination of DRS and the long straight enables passes into the heavy braking zone at Turn 1.',
      effectiveness: 'Very High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium',
      explanation:
        'Medium-load rear wings are standard at Interlagos. Teams vary between medium-low (favoring dry conditions with straight-line speed) and medium-high (optimal for wet sessions and Sector 2). The 765m altitude partially offsets drag penalties of higher-downforce configurations. McLaren and Ferrari use V-shaped lower planes versus Red Bull\'s full-width design.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard mid-range compounds',
      primaryWearMechanism: 'Right-side tyre stress from counter-clockwise direction',
      explanation:
        'The counter-clockwise direction heavily stresses the right-hand side tyres, particularly the rear-right. Mediums were the king compound in 2025, with multiple viable strategies confirmed. Softs faded faster than expected, while Hards were generally a trap. One-stop is possible with exceptional tyre management.',
      strategicNote: 'Two-stop is standard. M-S-M or S-M-M strategies most common.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium with very high evolution',
      impact: 'Track evolution is extreme — qualifying order can change dramatically between sessions. The short lap length (4.309 km) creates significant traffic management challenges.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (end of main straight with DRS Zone 2)',
    secondaryZones: ['Turn 4 (after Senna Esses)', 'Turn 12 (Junção)'],
    factors: [
      'Two DRS zones provide good overtaking opportunities',
      'Heavy braking into T1 is primary passing spot',
      'Short lap length means frequent traffic encounters',
      'T12 (Junção) braking zone enables opportunistic moves',
      'Dirty air through Senna Esses is punishing',
      'Setup compromise between S2 downforce and S3 straight-line speed',
    ],
    recommendation:
      'Qualifying position is important but overtaking is achievable. Two DRS zones and heavy braking zones create genuine opportunities. Strategic undercuts are effective due to high track evolution.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Notoriously unpredictable — rain can appear suddenly',
      airTemperature: {
        max: '28°C',
        min: '18°C',
        raceTime: '22-25°C',
      },
      rainProbability: 'High (30-50% for any session)',
      wind: 'Variable, light to moderate',
      humidity: 'High (tropical climate)',
    },
    sessionConditions: {
      fp1: '24°C, variable conditions',
      sprintQuali: '22°C, dry',
      sprint: '23°C, dry (red flag incidents)',
      qualifying: '24°C, dry',
      race: '25°C, dry',
    },
    impact:
      'Interlagos is notorious for unpredictable weather. Rain can affect isolated sections of the track while others remain dry, creating strategic chaos. The 2024 race featured 5 red flags due to wet conditions. Teams must always have a wet-weather backup strategy ready.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:10.540',
      driver: 'Valtteri Bottas',
      year: 2018,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:23.405',
        driver: 'NOR',
        note: 'Wet conditions (5 red flags)',
      },
      {
        year: 2025,
        time: '1:09.511',
        driver: 'NOR',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:09.511' },
        { position: 2, driver: 'ANT', time: '1:09.685' },
        { position: 3, driver: 'LEC', time: '1:09.805' },
        { position: 4, driver: 'PIA', time: '1:09.886' },
        { position: 5, driver: 'HAD', time: '1:09.931' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Sprint Qualifying',
      sectors: [
        { sector: 1, time: '17.742s', driver: 'VER' },
        { sector: 2, time: '35.231s', driver: 'NOR' },
        { sector: 3, time: '16.050s', driver: 'NOR' },
      ],
      overallIdealLap: '1:09.023',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER (Four-Stop Strategy)',
        meanLapTime: '74.11s',
        gaps: [
          { driver: 'NOR', gap: '+0.03s (Three-Stop Strategy)' },
          { driver: 'PIA', gap: '+0.10s (Three-Stop Strategy)' },
          { driver: 'ANT', gap: '+0.14s (Three-Stop Strategy)' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '83.30s',
        gaps: [
          { driver: 'RUS', gap: '+0.19s' },
          { driver: 'NOR', gap: '+0.30s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'HAM', speed: '340 km/h' },
        range: '331-340 km/h',
      },
      race: {
        withDRS: 'Up to 346 km/h (VER recovery drive)',
        withoutDRS: '313-315 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop standard, one-stop possible with management',
      factors: [
        'Laps 25-30 optimal for first stop',
        'Laps 45-50 for second stop',
        'Early stop (Lap 18-22) for undercut potential',
        'Extended first stint to Lap 35+ possible with tyre management',
        'Pit lane time loss approximately 22-23 seconds',
      ],
    },
    keyStrategicFactors: [
      'Mediums were the king compound in 2025',
      'Multiple viable strategies: M-S-M, S-M-M, H-M-S-M all worked',
      'Softs faded faster than expected',
      'Hards were generally a trap',
      'Very high track evolution rewards later runs in qualifying',
      'Short lap length creates frequent safety car opportunities',
    ],
    safetyCarLikelihood: 'High - short track, barriers, and unpredictable weather',
    historicalNotes: [
      '2025: Norris won from pole, Verstappen recovered from pit lane to P3',
      '2025: Both Ferrari drivers DNF (Hamilton floor damage, Leclerc collision)',
      '2025: Antonelli\'s first front-row start in F1 (P2)',
      '2025: Sprint red-flagged twice (Piastri/Colapinto crash, Bortoleto crash)',
      '2024: Verstappen won from P17 in legendary wet race',
      'Verstappen Q1 elimination in 2025 — worst qualifying since 2018',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Legendary Circuit',
      icon: 'trophy',
      description: 'One of F1\'s most historic venues with championship-deciding drama',
    },
    {
      tag: 'Weather Roulette',
      icon: 'weather',
      description: 'Notoriously unpredictable conditions with localized rain showers',
    },
    {
      tag: 'Altitude Challenge',
      icon: 'elevation',
      description: 'Second highest circuit at 765m affects aero and engine performance',
    },
    {
      tag: 'Tyre Critical',
      icon: 'tyre',
      description: 'Counter-clockwise direction stresses right-side tyres heavily',
    },
    {
      tag: 'Strategy Diverse',
      icon: 'strategy',
      description: 'Multiple viable pit strategies with very high track evolution',
    },
  ],
}
