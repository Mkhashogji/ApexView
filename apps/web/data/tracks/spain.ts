import type { TrackIntelligence } from './types'

/**
 * Spanish Grand Prix - Circuit de Barcelona-Catalunya
 * Round 9 of the 2025 FIA Formula 1 World Championship
 *
 * The 2025 race marks the 35th and final 'Spanish Grand Prix' at Circuit de Barcelona-Catalunya.
 * The circuit will host the renamed 'Barcelona-Catalunya Grand Prix' in 2026, while Madrid
 * takes over the Spanish GP title from 2026-2035. Barcelona's F1 future beyond 2026 is uncertain.
 *
 * Circuit de Barcelona-Catalunya is one of the most comprehensive test circuits in
 * Formula 1, featuring a demanding mix of high-speed sweeping corners and technical
 * sections that test every aspect of car performance. Built as part of the 1992
 * Barcelona Olympics development program and opening in September 1991, the circuit
 * has hosted the Spanish Grand Prix since its inaugural F1 race.
 */
export const spainTrackIntelligence: TrackIntelligence = {
  circuitId: 'barcelona',
  round: 9,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit de Barcelona-Catalunya',
    country: 'Spain',
    location: 'Montmeló, Barcelona',
    grandPrixName: 'Spanish Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1991,
    description:
      "Circuit de Barcelona-Catalunya is one of the most comprehensive test circuits in Formula 1, featuring a demanding mix of high-speed sweeping corners and technical sections that test every aspect of car performance. Built as part of the 1992 Barcelona Olympics development program and opening in September 1991, the circuit has hosted the Spanish Grand Prix since its inaugural F1 race. The track is notorious for high tyre wear—clockwise layout means right-hand corners dominate, so the left tyres (especially front-left) take the beating. The 2023 layout modification removed the final chicane, reverting to the MotoGP configuration with a sweeping higher-speed final complex. The 2025 race marks the 35th and final 'Spanish GP' at Catalunya—the circuit hosts a renamed 'Barcelona-Catalunya GP' in 2026, but Madrid takes the Spanish GP title permanently.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.657,
      miles: 2.894,
    },
    raceDistance: {
      km: 307.236,
      miles: 190.899,
    },
    numberOfLaps: 66,
    numberOfCorners: 16,
    drsZones: 2,
    lapRecord: {
      time: '1:15.743',
      driver: 'Oscar Piastri',
      year: 2025,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '26.0 psi',
        rear: '22.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,         // Moderate - important but not critical
    tyreStress: 5,       // MAXIMUM - one of the most demanding circuits
    asphaltGrip: 3,      // Medium grip
    asphaltAbrasion: 4,  // High abrasion
    braking: 3,          // Moderate - two heavy braking zones
    lateral: 5,          // MAXIMUM - high-speed corners dominate
    downforce: 4,        // High - medium-high downforce required
    trackEvolution: 3,   // Medium - grip improves through weekend
  },

  energyProfile: {
    longitudinal: 'High',   // Multiple acceleration zones
    lateral: 'High',        // Sustained high-speed corners
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T3',
      description:
        "The fastest sector featuring the 1,047m main straight into the heavy T1-T2 chicane braking zone—the primary overtaking opportunity after DRS Zone 2 (the longest DRS zone). Continues through the full-throttle sweeping T3 (Repsol corner). In qualifying, T3 is taken flat-out, but during the race drivers typically lift through this corner to preserve tyres at minimal time cost.",
      keyFeatures: [
        'Main straight: 1,047m with DRS Zone 2 (primary passing zone)',
        'T1-T2 (Elf): Heavy braking chicane, primary overtaking spot',
        'T3 (Repsol): High-speed sweeper, flat in quali, lift in race',
        'Power-focused sector with low drag benefiting top speed',
        '~30% of lap time proportion (estimate)',
      ],
      criticalCorners: [
        'T1-T2 (Elf) - Heaviest braking from ~330 km/h to ~80 km/h',
        'T3 (Repsol) - ~240 km/h in quali, drivers lift in race to save tyres',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T4-T9',
      description:
        'A medium-speed sector with significant elevation changes featuring multiple demanding corners. The sector ends with flat-out T9 and DRS Zone 1 activates immediately after, setting up the T10 overtaking opportunity. Downforce is crucial through this section, but low drag helps on the straight connecting to Sector 3. The elevation changes can induce a snappy oversteer if the car balance is not optimized.',
      keyFeatures: [
        'T5 (Seat): Medium-speed corner feeding into infield',
        'T7-T8: Technical chicane with elevation change',
        'T9 (Campsa): High-speed left taken flat-out, ~250 km/h',
        'DRS Zone 1 activates after T9, leads to La Caixa braking zone',
        '~35% of lap time proportion (estimate)',
      ],
      criticalCorners: [
        'T5 (Seat) - ~160 km/h, 4th gear, feeds into infield complex',
        'T9 (Campsa) - Flat-out high-speed left, requires good downforce',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T10-T16', // FIA map shows 16 corners; some sources refer to final complex as T14
      description:
        "The slowest sector where drag has no importance, while every additional percentage of downforce helps significantly (with both sector time and tyre wear). Since the 2023 layout change, the final chicane was removed and replaced with the sweeping higher-speed final complex leading onto the main straight. Following closely here can heat the tyres quickly through dirty air.",
      keyFeatures: [
        'T10 (La Caixa): Heavy braking hairpin, potential overtaking spot',
        'T11-T13: Technical chicane complex requiring precision, front-left load builds',
        'Final complex (T14-T16, often referred to as T14/New Holland): Higher-speed lead-out to straight',
        'Downforce-critical sector, drag not important',
        '~35% of lap time proportion (estimate)',
      ],
      criticalCorners: [
        'T10 (La Caixa) - Hardest braking zone: ~300→70 km/h, 2nd gear',
        'Final complex - ~260 km/h sweeper, dirty air raises follower tyre temps',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Approach to T9 (~86m before T9 entry)',
      activationPoint: 'Immediately after T9 exit (~40m after T9)',
      deactivationPoint: 'Turn 10 braking zone',
      description:
        'Shorter DRS assist that rewards a committed T9. Sets up late braking into T10, but the corner is tight and easier to defend.',
      effectiveness: 'Medium',
    },
    {
      zone: 2,
      detectionPoint: 'Main straight at Safety Car Line 1',
      activationPoint: 'Main straight (~162m after final corner)',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'Longest DRS run on the lap. A strong launch from the final corner delivers a real braking-window advantage into T1.',
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
        "The track requires downforce, while having low drag is a nice bonus but less crucial. Medium-high downforce configuration prioritizes high-speed corner performance in T3, T9, and the final complex. In 2025, Mercedes appeared to run a Monaco-spec wing (most loaded among top teams) which helped in S2 and S3 where drag matters less; McLaren started with loaded wing, switched to less loaded spec in FP2 for improved top speed (weekend analysis). The 2025 Technical Directive tightened front wing flex limits, potentially impacting teams relying on flexible front wing designs.",
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C2 (Medium)', 'C3 (Soft)'],
      allocation: 'Hardest available compounds (3 steps harder than Monaco/Imola)',
      primaryWearMechanism: 'Front-left tyre is the limiting factor. Clockwise layout means right-hand corners dominate, so the left tyres—especially the front-left—take the beating from sustained lateral loads.',
      explanation:
        "Pirelli brings the hardest compound range (C1-C3) to Barcelona—there was no other option, as the track stresses the tyres tremendously (similar to Suzuka). You cannot perform well without solid cornering performance; top speed, traction, and braking are still important, but not as critical.",
      strategicNote: 'Lifting in T3 during race saves significant tyre life at minimal time cost. 18 of 19 drivers started on Softs in 2025; longest soft stint: 25 laps (Sainz), longest medium stint: 36 laps (Hülkenberg) — 2025 analysis.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium initial grip - significant evolution throughout weekend',
      impact: 'Grip evolution occurs as rubber builds up on the racing line. The asphalt surface offers medium grip that improves over the weekend. Hot Mediterranean conditions (45-55°C track) stress tyres, brakes, and power unit cooling.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Turn 1-2 (Elf chicane) - Primary overtaking zone after 1,047m DRS Zone 2 straight with heavy braking',
    secondaryZones: [
      'Turn 10 (La Caixa) - Heavy braking hairpin with DRS Zone 1 approach',
    ],
    factors: [
      'Long main straight (1,047m) with DRS Zone 2 creates primary passing opportunity',
      'Heavy braking into T1 from ~330 km/h to ~80 km/h enables late-braking moves',
      'T10 La Caixa offers second opportunity with ~300→70 km/h deceleration',
      'Final complex (since 2023) raises following car tyre temps through dirty air',
      'High-speed corners make close following difficult due to aero wake',
      'Track position valuable but two genuine overtaking spots provide opportunities',
    ],
    recommendation:
      'Focus overtaking attempts at Turn 1 after DRS Zone 2 on the main straight—the heavy braking and chicane format offer the best opportunity. Turn 10 provides a secondary option with DRS Zone 1 approach, but the tighter hairpin makes it more difficult to complete the pass. Avoid forcing moves through the high-speed sections where dirty air compromises grip.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot, sunny, stable Mediterranean climate with very low rain probability',
      airTemperature: {
        max: '31°C',
        min: '18°C',
        raceTime: '28-29°C',
      },
      rainProbability: 'Very Low (<5%) - last rain-affected Spanish GP at Catalunya was 1996',
      wind: 'Light breeze, minimal impact on car performance',
      humidity: 'Moderate (40-60%)',
    },
    sessionConditions: {
      fp1: '30°C, sunny',
      fp2: '31°C, sunny',
      fp3: '29°C, sunny',
      qualifying: '30°C, sunny',
      race: '28-29°C, sunny with high-level clouds, 0% rain chance',
    },
    impact:
      "Rain is rare here—the most memorable wet race was the 1996 Spanish GP when Michael Schumacher won in torrential conditions for Ferrari. Hot Mediterranean conditions stress tyres (~45-55°C track temps typical), brakes, and power unit cooling. Thermal management crucial for race success. Cool morning sessions contrast with hot afternoon track conditions.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:15.743',
      driver: 'Oscar Piastri',
      year: 2025,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:11.383',
        driver: 'NOR',
        note: 'All-Time Track Record',
      },
      {
        year: 2025,
        time: '1:11.546',
        driver: 'PIA',
        note: 'Pole margin 0.209s (from weekend dataset)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:11.546' },
        { position: 2, driver: 'NOR', time: '1:11.755' },
        { position: 3, driver: 'VER', time: '1:11.848' },
        { position: 4, driver: 'RUS', time: '1:11.848' },
        { position: 5, driver: 'HAM', time: '1:12.045' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 3',
      sectors: [
        { sector: 1, time: '21.443s', driver: 'PIA' },
        { sector: 2, time: '28.990s', driver: 'PIA' },
        { sector: 3, time: '21.954s', driver: 'PIA' },
      ],
      overallIdealLap: '1:12.387',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '1:19.65s',
        gaps: [
          { driver: 'PIA', gap: '+0.07s' },
          { driver: 'NOR', gap: '+0.13s' },
          { driver: 'LEC', gap: '+0.50s' },
          { driver: 'RUS', gap: '+0.67s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '1:19.63s',
        gaps: [
          { driver: 'NOR', gap: '+0.04s' },
          { driver: 'HAM', gap: '+0.20s' },
          { driver: 'LEC', gap: '+0.24s' },
          { driver: 'RUS', gap: '+0.26s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Nico Hülkenberg', speed: '330 km/h' },
        range: '322-330 km/h',
      },
      race: {
        withDRS: 'Up to 345 km/h (Ocon)',
        withoutDRS: '~316-318 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop: Laps 17-22 (first stop), Laps 40-48 (second stop)',
      factors: [
        'Typically a 2-stop race with soft tyres degrading significantly after ~20 laps',
        'Pit lane time loss ~22-24s (estimate)',
        'Medium stint in middle provides more consistency, though ~0.8s/lap slower initially',
        '3-stop strategy viable but requires exceptional pace to offset additional pit time',
        'Verstappen attempted 3-stop in 2025, compromised by late SC leaving him on Hards',
        '53 pit stops in 2025 race',
        'Undercut effective due to clean air advantage',
      ],
    },
    keyStrategicFactors: [
      'Front-left tyre limiting factor—18 of 19 drivers started on Softs in 2025 (analysis)',
      'Late Safety Car (Antonelli retirement) disrupted strategies in 2025',
      'Lifting in T3 during race saves significant tyre life at minimal time cost',
      'Red Bull used 10 tyre sets total in 2025 (Verstappen 3-stop + SC restart) — analysis',
      'Track position valuable but two genuine overtaking opportunities exist',
    ],
    safetyCarLikelihood: 'Moderate (~35% historical trend estimate)',
    historicalNotes: [
      '2025: Piastri wins, McLaren 1-2. Verstappen P10 after 10s penalty for Russell collision',
      '2025: Hülkenberg P5 from P15—Sauber best result of season',
      '2025: Lance Stroll DNS (withdrew pre-race with wrist/hand pain)',
      '2025: First Aston Martin points of season (Alonso P9)',
      '2023: Layout modification removed final chicane, reverting to MotoGP configuration',
      '2016: Verstappen maiden F1 victory at 18 years old after Hamilton-Rosberg collision',
      '2012: Maldonado scores only F1 victory (and Venezuela\'s only GP win ever)',
      '2006: Alonso becomes first Spanish driver to win home GP',
      '1996: Schumacher wins in torrential rain for Ferrari—legendary drive',
      '1991: Inaugural race—Mansell vs Senna wheel-to-wheel battle down main straight',
      "Final 'Spanish GP' at Catalunya in 2025; circuit hosts 'Barcelona-Catalunya GP' in 2026 before uncertain future",
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'High-Speed Technical',
      icon: 'aero',
      description: 'Fast sweeping corners (T3, T9, T14) and technical sections test car balance.',
    },
    {
      tag: 'Tyre Torture Test',
      icon: 'tyre',
      description: 'Maximum stress (5/5). Hardest compounds (C1-C3). Front-left critical.',
    },
    {
      tag: 'Development Benchmark',
      icon: 'track',
      description: "F1's historic test venue. Layout tests all car aspects.",
    },
    {
      tag: 'Heat Management',
      icon: 'thermometer',
      description: 'Hot conditions (28-31°C air, 45-55°C track) stress tyres, brakes, and PU.',
    },
    {
      tag: 'Downforce Priority',
      icon: 'aero',
      description: 'Medium-high speed corners dominate. Teams run loaded wings.',
    },
    {
      tag: 'Historic Finale',
      icon: 'trophy',
      description: "Final 'Spanish GP' (1991-2025). Hosts 'Barcelona-Catalunya GP' 2026; future uncertain.",
    },
  ],

  fuelEffectPerKg: 0.033,
}
