import type { TrackIntelligence } from './types'

/**
 * Dutch Grand Prix - Circuit Zandvoort
 * Round 15 of the 2025 FIA Formula 1 World Championship
 * 
 * A legendary seaside circuit that returned to the F1 calendar in 2021 after a 36-year
 * absence. Famous for its unique banked corners at Turn 1 (Tarzanbocht, 18°) and Turn 14
 * (Arie Luyendijk, ~18°), Zandvoort is a medium-high downforce track with maximum tyre
 * stress. The coastal location creates unpredictable weather, while the narrow layout
 * and limited overtaking opportunities make qualifying position crucial.
 */
export const zandvoortTrackIntelligence: TrackIntelligence = {
  circuitId: 'zandvoort',
  round: 15,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit Zandvoort',
    country: 'Netherlands',
    location: 'Zandvoort, Netherlands',
    grandPrixName: 'Dutch Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1952,
    description:
      'A legendary seaside circuit that returned to the F1 calendar in 2021 after a 36-year absence. Famous for its unique banked corners at Turn 1 (Tarzanbocht, 18°) and Turn 14 (Arie Luyendijk, ~18°), Zandvoort is a medium-high downforce track dominated by medium-speed corners. The coastal North Sea location creates unpredictable, rapidly changing weather conditions, while the narrow layout and limited overtaking opportunities make qualifying position crucial. The "Orange Army" of Dutch fans creates one of the most electrifying atmospheres on the calendar.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.259,
      miles: 2.646,
    },
    raceDistance: {
      km: 306.587,
      miles: 190.512,
    },
    numberOfLaps: 72,
    numberOfCorners: 14,
    drsZones: 2,
    lapRecord: {
      time: '1:11.097',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '25.0 psi',
        rear: '22.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,           // Moderate - key zones at T3 and T14 exits
    tyreStress: 5,         // MAXIMUM - highest on calendar, explains conservative compounds
    asphaltGrip: 3,        // Medium grip with significant track evolution
    asphaltAbrasion: 3,    // Medium surface abrasiveness
    braking: 3,            // Moderate - three primary heavy braking zones
    lateral: 4,            // High - especially punishing on left-side tyres through banking
    downforce: 4,          // High - medium-high wing configurations typical
    trackEvolution: 4,     // Significant rubber build-up throughout weekend
  },

  energyProfile: {
    longitudinal: 'Medium',   // Moderate braking demands
    lateral: 'High',          // Sustained cornering through banking
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
        'End of main straight into the iconic 18° banked Turn 1 (Tarzanbocht) hairpin, then two short full-throttle sections through Turn 2 and the 18° banked Turn 3 (Hugenholtzbocht). The banking allows unique racing lines and requires excellent traction on exit.',
      keyFeatures: [
        'Primary overtaking zone at Turn 1 (Tarzanbocht)',
        'Heavy braking from 300+ km/h into 18° banked hairpin',
        'Turn 3 (Hugenholtzbocht) - 18° banked corner',
        'Multiple racing lines possible due to banking at T1 and T3',
        'Critical traction zones on T1 and T3 exits',
      ],
      criticalCorners: [
        'T1 (Tarzanbocht) - 18° banked hairpin, heavy braking, primary overtaking opportunity',
        'T3 (Hugenholtzbocht) - 18° banking, unique racing lines, exit speed critical',
      ],
    },
    {
      sector: 2,
      color: '#1E88E5',  // Blue
      corners: 'T4-T10',
      description:
        'The most technical sector featuring three medium-speed right corners and one medium-speed left corner. Pure downforce and mechanical grip territory with minimal straights. A short DRS zone concludes the sector.',
      keyFeatures: [
        'Most technical sector - minimal straights',
        'Sequence of medium-speed corners',
        'DRS Zone 1 (low effectiveness - too short)',
        'Pure downforce and mechanical grip territory',
        'Ferrari struggled here in 2025',
      ],
      criticalCorners: [
        'T7 (Hans Ernst Bocht) - Key left-hander breaking right-corner sequence',
        'T9 (Scheivlak) - High-speed right with blind entry, driver confidence critical',
      ],
    },
    {
      sector: 3,
      color: '#FDD835',  // Yellow
      corners: 'T11-T14',
      description:
        'Tight chicane (T11-12), fast right-hander T13, then the ~18° banked Turn 14 leading onto the main DRS-assisted straight. DRS Zone 2 is extremely powerful — activates after T13 and can remain open through the banked final corner.',
      keyFeatures: [
        'T11-12 chicane - secondary overtaking opportunity',
        'DRS opens after T13 and can remain open into banked T14',
        'DRS Zone 2 - extremely powerful',
        'T14 (Arie Luyendijk) - ~18° banked final corner',
        'Exit speed critical for main straight performance',
      ],
      criticalCorners: [
        'T11-12 (Chicane) - Heavy braking, secondary overtaking zone',
        'T14 (Arie Luyendijk) - ~18° banking, exit determines main straight speed',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Entry of Turn 10',
      activationPoint: '50m after Turn 10',
      deactivationPoint: 'Turn 11 braking zone',
      description:
        'Short DRS zone in Sector 2. Too brief for reliable overtaking — primarily useful for closing gaps rather than completing passes.',
      effectiveness: 'Low',
    },
    {
      zone: 2,
      detectionPoint: '20m after Turn 12',
      activationPoint: '40m after Turn 13',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'Primary overtaking opportunity. Extremely powerful due to medium-high wing configurations. DRS activates after T13 and can remain open through the banked final corner (T14) onto the main straight.',
      effectiveness: 'Very High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium-High',
      explanation:
        'Zandvoort demands medium-high downforce to maximize cornering speed through the technical Sector 2 sequence and banked corners at T1 (Tarzanbocht) and T3 (Hugenholtzbocht). McLaren ran high downforce with a deep narrow spoon lower plane (324 km/h top speed) while Red Bull ran lower downforce with a full-width lower plane (331 km/h). McLaren\'s approach paid off — trading ~7 km/h top speed for significant cornering advantage. DRS Zone 2 is extremely effective with loaded wings, creating the primary overtaking opportunity.',
    },
    tyreManagement: {
      compounds: ['C2 (Hard)', 'C3 (Medium)', 'C4 (Soft)'],
      allocation: 'Conservative compounds due to maximum tyre stress',
      primaryWearMechanism: 'Lateral stress through banked corners, especially left-side tyres',
      explanation:
        'Zandvoort has Pirelli\'s maximum tyre stress rating (5/5), explaining the conservative C2/C3/C4 compound selection. The banked corners at Turn 1 (Tarzanbocht), Turn 3 (Hugenholtzbocht), and Turn 14 put exceptional stress on left-side tyres. Hard compound showed best race consistency — Bearman completed 53 laps on Hards proving one-stop viability. Medium degraded faster but offered initial pace advantage.',
      strategicNote: 'Two-stop optimal (M-H-S or M-H-H). One-stop viable with careful management.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium initial grip with significant track evolution',
      impact: 'Rated 4/5 for evolution — grip improves dramatically throughout weekend. Late qualifying runs typically fastest. Banking can hold moisture after rain.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'High',
    primaryZone: 'Turn 1 (end of main straight with DRS Zone 2)',
    secondaryZones: ['Turn 11 chicane entry'],
    factors: [
      'Narrow circuit limits alternative racing lines',
      'DRS Zone 1 too short for reliable overtaking',
      'DRS Zone 2 extremely powerful — primary opportunity',
      'Track position paramount due to limited passing zones',
      'Qualifying performance critical',
      'Undercut highly effective due to track position value',
      'Banked corners create unique defensive/attacking opportunities',
    ],
    recommendation:
      'Focus on qualifying — track position is paramount. DRS Zone 2 into Turn 1 is the primary overtaking opportunity. The narrow layout punishes drivers stuck behind slower cars. Undercut strategy highly effective when fresh tyres provide track position.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Coastal, highly variable',
      airTemperature: {
        max: '20°C',
        min: '15°C',
        raceTime: '17°C',
      },
      rainProbability: 'High (coastal weather patterns)',
      wind: 'Moderate southwesterly from North Sea',
      humidity: 'High (70-85%)',
    },
    sessionConditions: {
      fp1: 'Wet — red flags due to incidents',
      fp2: 'Drying, continued rain threat',
      fp3: '16-18°C, cloudy, 80%+ rain chance',
      qualifying: '16-18°C, cloudy, showers threatened',
      race: '15-19°C, showers threatened, 60% rain chance, moderate SW wind',
    },
    impact:
      'Coastal North Sea location creates rapidly changing conditions within sessions. Sea breeze affects grip levels throughout the day. Damp patches particularly treacherous at banked corners — the Tarzanbocht (T1) banking caught Hamilton in 2025. Track dries quickly due to sea wind but banking can hold moisture longer.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:11.097',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    polePositions: [
      {
        year: 2021,
        time: '1:08.885',
        driver: 'VER',
        note: 'First Dutch GP since 1985',
      },
      {
        year: 2024,
        time: '1:09.673',
        driver: 'NOR',
        note: 'Ended Verstappen pole streak',
      },
      {
        year: 2025,
        time: '1:08.662',
        driver: 'PIA',
        note: 'All-time fastest lap at Zandvoort',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:08.662' },
        { position: 2, driver: 'NOR', time: '1:08.674' },
        { position: 3, driver: 'VER', time: '1:08.925' },
        { position: 4, driver: 'HAD', time: '1:09.208' },
        { position: 5, driver: 'RUS', time: '1:09.255' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '23.258s', driver: 'PIA' },
        { sector: 2, time: '24.365s', driver: 'VER' },
        { sector: 3, time: '20.819s', driver: 'PIA' },
      ],
      overallIdealLap: '1:08.542',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR (Retired Lap 65)',
        meanLapTime: '74.67s',
        gaps: [
          { driver: 'PIA', gap: '+0.01s' },
          { driver: 'VER', gap: '+0.60s' },
          { driver: 'HAD', gap: '+0.68s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '75.22s',
        gaps: [
          { driver: 'HAM', gap: '+0.32s' },
          { driver: 'RUS', gap: '+0.32s' },
          { driver: 'VER', gap: '+0.34s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'SAI/HUL', speed: '334 km/h' },
        range: '324-334 km/h',
      },
      race: {
        withDRS: 'Up to 342 km/h (Hulkenberg)',
        withoutDRS: '302-307 km/h (frontrunners)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop strategy optimal (M-H-S or M-H-H)',
      factors: [
        'Maximum tyre stress rating (5/5) favors multi-stop',
        'First stop window: Laps 18-28',
        'Second stop window: Laps 45-58',
        'Pit lane time loss approximately 19-22 seconds',
        'One-stop viable — Bearman ran 53 laps on Hards',
        'Undercut highly effective due to track position premium',
        'High Safety Car likelihood (3 in 2025) rewards strategic flexibility',
      ],
    },
    keyStrategicFactors: [
      'Track position paramount — limited overtaking outside DRS Zone 2',
      'Qualifying performance critical due to narrow circuit',
      'Left-side tyre management crucial through banked corners',
      'Safety Car timing can completely reshape race outcome',
      'Weather can change rapidly — coastal location unpredictable',
      'Hard compound showed best race consistency in 2025',
      'Ferrari\'s traction deficit (-4% full throttle vs leaders) proved costly',
    ],
    safetyCarLikelihood: 'High - narrow track, gravel traps, variable weather',
    historicalNotes: [
      '2025: Three Safety Cars (Hamilton crash L23, Leclerc retirement L52, Norris DNF L65)',
      '2025: Piastri wins, extends championship lead to 34 points over Norris',
      '2025: Hadjar first career podium (P3); Ferrari double DNF',
      '2025: Norris retired from P2 with engine failure — matching Piastri\'s pace',
      '2024: Norris wins, ends Verstappen\'s three-year home winning streak',
      '2021-2023: Verstappen won all three races since F1 return',
      '2026: Confirmed final year of current contract — uncertain future',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Banked Corners',
      icon: 'track',
      description: 'Iconic 18° banking at T1 (Tarzanbocht), T3 (Hugenholtzbocht), and T14 — unique on calendar',
    },
    {
      tag: 'Maximum Tyre Stress',
      icon: 'tyre',
      description: 'Pirelli\'s highest rating (5/5) — banked corners create extreme lateral loads',
    },
    {
      tag: 'Medium-High Downforce',
      icon: 'aero',
      description: 'Corner speed prioritized; similar demands to Hungary',
    },
    {
      tag: 'Powerful DRS',
      icon: 'overtake',
      description: 'DRS Zone 2 extremely effective due to loaded wing configurations',
    },
    {
      tag: 'Weather Variable',
      icon: 'weather',
      description: 'Coastal North Sea location creates rapidly changing, unpredictable conditions',
    },
    {
      tag: 'Orange Army',
      icon: 'track',
      description: 'Verstappen\'s home race creates iconic atmosphere with sea of orange supporters',
    },
  ],
}

