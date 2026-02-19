import type { TrackIntelligence } from './types'

/**
 * Austrian Grand Prix - Red Bull Ring
 * Round 11 of the 2025 FIA Formula 1 World Championship
 *
 * The Red Bull Ring is a high-altitude circuit in the Styrian Alps that produces
 * the shortest lap times on the F1 calendar. Its 10 corners—the fewest of any
 * circuit—are connected by three consecutive straights that put immense stress
 * on ERS deployment and battery management. The 700m altitude reduces air density
 * by approximately 7%, affecting both aerodynamic performance and engine cooling.
 */
export const austriaTrackIntelligence: TrackIntelligence = {
  circuitId: 'red_bull_ring',
  round: 11,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Red Bull Ring',
    country: 'Austria',
    location: 'Spielberg, Styria',
    grandPrixName: 'Austrian Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1970,
    description:
      'The Red Bull Ring is a high-altitude circuit in the Styrian Alps that produces the shortest lap times on the F1 calendar. Its 10 corners—the fewest of any circuit—are connected by three consecutive straights that put immense stress on ERS deployment and battery management. The 700m altitude reduces air density by approximately 7%, affecting both aerodynamic performance and engine cooling. Stop-and-go slow corners demand excellent traction, while the high-speed final sector rewards aerodynamic efficiency and driver bravery. Despite being only the 5th shortest track by distance, it has the fastest lap times due to its flowing nature and limited corner count.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.326, // FIA centreline length per 2025 Event Notes
      miles: 2.688,
    },
    raceDistance: {
      km: 307.146, // 71 laps × 4.326 km (FIA centreline)
      miles: 190.852,
    },
    numberOfLaps: 71, // Note: 2025 race ran 70 laps after aborted start (per race classification)
    numberOfCorners: 10, // Fewest on F1 calendar
    drsZones: 3,
    lapRecord: {
      time: '1:05.619',
      driver: 'Carlos Sainz',
      year: 2020,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '22.5 psi',
        rear: '20.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,        // Adjusted from Pirelli's 2/5 - poor exits significantly impact performance
    tyreStress: 3,      // Moderate overall
    asphaltGrip: 3,     // Moderate
    asphaltAbrasion: 3, // Moderate
    braking: 3,         // Moderate
    lateral: 3,         // Moderate
    downforce: 3,       // Medium downforce requirement
    trackEvolution: 3,  // Moderate
  },

  energyProfile: {
    longitudinal: 'Medium',   // Moderate braking demands
    lateral: 'Medium',        // Moderate lateral loads
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  // Note: Corner naming varies across sources. Names below follow FIA 2025 Event Notes where available.
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T2',
      description:
        'The shortest sector. A high-speed blast from the start/finish line up the hill to T1 (Niki Lauda Turn), followed by T2 (Münzer Turn). Predominantly uphill with heavy braking into T1 from over 300 km/h. Exit speed from T1 is crucial as it feeds directly into the next straight.',
      keyFeatures: [
        'T1 (Niki Lauda Turn): Heavy braking from 310+ km/h to ~70 km/h - hardest braking zone',
        'T2 (Münzer Turn): Medium-speed right at ~150-180 km/h',
        'DRS Zone 3 ends approaching T1 - primary overtaking opportunity',
        'Exit traction from T1 critical for following straight speed',
        'Site of 2025 Verstappen-Antonelli lap 1 collision (analysis)',
      ],
      criticalCorners: [
        'T1 (Niki Lauda Turn) - ~70 km/h apex, primary overtaking zone',
        'T2 (Münzer Turn) - medium-speed right, sets up T3 approach',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T3-T5',
      description:
        'A mix of slow and medium-speed corners with significant braking zones. T3 is an overtaking spot after DRS Zone 1. The blind entry to T4 over a crest is particularly challenging and a common site of incidents.',
      keyFeatures: [
        'T3 (Schlossgold): Tight right-hander at ~95 km/h - DRS Zone 1 ends here',
        'T4 (Rauch Turn): Blind uphill right at ~130 km/h - challenging entry over crest',
        'T5: Fast left at ~220 km/h - often flat in qualifying',
        'DRS Zone 1 activates after T1, enabling overtakes into T3',
        'T3-T4 complex key to sector time',
      ],
      criticalCorners: [
        'T3 (Schlossgold) - ~95 km/h, heavy braking from ~290 km/h',
        'T4 (Rauch Turn) - ~130 km/h, blind crest entry, common incident site',
      ],
    },
    {
      sector: 3,
      color: '#FFD700', // Yellow/Gold
      corners: 'T6-T10',
      description:
        'The most demanding sector aerodynamically, featuring a succession of medium and high-speed corners where downforce is critical. This is where high-downforce setups and driver bravery shine. The flowing nature punishes mistakes severely, and dirty air significantly impacts following cars.',
      keyFeatures: [
        'T6 (Projekt Spielberg): Fast right at ~230 km/h - entry to high-speed complex',
        'T7 (Graz Turn): Medium-speed right at ~180 km/h',
        'T8: Fast left at ~260 km/h - typically flat, tests aero efficiency',
        'T9 (Jochen Rindt Turn): Fast right at ~225 km/h - track limits historically problematic',
        'T10: Final corner at ~200 km/h - exit speed critical for main straight DRS',
      ],
      criticalCorners: [
        'T9 (Jochen Rindt Turn) - ~225 km/h, downforce and confidence key',
        'T10 (Final Corner) - ~200 km/h, exit determines pit straight speed',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '160m before T1 (Niki Lauda Turn)',
      activationPoint: '102m after T1',
      deactivationPoint: 'Approaching T3 braking zone',
      description:
        'First DRS zone activates after T1, enabling overtakes into T3 (Schlossgold). Heavy braking from ~290 km/h provides late-braking opportunities.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: '40m before T3 (Schlossgold)',
      activationPoint: '100m after T3',
      deactivationPoint: 'Approaching T7 (Graz Turn)',
      description:
        'Second DRS zone through the T4-T6 section. Less effective for overtaking due to medium-speed corner entries at T4 and T7, but useful for closing gaps.',
      effectiveness: 'Medium',
    },
    {
      zone: 3,
      detectionPoint: '120m before T10 (Final Corner)',
      activationPoint: '106m after T10 (Start/Finish Straight)',
      deactivationPoint: 'T1 braking zone (Niki Lauda Turn)',
      description:
        'Primary overtaking zone on the main straight. Combined with heavy braking into T1 from over 310 km/h, this creates excellent passing opportunities. Most overtakes occur here.',
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
        'The Austrian GP presents a classic power vs. downforce dilemma. Three long straights reward low drag, but the S3 high-speed complex punishes insufficient downforce. McLaren\'s 2025 success demonstrated that prioritizing S3 performance can overcome straight-line deficits through DRS usage. At 700m altitude, air density is approximately 7% lower than sea level, reducing both drag and downforce proportionally. Teams typically run marginally higher wing angles to compensate. McLaren ran the most loaded configuration and dominated; Mercedes ran very unloaded and struggled in S3.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'One step below softest available compounds',
      primaryWearMechanism: 'Rear tyre traction stress from slow corner exits onto three consecutive straights. Altitude reduces mechanical loading but increases thermal stress due to reduced cooling.',
      explanation:
        'Austria\'s lower air density reduces downforce and therefore stresses tyres less mechanically, but the reduced cooling effect makes thermal management more challenging. Moderate and balanced characteristics across the board. The stop-and-go nature emphasizes traction zones despite moderate overall demands.',
      strategicNote: 'One-stop viable with Hard compound - Lawson completed 38-lap Hard stint in 2025. All three compounds proved viable. Only 5 drivers started on Softs.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Moderate - consistent grip with balanced tyre stress',
      impact: 'Tyre stress, grip, asphalt abrasion, and track evolution are often correlated at this circuit. 65m total elevation change with 12% maximum incline and 9.3% maximum decline affects suspension loading significantly.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (Niki Lauda Turn) - end of main straight with DRS Zone 3',
    secondaryZones: ['Turn 3 (Schlossgold) - end of DRS Zone 1', 'Turn 4 (Rauch Turn) - continuation of T3 battles'],
    factors: [
      'Three DRS zones create multiple overtaking opportunities per lap',
      'Heavy braking into T1 (~310+ to ~70 km/h) is ideal for late-braking moves',
      'T3 offers secondary opportunity with heavy braking from ~290 km/h',
      'T4 blind entry makes defense easier despite late-braking potential',
      'High-speed S3 complex nearly impossible to attack - dirty air costs significant time',
      '2024 race saw ~85 completed overtakes (estimated from broadcast data)',
      'Short lap time means more DRS opportunities per race distance',
    ],
    recommendation:
      'Focus on DRS zones for passing opportunities. T1 offers the best chance with heavy braking and wide entry. T3 provides secondary option. Track position through S3 high-speed corners is nearly impossible to attack due to dirty air effects. Undercut potential moderate due to short pit lane time loss (~18-19s, typical estimate).',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Late June racing typically brings warm, dry conditions with occasional afternoon thunderstorm risk due to Alpine location. The Styrian mountains can create localized weather patterns.',
      airTemperature: {
        max: '30°C',
        min: '20°C',
        raceTime: '28°C',
      },
      rainProbability: 'Low (~20%) - rapid weather changes possible due to mountain location',
      wind: 'Variable, light - westerly to northwesterly typical',
      humidity: '50% average',
    },
    sessionConditions: {
      fp1: '28°C, mix of clouds and sun, slight early morning rain risk, light westerly gusts to 30 kph',
      fp2: '28°C, high clouds, decreasing rain chance, light westerly wind',
      fp3: '28°C, dawn clouds clearing to sunny, light northwesterly wind',
      qualifying: '29°C, mainly sunny and dry, light northwesterly wind',
      race: '30°C, sunny with developing cumulus clouds in afternoon, light easterly wind, 20% rain chance',
    },
    impact:
      '2025 weekend saw progressively increasing temperatures (28→29→30°C). Stable conditions throughout, which is relatively unusual for this Alpine venue. Teams should always prepare for rapid weather changes given the mountainous terrain. 700m altitude means reduced air density affects both aerodynamics and engine cooling capacity.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:05.619',
      driver: 'Carlos Sainz',
      year: 2020,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:04.314',
        driver: 'VER',
        note: 'Verstappen pole before Verstappen-Norris collision in race',
      },
      {
        year: 2025,
        time: '1:03.971',
        driver: 'NOR',
        note: 'Pole by 0.521s margin (from weekend dataset)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:03.971' },
        { position: 2, driver: 'LEC', time: '1:04.492' },
        { position: 3, driver: 'PIA', time: '1:04.554' },
        { position: 4, driver: 'HAM', time: '1:04.582' },
        { position: 5, driver: 'RUS', time: '1:04.763' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2', // From weekend timing data
      sectors: [
        { sector: 1, time: '16.299s', driver: 'NOR' },
        { sector: 2, time: '28.737s', driver: 'NOR' },
        { sector: 3, time: '19.458s', driver: 'NOR' },
      ],
      overallIdealLap: '1:04.494',
    },
    // Race pace benchmarks derived from race timing analysis
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '1:09.68', // From race analysis
        gaps: [
          { driver: 'PIA', gap: '+0.03s' },
          { driver: 'LEC', gap: '+0.27s' },
          { driver: 'HAM', gap: '+0.44s' },
          { driver: 'RUS', gap: '+0.91s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '1:10.19', // From race analysis
        gaps: [
          { driver: 'NOR', gap: '+0.05s' },
          { driver: 'RUS', gap: '+0.30s' },
          { driver: 'SAI', gap: '+0.35s' },
          { driver: 'PIA', gap: '+0.37s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Leclerc', speed: '327 km/h' },
        range: '320-327 km/h',
      },
      race: {
        withDRS: 'Up to 330 km/h (Piastri)',
        withoutDRS: '~306 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop Medium → Hard preferred (first stop lap 20-25)',
      factors: [
        'Short lap time (~64s) makes pit stop time loss (~18-19s typical) relatively more significant',
        'One-stop viable with Hard compound (2025 analysis: Lawson completed 38-lap Hard stint)',
        'Medium → Hard → Medium possible for aggressive two-stop pace',
        'All three compounds proved viable in 2025 - only 5 drivers started on Softs (analysis)',
        'Norris early pit on lap 20 strategically mitigated intra-team battle with Piastri (2025 analysis)',
        'Three DRS zones enable overtaking, reducing need for aggressive undercuts',
        'Track position critical in S3 where dirty air significantly costs time',
      ],
    },
    keyStrategicFactors: [
      'Altitude affects PU cooling and ERS regeneration strategies',
      'Three consecutive straights exceed single ERS charge capacity - deployment crucial',
      'Safety car probability moderate-high (~35-40% historical trend) - T2 and T4 historically incident-prone',
      'VSC probability moderate-high (~45-55% historical trend) - multiple corners with gravel trap proximity',
      '2025 race ran 70 laps after aborted start (per race classification)',
      'Lap 1 collision between Verstappen and Antonelli at T2 triggered Safety Car (2025 analysis)',
    ],
    safetyCarLikelihood: 'Moderate-High (~35-40% historical SC, ~45-55% VSC - based on historical trends)',
    historicalNotes: [
      '2025: Norris wins - McLaren 1-2 with dominant pace',
      '2025: Verstappen-Antonelli collision lap 1 - both DNF (Antonelli 3-place penalty)',
      '2024: Russell inherited win after Verstappen-Norris collision lap 64',
      '2023: Verstappen beat Leclerc by 5+ seconds',
      '2022: Leclerc\'s second win of the season',
      '2020: Circuit hosted COVID double-header (Styrian GP + Austrian GP)',
      '1984: Niki Lauda - only Austrian to win Austrian GP',
      'Circuit evolution: Österreichring (1970-87) → A1-Ring (1997-03) → Red Bull Ring (2014-present)',
      'Max Verstappen: 5 wins at this venue (most of any driver)',
    ],
  },

  // =========================================================================
  // Defining Characteristics - CONDENSED for proper tooltip display
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Shortest Lap',
      icon: 'clock',
      description:
        'Produces F1\'s quickest lap times despite being only the 5th shortest circuit by distance.',
    },
    {
      tag: 'High Altitude',
      icon: 'mountain',
      description:
        'At 700m elevation, air density drops ~7%, reducing both drag and downforce proportionally.',
    },
    {
      tag: 'Power Circuit',
      icon: 'zap',
      description:
        'Three consecutive straights stress ERS deployment beyond single battery charge capacity.',
    },
    {
      tag: 'Fewest Corners',
      icon: 'route',
      description:
        'Just 10 corners — the simplest F1 layout. T2, T5, and T8 are taken flat in qualifying.',
    },
    {
      tag: 'Overtaking Paradise',
      icon: 'flag',
      description:
        'Three DRS zones with heavy braking at T1 and T3 create multiple passing opportunities.',
    },
  ],

  fuelEffectPerKg: 0.031,
}
