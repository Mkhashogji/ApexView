import type { TrackIntelligence } from './types'

/**
 * Canadian Grand Prix - Circuit Gilles Villeneuve
 * Round 10 of the 2025 FIA Formula 1 World Championship
 *
 * The Circuit Gilles Villeneuve is a fast, stop-and-go track built on the
 * man-made Île Notre-Dame (created for Expo 67) in the St. Lawrence River.
 * The circuit first hosted F1 in 1978 when hometown hero Gilles Villeneuve
 * won. It features long straights punctuated by heavy braking zones and tight
 * chicanes, with the infamous Wall of Champions awaiting those who push too
 * hard through the final complex.
 */
export const canadaTrackIntelligence: TrackIntelligence = {
  circuitId: 'gilles_villeneuve',
  round: 10,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit Gilles Villeneuve',
    country: 'Canada',
    location: 'Montreal, Quebec',
    grandPrixName: 'Canadian Grand Prix',
    circuitType: 'Semi-Permanent',
    firstGrandPrix: 1978,
    description:
      'The Circuit Gilles Villeneuve is a fast, stop-and-go track built on the man-made Île Notre-Dame (created for Expo 67) in the St. Lawrence River. First hosting F1 in 1978 when hometown hero Gilles Villeneuve won, the circuit features long straights punctuated by heavy braking zones and tight chicanes. The track is essentially a semi-permanent street circuit that remains largely unchanged throughout the year, leading to low grip levels and significant track evolution during the race weekend. Named after Canadian racing legend Gilles Villeneuve following his tragic death at Spa in 1982, the circuit has become one of the most beloved venues on the F1 calendar.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.361,
      miles: 2.710,
    },
    raceDistance: {
      km: 305.270,
      miles: 189.686,
    },
    numberOfLaps: 70,
    numberOfCorners: 14,
    drsZones: 3, // FIA 2025 Event Notes: 3 activation points, 2 detection points
    lapRecord: {
      time: '1:13.078',
      driver: 'Valtteri Bottas',
      year: 2019,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-2.00°',
      },
      minStartingPressures: {
        front: '23.5 psi',
        rear: '20.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,        // High - critical for chicane exits onto straights
    tyreStress: 3,      // Moderate
    asphaltGrip: 2,     // Low - semi-permanent surface with limited rubber
    asphaltAbrasion: 1, // Very low
    braking: 5,         // MAXIMUM - heavy braking zones throughout
    lateral: 1,         // Low - few high-speed corners
    downforce: 1,       // Low - long straights demand drag reduction
    trackEvolution: 5,  // MAXIMUM - significant grip improvement over weekend
  },

  energyProfile: {
    longitudinal: 'High',    // Strong acceleration/deceleration cycles
    lateral: 'Low',          // Few sustained cornering loads
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T5',
      description:
        'The slowest and most compact sector with 5 corners in a short distance and no straights. The Senna "S" chicane (T1-T2) opens the lap and sets the rhythm. Requires precision and downforce — easy to make mistakes here that compromise the entire lap.',
      keyFeatures: [
        'Virage Senna (T1-T2): Iconic "S" chicane named after Ayrton Senna',
        'T3: Tight right-hander requiring patience',
        'T4-T5: Technical complex demanding precision',
        'No straights in sector — pure cornering focus',
        'Overall cornering capability most important here',
      ],
      criticalCorners: [
        'T1-T2 (Virage Senna) - Sets up entire sector, kerb usage critical',
        'T4-T5 - Technical chicane, exit onto short straight to S2',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T6-T9',
      description:
        'Medium speed sector with flowing rhythm featuring two chicanes, each followed by a straight. DRS Zone 1 activates after T7, rewarding a clean chicane exit. The Pont de la Concorde (T8) is a fast kink before T9, adding visual drama with the bridge underpass.',
      keyFeatures: [
        'T6-T7: First chicane of sector, followed by DRS Zone 1 activation',
        'DRS Zone 1: Activates after T7, leads into T8 braking zone',
        'Pont de la Concorde (T8): Fast kink after bridge underpass',
        'T9: Sets up approach to the famous hairpin',
        'Mix of acceleration zones and chicane negotiation',
      ],
      criticalCorners: [
        'T6-T7 - Chicane precision key, clean exit enables DRS Zone 1',
        'T8 (Pont de la Concorde) - Quick direction change, visually dramatic',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow/Gold
      corners: 'T10-T14',
      description:
        'The fastest and most decisive sector, built around exit speed and straight-line efficiency. L\'Épingle (T10) is one of the calendar\'s tightest hairpins (~60 km/h, near full lock), and DRS Zones 2 & 3 reward anyone who launches cleanly from slow corners. The final chicane fires you onto the line with the Wall of Champions waiting for the overcommitted.',
      keyFeatures: [
        'L\'Épingle (T10): 180° hairpin with near full lock — prime overtaking spot',
        'DRS Zones 2 & 3: Two late-lap DRS runs that amplify exit quality and slipstream',
        'Casino Straight: Long acceleration phase where closing speed builds quickly',
        'T13-14 (Final Chicane): Precision under braking, then commit on exit',
        'Wall of Champions: Exit wall that punishes small mistakes at speed',
        'Where most overtakes and most drama happens',
      ],
      criticalCorners: [
        'T10 (L\'Épingle) - ~60 km/h hairpin, exit crucial for the long acceleration phase',
        'T13-14 (Final Chicane) - Wall of Champions awaits the overambitious',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Just after T5 (~15m beyond exit)',
      activationPoint: 'After T6-T7 chicane (~95m beyond T7)',
      deactivationPoint: 'Heavy braking for T8',
      description:
        'A short acceleration zone after the first chicane. Rewards a clean T6-T7 exit and sets up a late-brake attempt into the next change of direction.',
      effectiveness: 'Medium',
    },
    {
      zone: 2,
      detectionPoint: 'Out of T9 (~110m beyond corner)',
      activationPoint: 'On run toward T12 (~155m before T12)',
      deactivationPoint: 'Braking for final chicane (T13-T14)',
      description:
        'The main passing tool on the long drag section. Strong traction from the hairpin phase and low-drag trim let cars build decisive closing speed.',
      effectiveness: 'Very High',
    },
    {
      zone: 3,
      detectionPoint: 'Out of T9 (~110m beyond corner) — shared with Zone 2',
      activationPoint: 'After final chicane (~70m after T14)',
      deactivationPoint: 'Braking for T1',
      description:
        'A follow-up DRS opportunity that punishes a messy last chicane. Can convert a good final exit into a Turn 1 look, especially with a tow.',
      effectiveness: 'Medium',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium-Low',
      explanation:
        'The Circuit Gilles Villeneuve demands a low-drag setup to maximize performance on the long Casino Straight and back straight, while retaining enough downforce for heavy braking stability and traction out of slow corners. Pirelli rates downforce demand at 1/5, but practically teams run closer to 2/5 — the braking demands (5/5) necessitate stability, and high traction requirements (4/5) out of slow corners support additional rear wing. In 2025, Mercedes appeared to carry relatively more drag than the lowest-drag cars (based on top-speed data), yet were strong over the lap — suggesting a stability/traction trade-off that paid off with pole and victory (analysis).',
    },
    tyreManagement: {
      compounds: ['C4 (Hard)', 'C5 (Medium)', 'C6 (Soft)'],
      allocation: 'Softest available compounds',
      primaryWearMechanism: 'Longitudinal stress from heavy braking and acceleration cycles. Low lateral energy means compounds survive cornering but front tyres suffer under repeated hard braking.',
      explanation:
        'The semi-permanent surface provides low initial grip (2/5 asphalt grip) but significant track evolution (5/5) as rubber is laid down. Cool Canadian temperatures favor softer compounds and extend tyre life. Hard compound proved most effective in 2025 race, with Medium faster initially but degrading more quickly.',
      strategicNote: 'Two-stop commonly competitive: Medium → Hard → Hard. Albon completed 23 laps on Mediums; Ocon and Sainz ran 57 laps on single Hard set (2025 analysis).',
    },
    surfaceCharacteristics: {
      gripLevel: 'Low initial grip - significant evolution throughout weekend',
      impact: 'Semi-permanent street circuit surface remains largely unchanged year-round, leading to dusty, low-grip conditions early in weekend. Track evolution critical — times drop significantly from FP1 to race.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Low',
    primaryZone: 'Turn 10 (L\'Épingle hairpin) - multiple line options for attack and defense',
    secondaryZones: ['Casino Straight into T13', 'Start/Finish into T1 via DRS Zone 3', 'T6-T7 chicane via DRS Zone 1'],
    factors: [
      'L\'Épingle hairpin allows multiple racing lines — inside, outside, or late apex',
      'Casino Straight with DRS Zone 2 provides prime slipstream opportunity',
      'Heavy braking zones create late-braking opportunities at T1, T6, T10, T13',
      'Final chicane sees frequent defending and cutting of T13 into run-off',
      'DRS trains can form after pit stops, temporarily reducing overtaking effectiveness',
      'Low lateral energy means following cars suffer less from dirty air than high-downforce circuits',
    ],
    recommendation:
      'The hairpin (T10) offers the best overtaking opportunity with multiple viable lines. Casino Straight with DRS allows closing the gap before T13 dive. Sector 1 is difficult for overtaking due to tight chicane sequence. Track position less critical than at high-downforce circuits.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Continental/humid climate with changeable weather. Rain common at Montreal, adding strategic unpredictability. Cool mornings give way to warm afternoons.',
      airTemperature: {
        max: '25°C',
        min: '18°C',
        raceTime: '22°C',
      },
      rainProbability: 'Moderate-High - Atlantic weather systems create unpredictability',
      wind: 'Light to moderate, variable direction',
      humidity: 'Moderate to High',
    },
    sessionConditions: {
      fp1: '18-20°C, variable clouds, low rain risk',
      fp2: '22-24°C, partly cloudy, dry',
      fp3: '20-22°C, morning clouds clearing',
      qualifying: '23-25°C, partly cloudy, low rain chance',
      race: '22-25°C, variable conditions, moderate rain probability',
    },
    impact:
      'Canadian weather is notoriously unpredictable. The 2011 race saw heavy rain causing multiple stoppages, resulting in the longest F1 race ever at 4 hours 4 minutes. Rain can completely alter strategy and race outcome. Cool temperatures favor softer compounds and extend tyre life. Track evolution significant as rubber is laid down on low-grip surface.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:13.078',
      driver: 'Valtteri Bottas',
      year: 2019,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:12.000',
        driver: 'RUS',
        note: 'Russell pole before rain-affected race',
      },
      {
        year: 2025,
        time: '1:10.899',
        driver: 'RUS',
        note: 'Pole on Medium compound (C5)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'RUS', time: '1:10.899' },
        { position: 2, driver: 'VER', time: '1:11.059' },
        { position: 3, driver: 'PIA', time: '1:11.120' },
        { position: 4, driver: 'ANT', time: '1:11.391' },
        { position: 5, driver: 'HAM', time: '1:11.526' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '20.085s', driver: 'NOR' },
        { sector: 2, time: '22.808s', driver: 'ALB' },
        { sector: 3, time: '29.120s', driver: 'RUS' },
      ],
      overallIdealLap: '1:12.013',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'RUS',
        meanLapTime: '1:15.54',
        gaps: [
          { driver: 'VER', gap: '+0.02s' },
          { driver: 'ANT', gap: '+0.05s' },
          { driver: 'NOR', gap: '+0.06s' },
          { driver: 'PIA', gap: '+0.08s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '1:25.28',
        gaps: [
          { driver: 'VER', gap: '+0.03s' },
          { driver: 'PIA', gap: '+0.21s' },
          { driver: 'RUS', gap: '+0.25s' },
          { driver: 'HAM', gap: '+0.34s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Lance Stroll', speed: '337 km/h' },
        range: '330-337 km/h',
      },
      race: {
        withDRS: 'Up to 345 km/h',
        withoutDRS: '~317 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop commonly competitive: Medium → Hard → Hard (stops around lap 12-16 and lap 37-45)',
      factors: [
        'Pit lane time loss ~18.4s (per F1 2025 track facts, including 2.5s stop)',
        'Hard compound most effective for race pace in 2025 (analysis)',
        'Medium faster initially but degrades more quickly',
        'One-stop viable from back of grid but risky in warm conditions',
        'Albon completed 23 laps on Mediums; Ocon/Sainz ran 57 laps on single Hard (2025 analysis)',
        'Track position crucial due to Sector 1 difficulty for overtaking',
        'Undercut powerful due to clean air advantage',
      ],
    },
    keyStrategicFactors: [
      'Safety Car probability 83% (F1 official 2025 stat)',
      'Virtual Safety Car probability 50% (F1 official 2025 stat)',
      'DRS trains can form after pit stops, making overtaking difficult temporarily',
      'High track evolution means early starters on low grip may struggle',
      '2025: Russell won; Antonelli claimed first F1 podium; McLaren teammates Norris and Piastri collided in closing stages',
    ],
    safetyCarLikelihood: 'Very High (83% probability per F1 official 2025 stats)',
    historicalNotes: [
      '2025: Russell wins for Mercedes; Antonelli\'s first F1 podium',
      '2025: Norris and Piastri collision in closing stages',
      '2024: Wet/dry conditions created chaotic race with multiple strategy variations',
      '2019: Vettel crossed line first but 5-second penalty handed victory to Hamilton',
      '2014: Ricciardo\'s first F1 win, capitalizing on Mercedes reliability issues',
      '2011: Longest F1 race ever (4h 4m 39s) due to rain; Button won from last to first',
      '1999: Wall of Champions created — Hill, Schumacher, Villeneuve all crashed at T14 exit',
      '1978: Circuit\'s inaugural F1 race won by hometown hero Gilles Villeneuve',
      'Circuit renamed after Gilles Villeneuve following his death at Spa in 1982',
    ],
  },

  // =========================================================================
  // Defining Characteristics - CONDENSED for proper tooltip display
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Stop-and-Go',
      icon: 'zap',
      description:
        'Heavy braking chicanes followed by full acceleration zones define the lap rhythm.',
    },
    {
      tag: 'Low Downforce',
      icon: 'wind',
      description:
        'Long straights demand drag reduction; minimal wing load for overtaking potential.',
    },
    {
      tag: 'Overtaking Friendly',
      icon: 'arrowLeftRight',
      description:
        'Three DRS zones and the hairpin create multiple passing chances each lap.',
    },
    {
      tag: 'Wall of Champions',
      icon: 'alertTriangle',
      description:
        'Infamous final chicane exit has ended races for many World Champions since 1999.',
    },
    {
      tag: 'Strategy Critical',
      icon: 'target',
      description:
        'Multiple viable strategy options combined with 83% Safety Car probability.',
    },
    {
      tag: 'Weather Variable',
      icon: 'cloudRain',
      description:
        'Changeable Canadian weather can disrupt any race plan; rain always possible.',
    },
  ],

  fuelEffectPerKg: 0.034,
}
