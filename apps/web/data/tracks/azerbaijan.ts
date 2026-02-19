import type { TrackIntelligence } from './types'

/**
 * Azerbaijan Grand Prix - Baku City Circuit
 * Round 17 of the 2025 FIA Formula 1 World Championship
 * 
 * One of the most unique challenges on the F1 calendar - a circuit of extreme contrasts.
 * The first two sectors feature conventional slow-speed city circuit character with tight
 * right-angle corners and the famous Castle section (Turn 8). Then comes Sector 3 with
 * the longest straight on the calendar (~2.2km). Often called "Monaco meets Monza."
 */
export const azerbaijanTrackIntelligence: TrackIntelligence = {
  circuitId: 'baku',
  round: 17,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Baku City Circuit',
    country: 'Azerbaijan',
    location: 'Baku, Azerbaijan',
    grandPrixName: 'Azerbaijan Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 2016,
    description:
      'The Baku City Circuit presents one of the most unique challenges on the Formula 1 calendar — a circuit of extreme contrasts. The first two sectors feature a conventional, slow-speed city circuit character with tight right-angle corners and the famous Castle section (Turn 8), one of the narrowest passages in F1. Then comes Sector 3, which is essentially the longest straight on the calendar, running from Turn 16 to Turn 1 along the Caspian Sea promenade. This extraordinary variance places immense demands on engineering teams who must balance adequate downforce for the slow sectors while minimizing drag for the 2km+ straight. Often referred to as "Monaco meets Monza," Baku has developed a reputation for dramatic, unpredictable races since its 2016 debut.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 6.003,
      miles: 3.730,
    },
    raceDistance: {
      km: 306.049,
      miles: 190.170,
    },
    numberOfLaps: 51,
    numberOfCorners: 20,
    drsZones: 2,
    lapRecord: {
      time: '1:43.009',
      driver: 'Charles Leclerc',
      year: 2019,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '27.0 psi',
        rear: '26.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 5,           // Maximum - critical corner exit from T16 onto 2.2km straight
    tyreStress: 3,         // Medium - moderate thermal demands
    asphaltGrip: 2,        // Low - street surface with limited grip
    asphaltAbrasion: 1,    // Minimum - low abrasion surface
    braking: 4,            // High - heavy braking into T1 from 340+ km/h
    lateral: 1,            // Minimum - right-angle corners, minimal sustained cornering
    downforce: 2,          // Low - must minimize drag for long straight
    trackEvolution: 5,     // Maximum - street surface rubbers in dramatically
  },

  energyProfile: {
    longitudinal: 'Maximum',  // Heavy braking and traction demands
    lateral: 'Minimum',       // Right-angle corners limit lateral forces
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#E10600',  // Red
      corners: 'T1-T7',
      description:
        'Medium-speed corners with braking emphasis. Four right-hand corners separated by short straights and one DRS-assisted longer straight. Heavy braking into Turn 1 from maximum speed defines this sector.',
      keyFeatures: [
        'Primary braking zone at T1 from 340+ km/h',
        'DRS Zone 1 ends here',
        'T2-T3-T4 sequence requires rhythm and precision',
        'Corner exits critical for momentum into short straights',
      ],
      criticalCorners: [
        'T1 - Primary overtaking zone, heavy braking from maximum speed',
        'T3-T4 - Medium-speed right-handers requiring precise turn-in',
      ],
    },
    {
      sector: 2,
      color: '#0090D0',  // Blue
      corners: 'T8-T15',
      description:
        'The slowest and most technical section featuring the famous Castle section (Turn 8) — one of the narrowest passages in F1, winding past Baku\'s medieval city walls. Driver confidence is paramount as walls punish mistakes instantly.',
      keyFeatures: [
        'Castle section (T8) - narrowest point on calendar',
        'Frequent crashes due to wall proximity',
        'Driver confidence paramount',
        'Traction out of slow corners critical',
      ],
      criticalCorners: [
        'T8 (Castle) - Extremely narrow, iconic section past medieval walls',
        'T15 - Deceptive entry, site of multiple qualifying incidents (Leclerc 2025)',
      ],
    },
    {
      sector: 3,
      color: '#FFD700',  // Yellow/Gold
      corners: 'T16-T20',
      description:
        'Essentially one massive straight — the longest on the F1 calendar (~2.2km). A bad exit from Turn 16 is extremely costly because it determines your speed all the way down the main straight. This is also where DRS Zone 1 operates, making straight-line efficiency and slipstream positioning decisive for both lap time and overtaking.',
      keyFeatures: [
        'Longest straight on F1 calendar (~2.2km)',
        'DRS is active on the main straight to maximise overtaking opportunities',
        'Primary overtaking opportunity',
        'Top speeds exceed 360 km/h with DRS and slipstream',
      ],
      criticalCorners: [
        'T16 - Exit speed determines entire sector time — most critical corner',
        'T20 - Final corner before main straight, requires precision',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Before Turn 16',
      activationPoint: 'After Turn 16',
      deactivationPoint: 'Turn 1 braking zone',
      description: 'Primary DRS zone on the main straight (the key overtaking tool).',
      effectiveness: 'Very High',
    },
    {
      zone: 2,
      detectionPoint: 'Before Turn 2',
      activationPoint: 'After Turn 2',
      deactivationPoint: 'Turn 3 braking zone',
      description: 'Shorter DRS zone on the T2→T3 straight; often riskier to complete passes.',
      effectiveness: 'Medium',
    },
  ],  

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Low',
      explanation:
        'Baku forces the most extreme compromise between downforce and drag on the calendar. Too much downforce results in a massive speed deficit on the 2.2km straight (sitting ducks for overtakes). Too little causes poor traction and braking stability in Sectors 1 and 2. Alpine ran Monza-spec minimum downforce but struggled massively in S1/S2 — the only cars lapped. Ferrari ran the most loaded configuration of top teams with 337 km/h top speed but strong FP2 pace. Haas\'s low-drag chassis allowed them to run more wing while Bearman still reached 361 km/h in race with DRS — the highest speed recorded. Hamilton was fastest in FP2 despite having the lowest top speed (337 km/h), proving that drag isn\'t everything at Baku.',
    },
    tyreManagement: {
      compounds: ['C4 (Hard)', 'C5 (Medium)', 'C6 (Soft)'],
      allocation: 'Softest available compounds',
      primaryWearMechanism: 'Traction and thermal cycling through stop-start corners',
      explanation:
        'Tyre management at Baku is relatively straightforward due to low lateral demands. The Hard compound showed virtually zero degradation when fuel-corrected in 2025 — incredibly consistent with almost no performance drop-off. The Medium crossed over with Hards after approximately 12 laps. The Soft offered higher initial performance but degraded rapidly, making it primarily a qualifying tyre at Baku.',
      strategicNote: 'One-stop dominant (Hard-Medium or Medium-Hard). Hards can comfortably run 40+ laps.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Low initial grip with massive track evolution',
      impact: 'Street surface sees minimal use outside race weekend. Grip improves 3-4 seconds lap time from start to finish of weekend. Rubbering in dramatically through sessions.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (end of 2.2km straight with DRS Zone 2)',
    secondaryZones: ['Turn 3 area (DRS Zone 1 assistance)'],
    factors: [
      'Longest straight on calendar provides excellent slipstream opportunities',
      'Two DRS zones but DRS trains problematic — following cars gain similar advantage',
      'Overtaking outside DRS zones extremely difficult due to wall proximity',
      'Track position critical despite straight-line overtaking opportunities',
      'Heavy braking into T1 creates late-braking opportunities',
      'Narrow Castle section makes defensive positioning easier',
    ],
    recommendation:
      'Focus on Turn 16 exit for optimal positioning on the 2.2km straight. Despite two DRS zones, track position remains valuable due to DRS train effect. Strategic pit timing (overcut viable) can be more effective than on-track battles through tight sectors.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Mostly dry, occasional showers possible',
      airTemperature: {
        max: '25°C',
        min: '18°C',
        raceTime: '21°C',
      },
      rainProbability: 'Low (occasional showers)',
      wind: 'Moderate northwesterly, gusts up to 50-60 km/h',
      humidity: 'Moderate (50-70%)',
    },
    sessionConditions: {
      fp1: '24°C, partly cloudy',
      fp2: '23°C, cloudy',
      fp3: '20°C, chance of showers',
      qualifying: '21°C, light rain drops during Q3',
      race: '21°C, mostly cloudy, windy (gusts 40-50 km/h)',
    },
    impact:
      'Wind plays a significant role at Baku due to the exposed seafront location along the Caspian Sea. The 2025 qualifying session saw light rain drops fall during Q3, contributing to chaos with the track surface described as "like ice" on the white lines by Kimi Antonelli. The coastal location means conditions can change rapidly, and wind gusts can significantly affect car stability, particularly on the exposed main straight.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:43.009',
      driver: 'Charles Leclerc',
      year: 2019,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:40.203',
        driver: 'LEC',
        note: 'Qualifying record',
      },
      {
        year: 2024,
        time: '1:41.186',
        driver: 'LEC',
      },
      {
        year: 2025,
        time: '1:41.117',
        driver: 'VER',
        note: '6 red flags in qualifying (F1 record)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:41.117' },
        { position: 2, driver: 'SAI', time: '1:41.595' },
        { position: 3, driver: 'LAW', time: '1:41.707' },
        { position: 4, driver: 'ANT', time: '1:41.717' },
        { position: 5, driver: 'RUS', time: '1:42.070' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '35.117s', driver: 'HAM' },
        { sector: 2, time: '42.577s', driver: 'NOR' },
        { sector: 3, time: '24.364s', driver: 'LAW' },
      ],
      overallIdealLap: '1:42.058',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '105.10s',
        gaps: [
          { driver: 'RUS', gap: '+0.15s' },
          { driver: 'SAI', gap: '+0.38s' },
          { driver: 'ANT', gap: '+0.40s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'PIA',
        meanLapTime: '108.0s',
        gaps: [
          { driver: 'SAI', gap: '+0.01s' },
          { driver: 'PER', gap: '+0.01s' },
          { driver: 'LEC', gap: '+0.03s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'LAW/RUS/ALO/STR', speed: '341 km/h' },
        range: '332-341 km/h',
      },
      race: {
        withDRS: 'Up to 361 km/h (Bearman, Haas)',
        withoutDRS: '326-329 km/h (frontrunners)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop strategy dominant (Hard → Medium or Medium → Hard)',
      factors: [
        'Optimal pit window: Laps 25-40',
        'Pit lane time loss approximately 21 seconds',
        'Hard compound showed virtually zero degradation when fuel-corrected',
        'Overcut viable — Russell\'s overcut on Sainz (Lap 40) proved effective',
        'Late pitters advantaged — Verstappen pitted Lap 40, had fresh Mediums for final stint',
        'Mediums crossed over with Hards after approximately 12 laps',
      ],
    },
    keyStrategicFactors: [
      'Track position critical despite DRS zones — DRS trains difficult to break',
      'One-stop dominant (Hard-Medium or Medium-Hard)',
      'Massive track evolution — lap times improved 3-4 seconds start to finish',
      'Safety Car likelihood high — 2025 had SC deployment on Lap 1 (Piastri crash)',
      'Overcut strategy viable due to low tyre degradation',
      'Soft primarily a qualifying tyre — not used in race by frontrunners',
    ],
    safetyCarLikelihood: 'High - tight corners and unforgiving barriers make incidents common',
    historicalNotes: [
      '2025: 6 red flags in qualifying (F1 record); Verstappen grand chelem (pole, every lap led, FL, win)',
      '2025: Piastri crashed Q3, jumped start, stalled, fell to last, crashed out Lap 1',
      '2025: Williams podium (Sainz P3) — first since rain-curtailed 2021 Belgian GP',
      '2024: Oscar Piastri wins his first Baku race',
      '2023: Pérez becomes first double winner at Baku; Leclerc sets qualifying record',
      '2021: Verstappen suffers tyre failure while leading; Pérez wins',
      '2017: Ricciardo wins from P10; Hamilton-Vettel Safety Car controversy',
      '2016: Rosberg wins inaugural race (as European GP)',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Longest Straight',
      icon: 'speed',
      description: '2.2km main straight — the longest on the F1 calendar',
    },
    {
      tag: 'Extreme Contrast',
      icon: 'track',
      description: '"Monaco meets Monza" — slow city sections combined with high-speed straight',
    },
    {
      tag: 'Track Evolution',
      icon: 'evolution',
      description: 'Maximum evolution (5/5) — street surface rubbers in dramatically',
    },
    {
      tag: 'Castle Section',
      icon: 'track',
      description: 'Iconic narrow passage through medieval city walls at Turn 8',
    },
    {
      tag: 'Heavy Braking',
      icon: 'braking',
      description: 'Heavy braking demands (4/5), especially into T1 from 340+ km/h',
    },
    {
      tag: 'Unpredictable',
      icon: 'weather',
      description: 'History of dramatic, chaotic races with unexpected results',
    },
  ],

  fuelEffectPerKg: 0.032,
}
