import type { TrackIntelligence } from './types'

/**
 * Bahrain Grand Prix - Bahrain International Circuit
 * Round 4 of the 2025 FIA Formula 1 World Championship
 *
 * The Bahrain International Circuit made history in 2004 as Formula 1's first
 * venture into the Middle East, establishing a blueprint for the sport's expansion
 * into new markets. Designed by Hermann Tilke, this purpose-built facility in the
 * Sakhir desert combines a challenging technical layout with world-class facilities.
 * The circuit's 5.412 km layout features 15 corners and three DRS zones, creating
 * excellent overtaking opportunities despite the technical middle sector.
 *
 * Bahrain's defining characteristic is its extreme surface abrasion—rated 5/5 by
 * Pirelli (maximum on their scale). The graywacke aggregate rapidly wears tyres,
 * necessitating the hardest compound selection (C1-C3) and careful rear tyre
 * management throughout race distance. Desert conditions bring additional challenges:
 * sand contamination reduces early-weekend grip, while the twilight race format sees
 * temperatures drop 5-6°C as the sun sets and floodlights illuminate the spectacular
 * desert venue.
 *
 * The 2025 edition marked a historic milestone as Oscar Piastri delivered McLaren's
 * first-ever Bahrain victory, leading every lap except during pit stops to win by
 * over 15 seconds. The race maintained Bahrain's reputation for drama with a Safety
 * Car deployment on Lap 32 following Carlos Sainz's incident, and a post-race
 * disqualification of Nico Hulkenberg for excessive plank wear. Remarkably, Pedro
 * de la Rosa's 2005 race lap record of 1:31.447 still stands—now the second-longest
 * standing lap record in Formula 1 history.
 */
