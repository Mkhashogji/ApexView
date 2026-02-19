import type { TrackIntelligence } from './types'

/**
 * Hungarian Grand Prix - Hungaroring
 * Round 14 of the 2025 FIA Formula 1 World Championship
 * 
 * Known as "Monaco without the barriers", the Hungaroring is a maximum downforce
 * circuit where track position is paramount. First F1 circuit behind the Iron Curtain
 * (1986), it features relentless corner sequences that test car balance and driver
 * fitness. Overtaking is extremely difficult, making strategy and qualifying crucial.
 */
export const hungaryTrackIntelligence: TrackIntelligence = {
  circuitId: 'hungaroring',
  round: 14,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Hungaroring',
    country: 'Hungary',
    location: 'Mogyoród, Budapest, Hungary',
    grandPrixName: 'Hungarian Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1986,
    description:
      'Known as "Monaco without the barriers", the Hungaroring is a maximum downforce circuit where track position is paramount. Built in just 8 months, it was the first F1 circuit behind the Iron Curtain when it debuted in 1986. The relentless succession of medium-speed corners — particularly through Sector 2 — creates among the highest sustained lateral g-forces on the calendar. With full-throttle running low (roughly 45-55% depending on metric, second only to Monaco in some datasets) and extremely limited overtaking opportunities, races are won in the pit lane and strategy room. Hot August conditions add physical challenge, while significant track evolution transforms grip levels from Friday to Sunday.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.381,
      miles: 2.722,
    },
    raceDistance: {
      km: 306.63,
      miles: 190.531,
    },
    numberOfLaps: 70,
    numberOfCorners: 14,
    drsZones: 2,
    lapRecord: {
      time: '1:16.627',
      driver: 'Lewis Hamilton',
      year: 2020,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25° (event-dependent)',
        rear: '-2.00° (event-dependent)',
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
    traction: 4,           // High - continuous slow-speed corner exits
    tyreStress: 3,         // Moderate - medium-high wear on softs in hot conditions
    asphaltGrip: 3,        // Moderate - significant improvement as rubber builds
    asphaltAbrasion: 3,    // Moderate - surface reasonably kind to tyres
    braking: 3,            // Moderate - fewer heavy braking zones but high thermal loads
    lateral: 3,            // Moderate - continuous medium-speed corners
    downforce: 5,          // MAXIMUM - comparable to Monaco, highest wing levels
    trackEvolution: 4,     // Significant - dusty initial conditions transform dramatically
  },

  energyProfile: {
    longitudinal: 'Medium',   // Moderate braking demands
    lateral: 'Medium',        // Consistent load through corners
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#E53935',  // Red
      corners: 'T1-T3',
      description:
        'Fastest sector containing both DRS zones and the primary overtaking opportunity. Main straight into Turn 1 hairpin features heavy braking from 317 km/h to 95 km/h — the circuit\'s only realistic passing zone.',
      keyFeatures: [
        'Main straight with DRS Zone 1',
        'Turn 1 hairpin - primary overtaking zone',
        'Heavy braking: 120-122m, peak 4.8g deceleration',
        'Turn 2 with secondary DRS zone approach',
        'Turn 3 downhill sweeper exceeding 160 km/h',
      ],
      criticalCorners: [
        'T1 (Hairpin) - Heavy braking from 317 to 95 km/h, circuit\'s main passing zone',
        'T3 - Downhill sweeper, must carry speed for sector time',
      ],
    },
    {
      sector: 2,
      color: '#1E88E5',  // Blue
      corners: 'T4-T10',
      description:
        'Most technical sector with among the highest sustained lateral acceleration demands on the calendar. Relentless succession of medium-speed corners with continuous direction changes — setup imbalances immediately punished.',
      keyFeatures: [
        'One of the highest lateral g-force sectors on F1 calendar',
        'Turn 4 at hilltop - one of circuit\'s quickest corners',
        'Turns 6-10 relentless medium-speed sequence',
        'Continuous direction changes demand supreme car balance',
        'Rhythm and flow essential - errors compound',
        'Downforce and mechanical grip absolutely crucial',
      ],
      criticalCorners: [
        'T4 - Fast corner at hilltop, sets up downhill sequence',
        'T6-T10 - Continuous medium-speed sequence, no recovery room',
      ],
    },
    {
      sector: 3,
      color: '#FDD835',  // Yellow
      corners: 'T11-T14',
      description:
        'Shortest sector featuring two 180-degree complexes. Turn 14 exit speed is crucial for main straight performance and defending into Turn 1. DRS detection zone located before Turn 14.',
      keyFeatures: [
        'Two 180-degree corner complexes',
        'Turn 11 critical for carrying momentum',
        'Turns 12-13 first 180-degree complex',
        'Turn 14 exit speed crucial for main straight',
        'DRS detection point before Turn 14 (controls both zones)',
        'Final sector defines lap time and vulnerability',
      ],
      criticalCorners: [
        'T12-T13 - First 180-degree complex, tests patience',
        'T14 - Final corner, exit determines main straight speed',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '5m before Turn 14',
      activationPoint: 'Main straight',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'Primary DRS zone on main straight. Highly effective due to maximum-downforce wing configurations creating large speed differentials. The only realistic overtaking opportunity on the circuit. Detection point (5m before T14) is shared with Zone 2.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: '5m before Turn 14 (shared with Zone 1)',
      activationPoint: 'Short straight to Turn 2',
      deactivationPoint: 'Turn 2 braking zone',
      description:
        'Secondary DRS zone on short straight between Turns 1 and 2. Shares the same detection point as Zone 1 (before Turn 14). Useful for completing moves started at Turn 1 but rarely sufficient for independent overtakes.',
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
        'Hungaroring demands the highest wing levels of the season — comparable to Monaco. Teams run aggressive "dirty downforce" configurations where drag penalty is fully accepted. McLaren\'s 2024/2025 wing surprised the paddock with unprecedented load levels. Lap time gained through corners far outweighs straight-line losses. Top speeds range 314-323 km/h (among the lowest of season — only Monaco is typically lower). Williams achieved highest top speed (323 km/h) but lacked corner speed; Alpine/Ferrari ran maximum downforce at 304-315 km/h.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard soft-bias allocation',
      primaryWearMechanism: 'Thermal degradation and sustained cornering load; rears can overheat on traction, while the front-left often sees significant load over a stint',
      explanation:
        'High track temperatures (45-55°C) stress tyres significantly. Soft compound loses peak grip quickly in hot conditions (optimal 15-18 laps). Medium provides good balance (25-32 laps). Hard shows exceptional durability — Antonelli completed a 48-lap stint in 2025. Protecting both rear tyres (traction stress) and front-left (cornering load) through Sector 2 is crucial for stint length.',
      strategicNote: 'Two-stop optimal (M-H-H or M-H-S). One-stop viable with excellent tyre management.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Moderate initial grip with significant track evolution',
      impact: 'Circuit unused outside F1 weekends results in dusty initial conditions. Grip transforms dramatically from Friday to Sunday. Rated 4/5 for evolution.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Very High',
    primaryZone: 'Turn 1 hairpin (end of main straight)',
    secondaryZones: ['Turn 2 (continuation of Turn 1 battle)'],
    factors: [
      'One of the most difficult circuits for on-track overtaking',
      '"Monaco without the barriers" — track position paramount',
      'Only one realistic passing zone (Turn 1 hairpin)',
      'Most overtakes require significant tyre delta from strategy',
      'DRS highly effective due to draggy wing configurations',
      'Successful pass requires major grip advantage or driver error',
      'Undercut is the primary weapon for position changes',
      'Total overtakes 2024: just 65 (among lowest on calendar)',
    ],
    recommendation:
      'Focus on qualifying — track position is paramount. Strategy is the primary method to gain positions. The undercut is extremely powerful at Hungaroring (Schumacher\'s famous 1998 3-stop victory demonstrated this). A successful on-track pass typically requires a significant tyre delta.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot, humid summers with afternoon thunderstorm potential',
      airTemperature: {
        max: '31°C',
        min: '16°C',
        raceTime: '27°C',
      },
      rainProbability: 'Moderate (30-40%)',
      wind: 'Light to moderate',
      humidity: 'Moderate to high (50-70%)',
    },
    sessionConditions: {
      fp1: '28°C, mainly sunny',
      fp2: '28°C, slight afternoon shower chance',
      fp3: '27°C, sunny morning, cloudier afternoon',
      qualifying: '28°C, sunny',
      race: '27°C, high overnight rain chance, mostly cloudy, drying track expected',
    },
    impact:
      'Hot August conditions create exceptional thermal challenges. Track temperatures reach 45-55°C (up to 60°C in extreme cases like FP1 2024). High temperatures increase rear tyre degradation significantly. Brake temperatures challenging due to limited airflow through corners. Afternoon thunderstorms can dramatically alter strategy. Cooler evening temperatures can help tyre life in closing laps.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:16.627',
      driver: 'Lewis Hamilton',
      year: 2020,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:16.609',
        driver: 'HAM',
      },
      {
        year: 2024,
        time: '1:15.227',
        driver: 'NOR',
      },
      {
        year: 2025,
        time: '1:15.372',
        driver: 'LEC',
        note: 'One of closest-ever Q3s — top 10 within 0.543s',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'LEC', time: '1:15.372' },
        { position: 2, driver: 'PIA', time: '1:15.398' },
        { position: 3, driver: 'NOR', time: '1:15.413' },
        { position: 4, driver: 'RUS', time: '1:15.425' },
        { position: 5, driver: 'ALO', time: '1:15.481' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '27.637s', driver: 'HAM' },
        { sector: 2, time: '26.565s', driver: 'NOR' },
        { sector: 3, time: '21.342s', driver: 'PIA' },
      ],
      overallIdealLap: '1:15.544',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'PIA',
        meanLapTime: '81.05s',
        gaps: [
          { driver: 'NOR', gap: '+0.22s' },
          { driver: 'RUS', gap: '+0.29s' },
          { driver: 'LEC', gap: '+0.57s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '83.36s',
        gaps: [
          { driver: 'PIA', gap: '+0.04s' },
          { driver: 'HAM', gap: '+0.21s' },
          { driver: 'LEC', gap: '+0.27s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'ALB', speed: '323 km/h' },
        range: '315-323 km/h',
      },
      race: {
        withDRS: 'Up to 331 km/h',
        withoutDRS: '293-310 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop strategy optimal (M-H-H or M-H-S)',
      factors: [
        'First stop window: Lap 17-20',
        'Second stop window: Lap 40-46',
        'Pit lane time loss approximately 20-21 seconds',
        'Undercut extremely powerful — can be race-defining',
        'One-stop viable with excellent tyre management (Norris won 2025 on M-H)',
        'Hard compound exceptional durability (48-lap stint achieved 2025)',
        'Track position paramount — strategy primary method for position gains',
      ],
    },
    keyStrategicFactors: [
      'Track position paramount — overtaking extremely difficult',
      'Undercut critical weapon — Schumacher\'s 1998 3-stop masterclass',
      'Qualifying performance crucial due to limited passing opportunities',
      'High ambient temperatures stress tyres and brakes',
      'Significant track evolution — Friday pace misleading',
      'DRS more effective than expected due to high-drag wings',
      'Plank wear potential issue — Leclerc compromised in 2025 from Lap 9',
    ],
    safetyCarLikelihood: 'Moderate - limited run-off but circuit generally forgiving',
    historicalNotes: [
      '2025: McLaren\'s 200th F1 victory — Norris wins 0.7s battle with Piastri',
      '2025: Leclerc took pole but plank wear issues (FS1 mode) from Lap 9',
      '2025: Piastri closed 9-second gap in final stint but couldn\'t pass',
      '2024: Piastri\'s first F1 victory after team orders controversy',
      '2021: Ocon\'s maiden victory after chaotic first-lap incident',
      '2006: Button\'s breakthrough maiden F1 victory',
      '1998: Schumacher\'s masterclass 3-stop undercut victory',
      '1986: Piquet wins first race behind the Iron Curtain',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Maximum Downforce',
      icon: 'gauge',
      description: 'Highest wing levels of season (5/5) — comparable to Monaco, drag penalty fully accepted',
    },
    {
      tag: 'Strategic Circuit',
      icon: 'strategy',
      description: '"Monaco without barriers" — races won in pit lane, undercut is primary weapon',
    },
    {
      tag: 'Extreme Lateral',
      icon: 'track',
      description: 'Sector 2 has highest sustained lateral g-forces on calendar — tests car balance',
    },
    {
      tag: 'Track Evolution',
      icon: 'evolution',
      description: 'Dusty initial conditions transform dramatically — Friday pace misleading',
    },
    {
      tag: 'Thermal Critical',
      icon: 'thermometer',
      description: 'Hot August conditions (45-55°C track) demand exceptional thermal management',
    },
    {
      tag: 'Hamilton\'s Circuit',
      icon: 'trophy',
      description: 'Lewis Hamilton holds most wins (8), poles (9), and podiums (13) at Hungary',
    },
  ],

  fuelEffectPerKg: 0.035,
}
