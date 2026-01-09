import type { TrackIntelligence } from './types'

/**
 * Saudi Arabian Grand Prix - Jeddah Corniche Circuit
 * Round 5 of the 2025 FIA Formula 1 World Championship
 *
 * The Jeddah Corniche Circuit represents one of the most ambitious additions to the
 * Formula 1 calendar, debuting in 2021 as a high-speed street circuit built along
 * the Red Sea waterfront. Designed by Carsten Tilke in conjunction with F1's Motorsports
 * team, the circuit was conceived to be the fastest street track in Formula 1 history—
 * and it delivers, with average speeds around 250 km/h rivaling permanent circuits
 * like Silverstone.
 *
 * At 6.174 km, Jeddah is the third-longest circuit on the calendar (after Spa and
 * Las Vegas) and features a remarkable 27 corners—the most of any F1 track. The layout
 * runs parallel to the coast in a narrow out-and-back configuration, with walls
 * positioned dangerously close to the racing line throughout. Three DRS zones and
 * multiple high-speed sweeping corners create a unique challenge where driver
 * confidence and aerodynamic efficiency are paramount.
 *
 * The 2025 edition saw Oscar Piastri take his second consecutive win after a dramatic
 * opening-lap battle with Max Verstappen. Verstappen took pole with a new qualifying
 * lap record of 1:27.294, but a 5-second penalty for cutting T1 while defending from
 * Piastri handed the McLaren driver victory by 2.8 seconds. The race maintained
 * Jeddah's 100% Safety Car deployment record after a first-lap collision between
 * Tsunoda and Gasly.
 */