export const bahrainTrackIntelligence: TrackIntelligence = {
  circuitId: 'bahrain',
  round: 4,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Bahrain International Circuit',
    country: 'Bahrain',
    location: 'Sakhir, Bahrain',
    grandPrixName: 'Bahrain Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 2004,
    description:
      "The Bahrain International Circuit holds a pioneering place in Formula 1 history as the sport's first Middle Eastern venue. Located in the Sakhir desert, this Hermann Tilke-designed permanent circuit debuted in 2004 and quickly established itself as a challenging technical test with its diverse corner profiles. The 5.412 km layout features 15 corners ranging from the ultra-slow T1-T3 chicane (~60 km/h) to flowing high-speed sections, creating a comprehensive examination of car performance. Three DRS zones enable overtaking, with the main straight's heavy braking zone into T1 serving as the primary passing point. Bahrain's extreme surface abrasion (5/5 Pirelli rating—highest on calendar) demands the hardest tyre allocation and careful rear degradation management. Despite extreme abrasion, overall tyre stress remains average (3/5) because the track lacks long sequences of fast corners like Suzuka. The twilight race format creates a stunning visual spectacle as cars transition from daylight to floodlit conditions, while the 5-6°C temperature drop significantly affects tyre behavior. Bahrain has been a frequent modern pre-season test venue, hosting annually since 2021 including the sole 2025 test, making it one of the best-understood circuits on the calendar.",
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
      km: 308.238,
      miles: 191.530,
    },
    numberOfLaps: 57,
    numberOfCorners: 15,
    drsZones: 3,
    lapRecord: {
      time: '1:31.447',
      driver: 'Pedro de la Rosa',
      year: 2005,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-2.00°',
      },
      minStartingPressures: {
        front: '23.0 psi',
        rear: '21.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED & CORRECTED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,          // High - critical for T1, T4, T10 exits; multiple heavy braking zones
    asphaltGrip: 3,       // Medium - desert surface with sand contamination; grip evolves
    asphaltAbrasion: 5,   // EXTREME - maximum Pirelli rating; graywacke aggregate rapidly wears tyres
    trackEvolution: 4,    // High - significant improvement as weekend progresses
    tyreStress: 3,        // Medium - despite high abrasion, lacks sustained fast corners like Suzuka
    braking: 4,           // High - heavy braking into T1, T4, T10; stability critical
    lateral: 3,           // Medium - few sustained lateral-load corners
    downforce: 3,         // Medium - balance between straights and S2 corner performance
  },

  energyProfile: {
    longitudinal: 'High',     // Acceleration/braking dominant; multiple heavy braking zones
    lateral: 'Medium',        // Moderate sustained lateral loads through technical sections
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T4',
      description:
        "The high-speed zone featuring two DRS-assisted straights connected by the slowest chicane on the circuit. The main straight approach exceeds 300 km/h before heavy braking into T1—the primary overtaking zone. The T1-T2-T3 chicane drops speed to approximately 60 km/h (the slowest point on circuit) before accelerating through the second DRS zone toward T4. Mercedes and Ferrari showed strong S1 pace in 2025 practice, highlighting the importance of top speed through this sector. This sector tests braking stability, traction on exit, and low-drag efficiency.",
      keyFeatures: [
        'Main straight approach at 300+ km/h with DRS Zone 3',
        'T1 slowest corner on circuit (~60 km/h from 300+ km/h)',
        'T1-T2-T3 chicane—tightest sequence on track',
        'T3-T4 DRS Zone 1 straight enables compound overtaking',
        'Primary overtaking zone—use main straight to close, T4 straight to attack',
        'Mercedes and Ferrari showed strong S1 pace in 2025 practice sessions',
        'Braking stability and traction on exit are paramount',
      ],
      criticalCorners: [
        'T1 - Heavy braking from 300+ km/h to ~60 km/h; primary overtaking spot; braking stability critical',
        'T4 - Second heavy braking zone; continuation battles from T1 often conclude here',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T5-T12',
      description:
        "The technical zone featuring multiple low/medium speed corners where mechanical grip dominates. The T9-T10 downhill complex represents the most challenging sequence on the circuit, with T10 exit speed determining DRS Zone 2 effectiveness into T11. DRS Zone 2 activates after T10, enabling attacks into the T11 hairpin. Dirty air severely hampers following cars through this section, making overtaking virtually impossible except at T11. High-downforce setups showed advantages through this sector in 2025, demonstrating that corner speed can outweigh straight-line speed penalties.",
      keyFeatures: [
        'Longest sector with multiple low/medium speed corners',
        'T9-T10 downhill complex is most challenging sequence',
        'DRS Zone 2 activates after T10 for T11 hairpin attacks',
        'Dirty air severely hampers following cars through technical corners',
        'High-downforce setups showed advantages in 2025',
        'T10 exit speed critical for DRS Zone 2 effectiveness',
        'T11 hairpin provides overtaking opportunity within sector',
      ],
      criticalCorners: [
        'T9-T10 Complex - Most demanding sequence; downhill double-apex left into hairpin right',
        'T8 - Fast right-hander leading into T9-T10; requires commitment for proper positioning',
        'T11 - Tight hairpin following DRS Zone 2; primary overtaking opportunity in this sector',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T13-T15',
      description:
        "The final sector featuring the T13-T14-T15 complex that sets up the main straight. This is the shortest sector, focused on exit speed optimization. T15 exit speed is paramount—every km/h lost here multiplies across the full main straight. DRS Zone 3 activates 170m after T15, enabling setup for T1 attack on the following lap. Cars that sacrifice S3 corner speed for reduced drag often struggle through the T14-T15 complex where balanced setups are rewarded.",
      keyFeatures: [
        'Shortest sector—focused on main straight setup',
        'T14-T15 complex determines main straight performance',
        'T15 exit critical—every km/h lost multiplies on main straight',
        'DRS Zone 3 activates 170m after T15 for T1 attack setup',
        'Balanced aero setup rewarded over low-drag compromise',
      ],
      criticalCorners: [
        'T13 - Right-hander entering final complex; positioning for T14 approach',
        'T14-T15 - Final complex; T15 exit speed paramount for main straight performance',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '50m before Turn 1 (unusually located in T1 braking zone)',
      activationPoint: '23m after Turn 3 exit',
      deactivationPoint: 'Turn 4 braking zone',
      description:
        "The primary DRS zone on the T3-T4 straight, uniquely detected in the T1 braking zone. Being within 1 second at detection enables DRS through the subsequent straight, creating compound attack opportunities. This zone is critical for continuing battles initiated into T1—cars that successfully defended the first attack remain vulnerable through this straight. The long zone length provides substantial speed advantage for the following car.",
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'Before Turn 9 (mid-Sector 2)',
      activationPoint: '50m after Turn 10 exit',
      deactivationPoint: 'Turn 11 braking zone',
      description:
        "The secondary DRS zone connecting Sector 2 to Sector 3, enabling attacks into the T11 hairpin. Detection before T9 means cars must be close through the demanding S2 corners to benefit. This shorter zone is valuable for converting position gained through the dirty-air-affected technical section into overtakes at the T11 hairpin.",
      effectiveness: 'Medium',
    },
    {
      zone: 3,
      detectionPoint: '110m before Turn 14 (late Sector 3)',
      activationPoint: '170m after Turn 15 exit',
      deactivationPoint: 'Turn 1 braking zone (next lap)',
      description:
        "The final zone of the lap, setting up T1 attacks on the following lap. Detection at T14 means cars must maintain proximity through the S3 medium-speed complex. This zone combined with slipstream effect on the main straight creates a significant speed advantage into the T1 braking zone, making this the most effective setup for overtaking attempts.",
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
        "Bahrain requires a delicate balance between straight-line speed and Sector 2 corner performance, reflected in Pirelli's 3/5 downforce rating. Teams face a crucial trade-off between top speed on the long straights and corner performance through the technical middle sector. In 2025, top speeds ranged from approximately 315–323 km/h in qualifying, reflecting varied aero philosophies across the grid. The Sector 2 dirty air effect means track position is extremely valuable—teams often accept slower qualifying pace for superior race-day tyre management and defensive capability. The 2025 race demonstrated that balanced or high-downforce setups can be optimal, with Piastri leading every lap.",
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C2 (Medium)', 'C3 (Soft)'],
      allocation: 'Hardest compound selection due to extreme surface abrasion (Pirelli 5/5)',
      primaryWearMechanism: 'Rear degradation through traction zones. Multiple low-speed exits (T1, T4, T10) stress rear tyres on acceleration. Front tyres experience less stress due to limited sustained lateral loads.',
      explanation:
        "Despite Bahrain's extreme surface abrasion (5/5 Pirelli rating—maximum on their scale), overall tyre stress remains average (3/5) because the track lacks long sequences of fast corners like Suzuka. The graywacke aggregate rapidly wears tyre surfaces, but the stop-start nature of the layout allows tyres to cool between stress events. The twilight race format provides additional relief as track temperatures drop 5-6°C from race start to finish. Vettel's legendary 2018 one-stop masterclass remains the benchmark for tyre management in modern F1, demonstrating the C1 Hard compound's exceptional durability when managed correctly.",
      strategicNote: 'Two-stop optimal (Laps 14-17, 32-37). One-stop viable with C1 Hard compound (Vettel 2018 benchmark). Safety Car historically frequent at Bahrain. Undercut potential HIGH due to S2 dirty air effect. Significant track evolution means early qualifiers are at risk until grip stabilizes.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium (3/5) - Desert surface with sand contamination; grip evolves significantly',
      impact: "Bahrain's circuit surface is defined by its extreme abrasiveness—the graywacke aggregate produces Pirelli's maximum asphalt abrasion rating (5/5), necessitating the hardest compound selection. However, initial grip is compromised by desert sand contamination, particularly in early sessions. Track evolution is significant (4/5) as rubber is laid down throughout the weekend, with the circuit improving by 2+ seconds from FP1 to Qualifying. This creates qualifying risk—drivers running early in sessions are vulnerable until all have completed their laps and grip levels stabilize. The twilight race format sees track temperatures drop from 30-45°C early in the weekend to 25-30°C during the race, significantly affecting tyre behavior.",
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Low',
    primaryZone: 'T1 - Heavy braking from 300+ km/h to ~60 km/h with DRS Zone 3 setup; widest overtaking window on circuit',
    secondaryZones: [
      'T4 - Continuation of T1 battles; DRS Zone 1 enables secondary attack on cars that defended into T1',
      'T11 - Tertiary opportunity following DRS Zone 2; tight hairpin enables late-braking moves',
    ],
    factors: [
      'Three DRS zones provide multiple attack opportunities per lap',
      'T1 offers best passing chance—heavy braking from 300+ km/h creates significant speed differential',
      'Long straights enable slipstream effect before braking zones',
      'Wide run-off areas allow aggressive divebombs with recovery options',
      'S2 dirty air effect severely hampers following through technical corners',
      'Variable desert wind conditions can affect car stability unpredictably',
      'Track position remains valuable despite multiple DRS zones',
      'Fresh tyres create meaningful pace advantage for overtaking attempts',
    ],
    recommendation:
      "Focus overtaking attempts at T1 using DRS Zone 3 and main straight slipstream. The combination of heavy braking from over 300 km/h down to approximately 60 km/h creates the largest overtaking window on the circuit. Conserve battery deployment through S2 when following, then deploy fully on straights. T4 provides continuation opportunities for battles initiated into T1—cars that successfully defend T1 remain vulnerable through DRS Zone 1. The T11 hairpin offers a tertiary option but the tighter nature limits success rate. Defensive drivers should prioritize T1 apex control—losing position there often means losing multiple places through subsequent DRS zones.",
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot, dry desert climate with twilight race format',
      airTemperature: {
        max: '33°C',
        min: '27°C',
        raceTime: '27-28°C (coolest—optimal for tyre performance)',
      },
      rainProbability: '<1% (rain extremely rare at Bahrain)',
      wind: 'Variable desert winds; can affect T10-T11 stability',
      humidity: 'Low (desert climate)',
    },
    sessionConditions: {
      fp1: '33°C air—hottest session of weekend',
      fp2: '29-30°C air—cooler twilight conditions representative of race',
      fp3: '32°C air—second hottest session',
      qualifying: '28-29°C air—evening session with improving track',
      race: '27-28°C air—coolest conditions with 5-6°C drop as sun sets and floodlights activate',
    },
    impact:
      "Bahrain's twilight race format creates a unique thermal challenge as the circuit transitions from scorching daytime heat to cooler evening conditions. Track temperatures can drop from 45°C early in the weekend to 25-30°C during the race, significantly affecting tyre behavior and degradation rates. The cooler race conditions provide some relief for tyre management but require teams to adapt setups throughout the weekend. Sand blown from the surrounding desert can accumulate on track, affecting grip unpredictably in earlier sessions. The stunning floodlit spectacle as the sun sets over the Sakhir desert is one of the most visually striking moments on the F1 calendar.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:31.447',
      driver: 'Pedro de la Rosa',
      year: 2005,
    },
    polePositions: [
      {
        year: 2022,
        time: '1:30.558',
        driver: 'LEC',
        note: 'Leclerc pole and win; Ferrari resurgence',
      },
      {
        year: 2023,
        time: '1:29.708',
        driver: 'VER',
        note: 'Verstappen pole and win; dominant Red Bull season opener',
      },
      {
        year: 2024,
        time: '1:29.179',
        driver: 'VER',
        note: 'Verstappen pole and Grand Slam victory',
      },
      {
        year: 2025,
        time: '1:29.841',
        driver: 'PIA',
        note: 'McLaren first Bahrain pole; Piastri won from pole',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:29.841' },
        { position: 2, driver: 'RUS', time: '1:30.009' },
        { position: 3, driver: 'LEC', time: '1:30.175' },
        { position: 4, driver: 'ANT', time: '1:30.213' },
        { position: 5, driver: 'GAS', time: '1:30.216' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '28.771s', driver: 'RUS' },
        { sector: 2, time: '38.574s', driver: 'PIA' },
        { sector: 3, time: '22.153s', driver: 'PIA' },
      ],
      overallIdealLap: '1:29.498',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'PIA',
        meanLapTime: '97.18s',
        gaps: [
          { driver: 'NOR', gap: '+0.39s' },
          { driver: 'RUS', gap: '+0.48s' },
          { driver: 'LEC', gap: '+0.50s' },
          { driver: 'HAM', gap: '+0.81s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '95.6s',
        gaps: [
          { driver: 'PER', gap: '+0.41s' },
          { driver: 'SAI', gap: '+0.47s' },
          { driver: 'LEC', gap: '+0.74s' },
          { driver: 'NOR', gap: '+0.83s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Alexander Albon / Isack Hadjar', speed: '323 km/h' },
        range: '315-323 km/h',
      },
      race: {
        withDRS: 'Up to 342 km/h (Hulkenberg with slipstream + DRS)',
        withoutDRS: '~303 km/h (Piastri clean air leader pace); ~324 km/h (Hulkenberg max no-DRS)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop: Laps 14-17 and Laps 32-37 (OPTIMAL)',
      factors: [
        'Two-stop strategy optimal; Safety Car on Lap 32 forced mass pit stops',
        'One-stop viable in theory (Vettel 2018 benchmark) but SC pushed field to two-stop',
        'Pit lane time loss: approximately 22-23 seconds',
        'Pit stop execution varied significantly across teams in 2025',
      ],
    },
    keyStrategicFactors: [
      'Undercut potential: HIGH—Russell pitted Lap 14 to cover Norris',
      'Ferrari (Leclerc) extended first stint to Lap 17 (Medium/Hard offset)',
      'Piastri led majority of laps; lost lead only during pit cycles',
      'Hulkenberg DSQ for excessive plank wear (floor management critical)',
    ],
    safetyCarLikelihood: 'Historically frequent—SC deployed in 2025 (Lap 32)',
    historicalNotes: [
      "2025: Piastri wins (McLaren's first Bahrain win); SC Lap 32 (Sainz/Tsunoda); Hulkenberg DSQ",
      '2024: Verstappen Grand Slam—pole, win, fastest lap, led every lap',
      '2023: Verstappen dominant victory; Red Bull 1-2',
      '2022: Leclerc/Sainz Ferrari 1-2',
      "2018: Vettel's one-stop masterclass remains the modern benchmark for tyre management",
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Desert Jewel',
      icon: 'flag',
      description: "F1's first Middle East GP (2004). Twilight race under stunning floodlights.",
    },
    {
      tag: 'Extreme Abrasion',
      icon: 'gauge',
      description: '5/5 Pirelli rating (maximum on their scale). Hardest compounds (C1-C3) mandatory.',
    },
    {
      tag: '20-Year Lap Record',
      icon: 'clock',
      description: "De la Rosa's 2005 record (1:31.447) still stands. Second-longest in F1 history.",
    },
    {
      tag: 'Testing Benchmark',
      icon: 'route',
      description: 'Pre-season test venue since 2014. Diverse corners reveal true car performance.',
    },
    {
      tag: 'Traction Zone',
      icon: 'speed',
      description: '4/5 Pirelli traction demand. T1, T4, T10 exits define lap time.',
    },
    {
      tag: 'Multi-DRS Challenge',
      icon: 'overtake',
      description: 'Three DRS zones with unique T1 braking zone detection point.',
    },
  ],

  fuelEffectPerKg: 0.034,
}
