import type { TrackIntelligence } from './types'

/**
 * Abu Dhabi Grand Prix - Yas Marina Circuit
 * Round 24 of the 2025 FIA Formula 1 World Championship
 * 
 * The season finale venue featuring a unique twilight race. Redesigned in 2021
 * to improve racing, the circuit rewards well-balanced cars and offers multiple
 * aerodynamic setup philosophies. Two DRS zones provide genuine overtaking opportunities.
 */
export const abuDhabiTrackIntelligence: TrackIntelligence = {
  circuitId: 'yas_marina',
  round: 24,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Yas Marina Circuit',
    country: 'UAE',
    location: 'Abu Dhabi, UAE',
    grandPrixName: 'Abu Dhabi Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 2009,
    description:
      'The Yas Marina Circuit concludes the Formula 1 season in spectacular fashion under the Abu Dhabi twilight. This medium-speed, complete track features a unique combination of fast flowing corners and tight, Monaco-like technical sections. Redesigned in 2021 to improve racing, the circuit allows for different aerodynamic setup philosophies — teams can choose between low drag for straight-line speed or higher downforce for the technical Sector 3. With two substantial DRS zones, overtaking is more achievable than at most circuits, though DRS trains can still form. The track rewards well-balanced cars with no specific weaknesses, making it the perfect stage for season-deciding battles.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.281,
      miles: 3.281,
    },
    raceDistance: {
      km: 306.183,
      miles: 190.253,
    },
    numberOfLaps: 58,
    numberOfCorners: 16,
    drsZones: 2,
    lapRecord: {
      time: '1:25.637',
      driver: 'Kevin Magnussen',  // Haas Ferrari, set on Lap 57 of 2024 race
      year: 2024,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-2.00°',
      },
      minStartingPressures: {
        front: '23.5 psi',
        rear: '21.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,
    tyreStress: 3,        // Moderate - unlike Qatar's 5
    asphaltGrip: 3,
    asphaltAbrasion: 3,
    braking: 4,
    lateral: 3,           // Medium - unlike Qatar's 5
    downforce: 3,         // Flexible - teams can choose philosophy
    trackEvolution: 4,
  },

  energyProfile: {
    longitudinal: 'Medium',   // Unlike Qatar's 'Minimum'
    lateral: 'Medium',        // Unlike Qatar's 'Maximum'
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
        'Contains the fastest corners of the circuit. Turn 1 is particularly tricky — drivers must judge the correct braking point and approach the corner correctly to avoid losing speed on exit or running wide. Good downforce is essential for this sector.',
      keyFeatures: [
        'High-speed corner complex',
        'Critical T1 braking zone',
        'Requires strong front-end grip',
        'Exit speed crucial for DRS zone',
      ],
      criticalCorners: [
        'T1 - Heavy braking from main straight, sets up entire sector',
        'T5 - Exit speed determines DRS effectiveness into S2',
      ],
    },
    {
      sector: 2,
      color: '#0066FF',  // Blue
      corners: 'T6-T9',
      description:
        'The fastest segment of the circuit — essentially two straights connected by a chicane, with a hairpin leading into the first straight. Low drag is advantageous here. This sector contains both DRS zones and is where most overtaking occurs.',
      keyFeatures: [
        'Two long straights',
        'Both DRS zones located here',
        'Primary overtaking opportunities',
        'Low drag setup beneficial',
      ],
      criticalCorners: [
        'T6/T7 - Chicane, key overtaking spot using DRS Zone 1',
        'T8/T9 - Hairpin complex, traction out of T9 critical',
      ],
    },
    {
      sector: 3,
      color: '#FFD700',  // Yellow/Gold
      corners: 'T10-T16',
      description:
        'The slowest sector with multiple slow-speed corners that make it very similar to Monaco. Downforce, mechanical grip, and car agility are king here. Setup compromises for straight-line speed in Sector 2 are punished in this technical section.',
      keyFeatures: [
        'Monaco-like slow corners',
        'Hotel section (T11-T14) demanding',
        'Mechanical grip critical',
        'Car agility determines pace',
      ],
      criticalCorners: [
        'T11-T14 - Hotel section, tight technical complex',
        'T14 - Hotel Hairpin, tightest corner on circuit',
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
      detectionPoint: 'After Turn 5',
      activationPoint: 'Before Turn 6',
      deactivationPoint: 'Turn 6/7 chicane entry',
      description:
        'Often used to prepare an attack rather than complete a pass. Getting alongside through this zone sets up the decisive move using Zone 2 on the following lap or into Turn 6.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'After Turn 9',
      activationPoint: 'Start of main straight',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'The primary overtaking zone. The long main straight combined with heavy braking into Turn 1 creates the best passing opportunity on the circuit.',
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
        'Abu Dhabi uniquely allows for varied aerodynamic philosophies. Teams can choose high downforce for Sectors 1 and 3 at the cost of straight-line speed, or run low drag to dominate Sector 2 while managing the technical sections. Red Bull typically runs lower drag, McLaren and Mercedes prefer higher downforce, while Ferrari often seeks a balanced compromise.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard middle-range compounds',
      primaryWearMechanism: 'Balanced longitudinal and lateral forces',
      explanation:
        'Tyre management at Yas Marina is significantly easier than at Qatar. The moderate lateral loads and cooling opportunities on the straights mean degradation is manageable. Hard tyres showed excellent durability in 2025, lasting 40+ laps with minimal drop-off. Track evolution throughout the weekend rewards later runs.',
      strategicNote: 'Both one-stop and two-stop strategies are viable — pace delta determines optimal choice.',
    },
    surfaceCharacteristics: {
      gripLevel: 'High initial grip with good evolution',
      impact: 'Smooth surface allows aggressive kerb usage in most corners',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1 (end of main straight with DRS Zone 2)',
    secondaryZones: ['Turn 6 chicane (DRS Zone 1)', 'Turn 5 exit (no DRS)'],
    factors: [
      'Two effective DRS zones provide genuine passing opportunities',
      'Long main straight into heavy T1 braking is primary overtaking spot',
      'DRS trains can form when multiple cars are within 1 second',
      'Defending cars also gain DRS, complicating attacks',
      'Dirty air effect is moderate — less severe than flowing circuits like Qatar',
      'Strategic undercuts remain effective due to track evolution',
    ],
    recommendation:
      'Qualifying position matters but is not as critical as at Qatar. Two DRS zones and varied strategy options mean overtaking is achievable. Focus on tyre management to create pace advantage windows.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Sunny and dry (twilight race)',
      airTemperature: {
        max: '28°C',
        min: '19°C',
        raceTime: '21-22°C',
      },
      rainProbability: '0% (virtually never rains)',
      wind: 'Light northerly winds',
      humidity: 'Moderate',
    },
    sessionConditions: {
      fp1: '26-27°C, afternoon heat',
      fp2: '23-24°C, evening session',
      fp3: '25-26°C, afternoon',
      qualifying: '22-23°C, twilight conditions',
      race: '21-22°C, day-to-night transition',
    },
    impact:
      'Consistent conditions throughout the weekend allow for reliable setup optimization. The twilight race means cooler track temperatures during qualifying and the race compared to daytime practice sessions, slightly reducing tyre stress and improving grip.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:25.637',
      driver: 'Kevin Magnussen',  // Haas Ferrari, set on Lap 57 of 2024 race
      year: 2024,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:22.595',
        driver: 'NOR',  // McLaren Mercedes, Q3 pole lap
      },
      {
        year: 2025,
        time: '1:22.207',
        driver: 'VER',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:22.207' },
        { position: 2, driver: 'NOR', time: '1:22.408' },
        { position: 3, driver: 'PIA', time: '1:22.437' },
        { position: 4, driver: 'RUS', time: '1:22.645' },
        { position: 5, driver: 'LEC', time: '1:22.730' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',  // Sector times from FP2, not Qualifying
      sectors: [
        { sector: 1, time: '16.998s', driver: 'NOR' },
        { sector: 2, time: '36.093s', driver: 'VER' },
        { sector: 3, time: '29.904s', driver: 'NOR' },
      ],
      overallIdealLap: '1:22.995',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '88.49s',
        gaps: [
          { driver: 'LEC', gap: '+0.11s' },
          { driver: 'VER', gap: '+0.16s (One Stop Strategy)' },
          { driver: 'PIA', gap: '+0.35s (One Stop Strategy)' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '88.49s',
        gaps: [
          { driver: 'SAI', gap: '+0.11s' },
          { driver: 'LEC', gap: '+0.46s' },
          { driver: 'HAM', gap: '+0.50s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'TSU', speed: '333 km/h' },
        range: '326-333 km/h',
      },
      race: {
        withDRS: 'Up to 349 km/h (in traffic)',
        withoutDRS: '313-316 km/h (frontrunners)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One or two stops viable',
      factors: [
        'Hard tyres showed excellent durability (40+ laps possible)',
        'One-stop preserves track position but requires tyre management',
        'Two-stop offers fresher tyres and faster lap times',
        'Undercut potential high due to track evolution',
        'Pit lane time loss approximately 21-22 seconds',
      ],
    },
    keyStrategicFactors: [
      'Qualifying position important but not critical — overtaking is possible',
      'Both one-stop and two-stop strategies can win depending on pace delta',
      'Track evolution rewards later pit stops',
      'Managing DRS trains important for overtaking',
      'Clean air provides significant advantage but is achievable through strategy',
    ],
    safetyCarLikelihood: 'Low - wide runoff areas reduce incident probability',
    historicalNotes: [
      '2025: Clean 58-lap race with no safety car',
      '2025: NOR clinched championship by just 2 points over VER',
      'One-stop and two-stop strategies both proved competitive',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Season Finale',
      icon: 'trophy',
      description: 'The championship-deciding venue — 2025 saw NOR clinch the title by just 2 points',
    },
    {
      tag: 'Setup Flexible',
      icon: 'sliders',
      description: 'Multiple aero philosophies viable — teams can optimize for straights or technical sections',
    },
    {
      tag: 'Good Overtaking',
      icon: 'overtake',
      description: 'Two effective DRS zones provide genuine passing opportunities into T1 and T6',
    },
    {
      tag: 'Complete Track',
      icon: 'balanced',
      description: 'Rewards well-balanced cars — fast corners, long straights, and technical sections all present',
    },
    {
      tag: 'Twilight Race',
      icon: 'twilight',
      description: 'Day-to-night transition creates spectacular visuals and evolving track conditions',
    },
  ],
}