export const jeddahTrackIntelligence: TrackIntelligence = {
  circuitId: 'jeddah',
  round: 5,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Jeddah Corniche Circuit',
    country: 'Saudi Arabia',
    location: 'Jeddah, Red Sea Coast',
    grandPrixName: 'Saudi Arabian Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 2021,
    description:
      "Often described as the fastest street circuit, the Jeddah Corniche Circuit sees average lap speeds above ~250 km/h. Built along the stunning Red Sea waterfront, this semi-permanent circuit features 27 corners (the most on any F1 track) packed into 6.174 km of racing. The layout combines long straights with fast, flowing corners that demand exceptional driver confidence with walls positioned mere centimeters from the racing line. Unlike traditional street circuits with slow chicanes, Jeddah derives its character from high-speed sweepers where lifting means losing. The circuit joined the calendar in 2021 during the dramatic Hamilton-Verstappen title fight and has delivered memorable action in every edition. Pirelli's data confirms cornering performance (Lateral 4/5) is the critical factor, while the low-abrasion asphalt (2/5) enabled the use of C3-C5 compounds—one step softer than 2024. The low downforce requirement (2/5) emphasizes the need for aerodynamic efficiency over raw downforce.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 6.174,
      miles: 3.836,
    },
    raceDistance: {
      km: 308.45,
      miles: 191.634,
    },
    numberOfLaps: 50,
    numberOfCorners: 27,
    drsZones: 3,
    lapRecord: {
      time: '1:30.734',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '25.5 psi',
        rear: '21.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED & CORRECTED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 2,          // Low - fast corners allow easy power deployment; minimal traction demand
    asphaltGrip: 4,       // High - purpose-built asphalt provides excellent mechanical grip
    asphaltAbrasion: 2,   // Low - smooth surface enables softest compounds (C3-C5)
    trackEvolution: 4,    // High - significant grip improvement as rubber is laid down
    tyreStress: 3,        // Medium - softer compounds increase wear despite low-abrasion surface
    braking: 3,           // Medium - fewer heavy braking zones; T1, T13, T27 are key
    lateral: 4,           // High - fast sweeping corners demand strong lateral performance (KEY FACTOR)
    downforce: 2,         // Low-Medium - long straights require efficiency over raw downforce
  },

  energyProfile: {
    longitudinal: 'Medium',   // Moderate braking demands; T27 hairpin is heaviest zone
    lateral: 'High',          // Sustained lateral loads through S1 and S2 fast corners
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T12',
      description:
        "The slowest sector in absolute terms, yet still remarkably quick by F1 standards. Features numerous medium-speed corners including the T1-T4 complex and a succession of direction changes through T5-T12. Higher wing loads benefit here as the drag penalty is minimal through the twisty sections. This sector tests mechanical grip and car balance through sustained cornering.",
      keyFeatures: [
        'T1-T2: Left-right chicane from start/finish; primary Lap 1 incident zone',
        'T3-T4: Medium-speed complex leading into the S-bends',
        'T5-T12: Succession of medium-speed direction changes; precision required',
        'Many 90° corners testing mechanical grip',
        'Higher downforce benefits here—drag penalty is minimal',
        'Most forgiving sector for setup compromises',
        'Sector 1 ends after T12, before the fast T13 complex',
      ],
      criticalCorners: [
        'T1-T2 - Opening chicane; Verstappen/Piastri 2025 incident location; high Lap 1 risk',
        'T4-T5 - Direction change complex; Norris 2025 qualifying crash location',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T13-T21', // FIA sector line before T22
      description:
        "The sector that defines Jeddah—a relentless succession of fast, flowing corners where driver confidence separates the elite from the rest. The banked T13 hairpin (~12° banking) initiates a high-speed run through T14-T21, with minimal time to recover from any mistake. A 'snappy' rear end destroys confidence here, as the driver must commit fully through blind apexes with walls inches away. Contains DRS Zone 1 on the run toward T22. Intermediate characteristics between Sectors 1 and 3.",
      keyFeatures: [
        'T13: ~12° banked hairpin—unique on calendar; initiates fast section',
        'T14-T20: High-speed sweeping sequence requiring total commitment',
        'Walls extremely close throughout—zero margin for error',
        'Rewards high downforce and rear stability',
        'DRS Zone 1 active through this sector',
        'Sector 2 ends before T22',
      ],
      criticalCorners: [
        'T13 (Banked Hairpin) - ~12° banking; sets up the fast section; unique corner',
        'T21 - Exit speed critical for approaching T22 and S3',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T22-T27', // FIA sector line includes T22
      description:
        "The fastest sector featuring the long straights connected by the T27 hairpin—the circuit's primary overtaking zone. Low drag is paramount here as top speeds can exceed ~340 km/h with DRS. Braking stability into T27 is critical; the heavy braking zone from around ~320 km/h down to ~80-90 km/h is the biggest stopping challenge of the lap. Contains DRS Zones 2 and 3. This sector is where races are won and lost, with the T27 hairpin being the premier overtaking spot.",
      keyFeatures: [
        'T22: Fast left; DRS Zone 2 detection point',
        'T23-T25: Fast kinks maintaining high speed before T26 straight',
        'Main straight: DRS Zone 2 active; ~340 km/h achievable with DRS',
        'Speed trap located before T27 braking zone',
        'T26: Fast right kink onto approach to T27',
        'T27: Slow hairpin (~80-90 km/h); primary overtaking zone',
        'DRS Zone 3 from T27 exit to start/finish line',
      ],
      criticalCorners: [
        'T27 (Hairpin) - Primary overtaking zone; heavy braking from ~320 km/h to ~80-90 km/h',
        'T25-T26 - High-speed approach; exit speed determines straight-line potential',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '40m after T17',
      activationPoint: '170m after T19',
      deactivationPoint: '80m after T22',
      description:
        "The mid-circuit DRS zone through the fast Sector 2 sequence. Less commonly used for direct overtaking due to the fast-corner nature, but helps following cars stay within range through the demanding high-speed sweepers.",
      effectiveness: 'Medium',
    },
    {
      zone: 2,
      detectionPoint: 'Entry to T22',
      activationPoint: 'Entry to T25',
      deactivationPoint: 'T27 braking zone',
      description:
        "The main passing tool on the long straight leading to the T27 hairpin. If you're close through T22, you can deploy here and build a big speed advantage before the heaviest braking zone on the lap.",
      effectiveness: 'High',
    },
    {
      zone: 3,
      detectionPoint: '40m after T27',
      activationPoint: '240m after T27',
      deactivationPoint: 'T1 braking zone',
      description:
        "Short zone on the run to the start/finish line. More about staying attached and setting up a T1 look on the next lap than making a pass here—but with slipstream it can create pressure into the opening chicane.",
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
        "Jeddah demands aerodynamic efficiency over raw downforce, reflected in Pirelli's 2/5 downforce rating. The circuit would rival Monza as 'the temple of speed' if not for the Italian track's legendary status. However, Jeddah differs from Monza significantly—its high average speed comes from fast corners rather than long straights. Teams must maintain sufficient downforce to manage tyres through Sector 2's sweepers while minimizing drag for Sector 3's straights. In 2025, McLaren ran a less loaded rear wing than Ferrari, Mercedes, and Red Bull—compensating for their inherently high-drag car. Red Bull's unique design omitted the spoon on the lower plane. Haas and Ferrari ran the most loaded wings, while Alpine and Racing Bulls went with minimal load—the latter potentially struggling with tyre wear over stint distances.",
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'One step softer than 2024 due to low-abrasion surface',
      primaryWearMechanism: 'Lateral degradation through Sector 2 high-speed sweepers. Rear tyres stressed through sustained cornering loads. Front tyres experience understeer-induced wear in fast direction changes.',
      explanation:
        "Pirelli confirms cornering performance is critical at Jeddah, with braking somewhat less significant, and traction minimal since most corners are fast enough to deploy power easily. The low-abrasion asphalt (2/5) allowed the softest compound selection (C3-C5), one step softer than 2024. Despite softer tyres, degradation remained manageable—Leclerc extended the opening Medium stint to Lap 29 before switching to Hard; Norris ran long on the opening Hard stint and switched around Lap 34. Several drivers managed very long stints once the race settled after the early incident. The Medium compound proved the optimal race tyre, offering excellent pace with moderate degradation.",
      strategicNote: 'One-stop dominant (Medium-Hard preferred). Extended Medium stints possible with good management. Hard compound slower but extremely consistent—degradation almost nonexistent. Safety Car highly likely (100% historical rate)—strategic flexibility essential.',
    },
    surfaceCharacteristics: {
      gripLevel: 'High (4/5) - Purpose-built low-abrasion asphalt provides excellent grip',
      impact: 'The circuit features purpose-built racing asphalt that provides high grip levels (4/5) while causing minimal tyre abrasion (2/5). Track evolution is significant (4/5) as the surface improves throughout the weekend with rubber accumulation. The combination of high grip and low abrasion creates an unusual situation where teams can push hard on softer compounds without excessive degradation. Sand blown onto the circuit from the desert environment can affect grip unpredictably, particularly in earlier sessions.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'T27 (Hairpin) - Heavy braking from ~320 km/h with DRS Zone 2 advantage; slowest corner on circuit',
    secondaryZones: [
      'T1 (Chicane) - Medium braking from start/finish with DRS Zone 3; more effective at race start',
      'T22 approach - End of DRS Zone 1; fast corner limits late-braking but slipstream effective',
    ],
    factors: [
      'Three DRS zones provide multiple opportunities per lap',
      'T27 hairpin offers best passing chance—significant speed differential (~320 to ~80-90 km/h)',
      'Despite DRS zones, overtaking proved difficult in 2025—Norris struggled to pass Hamilton',
      'Slipstream powerful on main straight but dirty air hurts through Sector 2 sweepers',
      'Walls close throughout limit alternative lines and recovery from failed attempts',
      'Track position remains valuable despite DRS assistance',
      'Fresh tyres create meaningful pace advantage for overtaking attempts',
      'Safety Car restarts create bunched-field opportunities',
    ],
    recommendation:
      "Focus overtaking attempts at T27 hairpin using DRS Zone 2 from the main straight. The combination of very heavy braking from around ~320 km/h down to ~80-90 km/h creates the largest overtaking window on the circuit. T1 provides a secondary opportunity, particularly at race start and Safety Car restarts. Despite three DRS zones, overtaking remains challenging as demonstrated by Norris's difficulty passing Hamilton in 2025—the McLaren driver required multiple laps and DRS assistance to complete what should have been a straightforward pass. Patience and tyre management are essential; creating a significant pace delta is more effective than repeated high-risk attempts.",
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Hot desert/coastal climate with negligible rain probability',
      airTemperature: {
        max: '34°C',
        min: '22°C',
        raceTime: '29-31°C',
      },
      rainProbability: 'Virtually zero (0%)',
      wind: 'Northwestern breeze, typically 15-35 km/h with gusts',
      humidity: 'Moderate to high (40-60%) due to Red Sea proximity',
    },
    sessionConditions: {
      fp1: '31°C air, sunny, NW wind gusts to 30 km/h',
      fp2: '29°C air, sunny, lighter wind',
      fp3: '32°C air, sunny (hottest day), NW gusts to 30 km/h',
      qualifying: '31°C air, clear, wind decreasing',
      race: '31°C air, clear, NW gusts to 35 km/h decreasing through race',
    },
    impact:
      "Jeddah's desert coastal climate ensures dry conditions but presents cooling challenges for power units and drivers. The race takes place under spectacular floodlights (1,500 lux) as temperatures drop from daytime peaks. Northwestern winds can affect car stability through fast corners, particularly in the exposed Sector 3 straights. Red Sea humidity impacts power unit cooling efficiency. The April date (moved from March to avoid Ramadan since 2025) typically sees temperatures ranging from 22-34°C. Sand blown from the surrounding desert can accumulate on track, affecting grip particularly in early sessions.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:30.734',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    polePositions: [
      {
        year: 2021,
        time: '1:27.511',
        driver: 'HAM',
        note: 'Inaugural Saudi GP; dramatic Hamilton-Verstappen title fight',
      },
      {
        year: 2022,
        time: '1:28.200',
        driver: 'PER',
        note: 'Pérez pole; Verstappen won race',
      },
      {
        year: 2023,
        time: '1:28.265',
        driver: 'PER',
        note: 'Pérez pole and race win; Red Bull 1-2',
      },
      {
        year: 2024,
        time: '1:27.472',
        driver: 'VER',
        note: 'Verstappen pole and race win',
      },
      {
        year: 2025,
        time: '1:27.294',
        driver: 'VER',
        note: 'NEW TRACK RECORD; beat Piastri by 0.010s; Norris crashed in Q3',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:27.294' },
        { position: 2, driver: 'PIA', time: '1:27.304' },
        { position: 3, driver: 'RUS', time: '1:27.407' },
        { position: 4, driver: 'LEC', time: '1:27.670' },
        { position: 5, driver: 'ANT', time: '1:27.866' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '31.507s', driver: 'VER' },
        { sector: 2, time: '27.550s', driver: 'RUS' },
        { sector: 3, time: '27.989s', driver: 'PIA' },
      ],
      overallIdealLap: '1:27.046',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '93.19s',
        gaps: [
          { driver: 'PIA', gap: '+0.04s' },
          { driver: 'LEC', gap: '+0.23s' },
          { driver: 'NOR', gap: '+0.24s' },
          { driver: 'RUS', gap: '+0.64s' },
          { driver: 'ANT', gap: '+0.72s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '92.93s',
        gaps: [
          { driver: 'PER', gap: '+0.23s' },
          { driver: 'LEC', gap: '+0.46s' },
          { driver: 'NOR', gap: '+0.59s' },
          { driver: 'HAM', gap: '+0.70s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Nico Hulkenberg', speed: '339 km/h' },
        range: '~330-339 km/h',
      },
      race: {
        withDRS: 'Up to ~343 km/h with DRS/slipstream (reported, situational)',
        withoutDRS: 'Low-to-mid 310s km/h typical in clean air',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop: Laps 16-22 (Medium to Hard)',
      factors: [
        'One-stop strategy dominant; Medium-Hard (M-H) preferred',
        'Extended Medium stints effective—Leclerc managed 29-30 laps on full fuel',
        'Hard compound very consistent; Norris ran 34 laps on Hards before stopping',
        'Verstappen served 5s penalty during pit stop, costing track position',
        'Safety Car on Lap 1 (Gasly-Tsunoda crash) neutralized early strategic split',
      ],
    },
    keyStrategicFactors: [
      'Verstappen 5s penalty (T1 incident) decided race; finished +2.8s behind Piastri',
      'Piastri took championship lead; first Australian since Mark Webber (2010)',
      'Piastri second consecutive win (following Bahrain)',
      'Norris P10 to P4 recovery using Reverse Strategy (Hard-Medium)',
      'McLaren first Jeddah win; broke Red Bull winning streak (2022-2024)',
    ],
    safetyCarLikelihood: '100% (SC deployed in every Saudi GP 2021-2025)',
    historicalNotes: [
      '2025: Piastri wins; Verstappen Pole (1:27.294); Lap 1 SC (Gasly-Tsunoda)',
      '2024: Verstappen dominant victory',
      '2023: Pérez pole and win',
      '2022: Verstappen win after Leclerc battle',
      '2021: Hamilton win in inaugural race',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Fastest Street Circuit',
      icon: 'speed',
      description: '~250 km/h average speed. ~340 km/h with DRS on main straight.',
    },
    {
      tag: 'Maximum Corners',
      icon: 'route',
      description: '27 corners—most on any F1 circuit. Relentless direction changes test concentration.',
    },
    {
      tag: 'Wall Proximity',
      icon: 'alertTriangle',
      description: 'Barriers inches from racing line throughout. Zero margin for error. High commitment required.',
    },
    {
      tag: '100% Safety Car Rate',
      icon: 'strategy',
      description: 'Safety Car deployed in every Saudi GP since 2021. Strategic flexibility essential.',
    },
    {
      tag: 'Night Racing Spectacle',
      icon: 'night',
      description: 'Stunning floodlit racing on Red Sea waterfront. High-intensity floodlighting for night running.',
    },
    {
      tag: 'Lateral Dominance',
      icon: 'lateral',
      description: 'Pirelli 4/5 Lateral rating. Fast sweepers through S2 demand exceptional cornering grip.',
    },
  ],
}

