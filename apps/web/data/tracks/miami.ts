import type { TrackIntelligence } from './types'

/**
 * Miami Grand Prix - Miami International Autodrome
 * Round 6 of the 2025 FIA Formula 1 World Championship
 *
 * The Miami International Autodrome represents the modern era of American Formula 1
 * expansion, joining the calendar in 2022 and extended through 2041—bringing F1 back
 * to Florida for the first time since the short-lived Sebring GP in 1959.
 *
 * This purpose-built temporary circuit wraps around the Hard Rock Stadium complex in
 * Miami Gardens, home to the NFL's Miami Dolphins. Despite being a temporary circuit,
 * the track was designed to have a permanent feel, with the 5.412 km layout featuring
 * 19 corners, three DRS zones, and top speeds exceeding 340 km/h. The design balances
 * high-speed straights with technical slow-speed sections, creating numerous overtaking
 * opportunities rare for a street-style circuit.
 *
 * The 2025 edition saw McLaren demonstrate dominant pace, with Oscar Piastri claiming
 * his third consecutive victory following wins in Bahrain and Saudi Arabia—the first
 * McLaren driver to achieve this feat since Mika Häkkinen in 1997. Max Verstappen set
 * a new track record in qualifying with a 1:26.204 lap.
 */
export const miamiTrackIntelligence: TrackIntelligence = {
  circuitId: 'miami',
  round: 6,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Miami International Autodrome',
    country: 'United States',
    location: 'Miami Gardens, Florida',
    grandPrixName: 'Miami Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 2022,
    description:
      "The Miami International Autodrome is a purpose-built temporary circuit situated within the Hard Rock Stadium complex in Miami Gardens, Florida—home to the NFL's Miami Dolphins. Designed to have a permanent feel despite being assembled and dismantled annually, the track features 19 corners, three DRS zones, and two long straights that create one of the fastest city circuits on the calendar. The circuit's unique theming includes a 'fake marina' section complete with decorative yachts and blue-painted asphalt at T7-T8, embodying Miami's glamorous waterfront culture. Miami joined the calendar in 2022 and was extended through 2041, making it one of three US races alongside Austin (COTA) and Las Vegas. The track requires a well-balanced car setup: a 3/5 score given to traction, braking, and lateral performance means no single car strength dominates. The medium downforce configuration (3/5) confirms this is a true all-rounder's circuit.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.412,
      miles: 3.363,
    },
    raceDistance: {
      km: 308.326,
      miles: 191.561,
    },
    numberOfLaps: 57,
    numberOfCorners: 19,
    drsZones: 3,
    lapRecord: {
      time: '1:29.708',
      driver: 'Max Verstappen',
      year: 2023,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '24.5 psi',
        rear: '21.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,          // Medium - balanced traction demands from slow chicanes and hairpin
    asphaltGrip: 4,       // High - purpose-built asphalt provides excellent mechanical grip
    asphaltAbrasion: 2,   // Low - smooth surface causes minimal tyre degradation
    trackEvolution: 5,    // Maximum - temporary circuit assembled weeks before race; dramatic grip improvement
    tyreStress: 3,        // Medium - one-step softer compounds (C3-C5) but low-wear city circuit nature
    braking: 3,           // Medium - heavy zones at T11/T17 but well-distributed overall
    lateral: 3,           // Medium - T4-T8 sweepers create sustained loads but no extreme corners
    downforce: 3,         // Medium - balanced aero configuration for straights vs corners
  },

  energyProfile: {
    longitudinal: 'Medium',   // Two long straights with heavy braking zones
    lateral: 'Medium',        // Sector 1 sweepers demand sustained lateral grip
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T8',
      description:
        "The tyre-killing sector featuring consecutive high-speed sweepers through T4-T8, culminating in the signature T7-T8 complex—a 150° decreasing-radius left past the 'marina' theming with fake yachts and blue asphalt. This sector ends approximately 110m after T8. Heavy front tyre wear occurs due to sustained understeer at high speed through the sweeper sequence.",
      keyFeatures: [
        'T1: Medium-speed right from start/finish straight, common Lap 1 overtaking spot',
        'T2-T3: Gentle link corners maintaining flow',
        'T4-T6: Consecutive 60° sweepers (left-right-left) building lateral load',
        'T7-T8 (Marina Complex): Signature corner—150° decreasing radius left past fake marina',
        'Sector 1 ends 110m after T8, before DRS Detection Zone 1',
        'Front tyre management critical through high-speed understeer zones',
      ],
      criticalCorners: [
        'T1 - Heavy braking from start/finish straight; primary Lap 1 action zone',
        'T7-T8 (Marina Complex) - Decreasing radius 150° left; key sector time corner; tyre killer',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T9-T16',
      description:
        "Features the 1.4km back straight (longest on circuit) ending at T11—a tight 120° left that is the primary overtaking spot. The sector then navigates the narrowest sections including 'The Beach' spectator area at T12 and the T14-T15 chicane complex. Sector ends approximately 70m after T16. Moderate rear tyre wear from multiple traction zones through the technical sections.",
      keyFeatures: [
        'T9-T10: Gentle kinks on 1.4km back straight (DRS Zone 1 active)',
        'T11: Tight 120° left—premier passing spot; heavy braking from 320+ km/h',
        'T12 (The Beach): Sweeping 160° right past premium spectator area',
        'T13: Tight left linking to chicane',
        'T14-T15: Right-left chicane requiring precise car placement',
        'T16: Medium-speed right; exit speed crucial for DRS Zone 2',
        'Sector 2 ends 70m after T16, before main straight',
      ],
      criticalCorners: [
        'T11 - Primary overtaking opportunity; 120° left from 320+ km/h; DRS-assisted moves',
        'T14-T15 (Chicane) - Technical complex; exit determines T17 approach speed',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T17-T19',
      description:
        "The main overtaking zone featuring the longest straight leading to T17 hairpin—minimum speed approximately 65 km/h. This is where the 2025 season-record 355 km/h was achieved by Alonso in a DRS train. T18-T19 complete the lap, with T19 exit speed setting up the following lap's potential. Minimal tyre wear in this short sector; pure straight-line and braking performance.",
      keyFeatures: [
        'Main straight: DRS Zones 2 and 3 active; 355 km/h potential with slipstream',
        'T17 (Hairpin): Slow 180° right, minimum ~65 km/h—main overtaking spot',
        'T18: Gentle left link corner',
        'T19: Medium-speed right onto start/finish; exit speed critical',
        'Speed trap location before T17 braking zone',
        'Sector 3 ends at start/finish line',
      ],
      criticalCorners: [
        'T17 (Hairpin) - Main overtaking zone; very heavy braking from 350+ km/h to 65 km/h',
        'T19 - Final corner; exit speed determines T1 attack/defense capability',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '90m after T8',
      activationPoint: '30m after T9 (back straight)',
      deactivationPoint: 'T11 braking zone',
      description:
        "The longest DRS stretch on the 1.4km back straight, building speed before the heavy stop at T11. If you're within a second through the marina complex, you can deploy on the run toward the tightest left on the lap.",
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: '70m after T16',
      activationPoint: '525m after T16 (main straight)',
      deactivationPoint: 'T17 braking zone',
      description:
        "Sets up the T17 hairpin approach—heavy braking from 340+ km/h into the slowest corner on the circuit. Combined with Zone 3, creates a double-DRS opportunity if you stay close through the technical section.",
      effectiveness: 'High',
    },
    {
      zone: 3,
      detectionPoint: '15m after T17',
      activationPoint: 'On T19 apex (immediately after rotation onto the line)',
      deactivationPoint: 'T1 braking zone',
      description:
        "Short zone that rewards a strong hairpin exit. If you launch well from T17, you can deploy as you rotate through T19 and arrive at T1 with a look down the inside—useful for setting up next-lap attacks.",
      effectiveness: 'Medium',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium',
      explanation:
        "Miami requires a balanced aerodynamic setup—teams must balance cornering performance in Sector 1's sweepers against straight-line speed for the two long straights. Based on visible rear-wing configurations from the 2025 weekend, McLaren and Mercedes appeared to run reduced wing loads versus 2024, which may suggest strong year-on-year downforce development allowing them to trim drag while maintaining corner speed. Red Bull ran a more loaded wing among frontrunners with increased lower-plane camber, which may suggest a different aero development trade-off prioritizing mechanical grip. Aston Martin ran high wing loads, sacrificing straight-line speed. The 3/5 downforce rating confirms this is a circuit where neither extreme works—true compromise is required.",
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'One step softer than 2024 (same approach as Saudi Arabia)',
      primaryWearMechanism: 'Front tyre degradation through Sector 1 sweepers (T4-T8). High-speed understeer creates sustained front loading. Rear tyres stressed by traction demands from T11 and T17 exits.',
      explanation:
        "Pirelli brought one-step softer compounds to Miami 2025 compared to 2024, the same approach used in Saudi Arabia. Despite the softer selection, tyre wear remained low due to the exceptional durability of Pirelli compounds and the inherent low-wear nature of city circuits with smooth, purpose-built asphalt. Soft saw limited race use; most strategies still leaned to Medium→Hard around the one-stop window.",
      strategicNote: 'One-stop dominant. Medium-Hard (M-H) preferred strategy. Soft compound reserved for qualifying. VSC on L29 created free pit window that Russell exploited to jump Verstappen.',
    },
    surfaceCharacteristics: {
      gripLevel: 'High (4/5) - Purpose-built asphalt provides excellent mechanical grip especially after rubber accumulates',
      impact: 'The circuit is assembled 2-3 weeks before the race weekend and dismantled afterward. Track evolution is rated maximum (5/5)—grip levels improve dramatically from FP1 through qualifying as rubber builds on the initially clean surface. The smooth asphalt causes minimal abrasion (2/5), allowing extended stint lengths. Some bumps exist from integrating with existing road infrastructure, particularly through the T12-T15 technical section.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'T17 (Hairpin) - Very heavy braking from 350+ km/h with DRS advantage from Zones 2 and 3',
    secondaryZones: [
      'T11 (120° Left) - Heavy braking from 320+ km/h at end of 1.4km back straight with DRS Zone 1',
      'T1 - Medium braking from start/finish with DRS Zone 3 advantage; more effective at race start',
    ],
    factors: [
      'Three DRS zones create multiple passing opportunities per lap—rare for street circuit',
      'T11 and T17 heavy braking zones ideal for late-braking moves',
      'DRS trains can reach extreme speeds (355 km/h achieved by Alonso in 2025)',
      'Slipstream effect powerful on both long straights',
      'Dirty air in Sector 1 sweepers can hurt following car pace',
      'Track position still valuable but not paramount—recovery drives possible',
      'Fresh tyres create significant delta for overtaking attempts',
      'T1 Lap 1 action common—Verstappen defended inside forcing Norris wide in 2025',
    ],
    recommendation:
      "Focus overtaking attempts at T17 hairpin using DRS from the main straight—the combination of very heavy braking from 350+ km/h and slow apex speed creates the largest overtaking window. T11 at the end of the back straight offers a secondary high-percentage opportunity with DRS Zone 1 assistance. Unlike traditional street circuits, Miami's three DRS zones make recovery drives feasible. The 2025 race demonstrated this: Norris dropped from P2 to P6 at T1 but recovered to P2 by Lap 18. Strategic pit stop timing via undercut/overcut remains effective but on-track passing is genuinely possible.",
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Subtropical climate with high humidity and afternoon thunderstorm risk (Köppen: Am)',
      airTemperature: {
        max: '30°C',
        min: '24°C',
        raceTime: '28-30°C',
      },
      rainProbability: 'Medium (30-40%) - Florida afternoon thunderstorms possible',
      wind: 'Light easterly breeze, typically 10-20 km/h',
      humidity: 'High (70-85%)',
    },
    sessionConditions: {
      fp1: '~27°C air / ~45°C track (approx), partly cloudy',
      fp2: '~28°C air / ~48°C track (approx), sunny',
      fp3: '~27°C air / ~44°C track (approx), partly cloudy',
      qualifying: '~29°C air / ~50°C track (approx), sunny',
      race: '~29°C air / ~52°C track (approx), partly cloudy; forecasted rain did not materialize',
    },
    impact:
      "Miami's subtropical climate creates challenging conditions with high humidity affecting power unit cooling and tyre warm-up. The 2025 Sprint was dramatically affected by torrential pre-race rain, with Leclerc crashing on the formation lap (aquaplaning at T10) and the race shortened from 19 to 18 laps. However, the main race enjoyed dry conditions throughout. Florida's characteristic afternoon thunderstorms pose strategic risk but are unpredictable. Hot track temperatures (50°C+) can accelerate degradation on the C5 soft compound.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:29.708',
      driver: 'Max Verstappen',
      year: 2023,
    },
    polePositions: [
      {
        year: 2022,
        time: '1:28.796',
        driver: 'LEC',
        note: 'Inaugural Miami GP; Leclerc pole but Verstappen won race',
      },
      {
        year: 2023,
        time: '1:26.841',
        driver: 'PER',
        note: 'Pérez pole but Verstappen won from P9 after Q3 Red Flag',
      },
      {
        year: 2024,
        time: '1:27.241',
        driver: 'VER',
        note: 'Verstappen pole; Norris maiden win aided by Safety Car strategy',
      },
      {
        year: 2025,
        time: '1:26.204',
        driver: 'VER',
        note: 'NEW TRACK RECORD; Verstappen pole by 0.065s over Norris',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:26.204' },
        { position: 2, driver: 'NOR', time: '1:26.269' },
        { position: 3, driver: 'ANT', time: '1:26.271' },
        { position: 4, driver: 'PIA', time: '1:26.375' },
        { position: 5, driver: 'RUS', time: '1:26.385' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Sprint Qualifying',
      sectors: [
        { sector: 1, time: '28.577s', driver: 'VER' },
        { sector: 2, time: '32.936s', driver: 'PIA' },
        { sector: 3, time: '24.832s', driver: 'NOR' },
      ],
      overallIdealLap: '1:26.345',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'PIA',
        meanLapTime: '91.11s',
        gaps: [
          { driver: 'NOR', gap: '+0.09s' },
          { driver: 'VER', gap: '+0.64s' },
          { driver: 'RUS', gap: '+0.68s' },
          { driver: 'ALB', gap: '+0.71s' },
          { driver: 'LEC', gap: '+0.88s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '92.13s',
        gaps: [
          { driver: 'VER', gap: '+0.11s' },
          { driver: 'LEC', gap: '+0.19s' },
          { driver: 'SAI', gap: '+0.19s' },
          { driver: 'PER', gap: '+0.29s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'LEC', speed: '343.5 km/h' },
        range: '~320-344 km/h',
      },
      race: {
        withDRS: 'Up to ~355 km/h with DRS/slipstream (reported, situational)',
        withoutDRS: 'Low-330s km/h typical in clean air, depending on wing level',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop: Laps 25-29 (Medium to Hard)',
      factors: [
        'One-stop strategy dominant in 2025 with Medium-Hard the preferred approach',
        'Pit lane time loss: ~22 seconds (McLaren fastest crew at 22.05s average)',
        'Soft compound unused in race—too short-lived for race stints',
        'VSC on Lap 29 created free pit window; Piastri/Norris/Russell/Leclerc exploited it',
        'Russell jumped Verstappen via VSC pit timing—gained podium position',
        'Hard-Medium (H-M) alternative used by 6 drivers including Russell and Hamilton',
        'No driver exceeded 29 laps on Mediums due to VSC opportunity',
        'Undercut/overcut both viable given three DRS zones for recovery',
      ],
    },
    keyStrategicFactors: [
      'McLaren 1-2 finish dominated by 37+ seconds over P3 Russell',
      'Piastri third consecutive win (Bahrain, Saudi Arabia, Miami)—first McLaren driver since Häkkinen (1997/98)',
      'Norris dropped from P2 to P6 after T1 incident with Verstappen',
      'Norris recovered P6→P2 by Lap 18 demonstrating overtaking viability',
      'Antonelli youngest sprint pole sitter in F1 history (1:26.482)',
      'Hamilton shock Q2 exit (P12)—finished P8 after team orders controversy with Leclerc',
      'Williams both cars in points (Albon P5, Sainz P9)—excellent result',
      'Alonso 36-lap Hard stint—longest of the race',
    ],
    safetyCarLikelihood: 'Medium (~35-45% probability - street circuit nature but wide run-off in most areas)',
    historicalNotes: [
      '2025: Piastri wins McLaren 1-2; Verstappen new qualifying record 1:26.204',
      '2024: Norris maiden victory; McLaren upgrade debut transformed competitiveness',
      '2023: Verstappen wins from P9; Perez on pole',
      '2022: Verstappen wins inaugural Miami GP; Leclerc on pole',
      'Contract extended through 2041 (originally 2022-2031)',
      'One of three US races alongside Austin (COTA) and Las Vegas',
      'Hard Rock Stadium home to NFL Miami Dolphins',
      'Sprint format venue since 2024',
      'Track assembled/dismantled annually around stadium complex',
    ],
  },
  
  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Modern American Glamour',
      icon: 'flag',
      description: "Purpose-built around Hard Rock Stadium. Fake marina at T7-T8. 'The Beach' at T12.",
    },
    {
      tag: 'Three DRS Zones',
      icon: 'overtake',
      description: 'Genuine overtaking at T11, T17, and T1. Recovery drives possible—rare for street circuit.',
    },
    {
      tag: 'True All-Rounder',
      icon: 'balance',
      description: '3/5 Pirelli ratings across traction, braking, lateral, and downforce. Overall package rewarded.',
    },
    {
      tag: 'Maximum Track Evolution',
      icon: 'evolution',
      description: '5/5 evolution. Temporary surface sees dramatic grip improvement FP1→Qualifying.',
    },
    {
      tag: 'Speed Record Venue',
      icon: 'speed',
      description: "355 km/h by Alonso in 2025—season's highest. Main straight enables extreme velocities.",
    },
    {
      tag: 'Sprint Weekend Venue',
      icon: 'clock',
      description: 'Hosts Sprint format. 2025 Sprint rain-affected; Norris won shortened race.',
    },
  ],
}

