import type { TrackIntelligence } from './types'

/**
 * Italian Grand Prix - Autodromo Nazionale Monza
 * Round 16 of the 2025 FIA Formula 1 World Championship
 * 
 * Known as the "Temple of Speed", Monza is the lowest downforce circuit on the
 * F1 calendar. Features very long and frequent full-throttle sections that prompt
 * teams to use extremely unloaded rear wings. Power unit performance, drag efficiency,
 * and braking stability are the primary differentiators. The 2025 race broke multiple
 * all-time F1 speed records.
 */
export const monzaTrackIntelligence: TrackIntelligence = {
  circuitId: 'monza',
  round: 16,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Autodromo Nazionale Monza',
    country: 'Italy',
    location: 'Monza, Lombardy, Italy',
    grandPrixName: 'Italian Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1950,
    description:
      'Monza is the lowest downforce circuit on the F1 calendar, featuring very long and frequent full-throttle sections that prompt teams to use extremely unloaded rear wings to minimize drag. The track places significantly less focus on cornering compared to most other circuits, with only 6 braking zones per lap. Power unit performance, drag efficiency, and braking stability are the primary performance differentiators. Known as the "Temple of Speed", Monza consistently produces the highest top speeds of the season, with cars exceeding 350 km/h on the main straight. The 2025 race saw multiple all-time F1 records broken, including fastest qualifying lap, fastest race, and fastest race lap.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.793,
      miles: 3.600,
    },
    raceDistance: {
      km: 306.72,
      miles: 190.587,
    },
    numberOfLaps: 53,
    numberOfCorners: 11,
    drsZones: 2,
    lapRecord: {
      time: '1:20.901',
      driver: 'Lando Norris',
      year: 2025,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-2.00°',
      },
      minStartingPressures: {
        front: '25.5 psi',
        rear: '23.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,           // Moderate - important for chicane exits
    tyreStress: 3,         // Moderate despite high speeds
    asphaltGrip: 3,        // Medium grip surface
    asphaltAbrasion: 2,    // Low - relatively gentle on tyres
    braking: 4,            // High - heavy braking into T1 and chicanes
    lateral: 2,            // Low - few high-speed corners
    downforce: 1,          // MINIMUM - lowest on calendar
    trackEvolution: 4,     // High - significant rubber buildup
  },

  energyProfile: {
    longitudinal: 'High',    // Heavy braking demands from high speed
    lateral: 'Low',          // Few sustained cornering loads
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
        'Two long full-throttle sections separated by the slow Rettifilo chicane. DRS Zone 1 on main straight produces maximum lap speeds (350+ km/h). Turn 1 braking is one of the hardest braking points on the entire calendar.',
      keyFeatures: [
        'Main straight with DRS Zone 1',
        'One of the the heaviest braking zones of the season',
        'Rettifilo chicane (T1-T2) requires precise turn-in',
        'Primary overtaking zone of the circuit',
      ],
      criticalCorners: [
        'T1-T2 (Rettifilo/Prima Variante) - Heavy braking from 350+ km/h, chicane exit crucial',
        'T3 (Curva Grande) - Fast right-hander, minimal lift',
      ],
    },
    {
      sector: 2,
      color: '#1E88E5',  // Blue
      corners: 'T4-T7',
      description:
        'Technical Roggia chicane followed by two fast right-hand corners (Lesmos), then downhill run with DRS Zone 2. Higher downforce configurations show strength through the Lesmos.',
      keyFeatures: [
        'Roggia chicane (T4-T5) tests car balance',
        'Lesmo 1 & 2 (T6-T7) taken at high speed',
        'DRS Zone 2 on back straight',
        'Downhill run to Ascari benefits from good traction',
      ],
      criticalCorners: [
        'T4-T5 (Roggia) - Tests car balance under braking and turn-in',
        'T6-T7 (Lesmo 1 & 2) - Fast right-handers rewarding aero stability',
      ],
    },
    {
      sector: 3,
      color: '#FDD835',  // Yellow
      corners: 'T8-T11',
      description:
        'Very fast Ascari chicane, non-DRS straight, and the iconic high-speed Parabolica corner. Parabolica exit speed directly correlates with main straight performance — the defining corner of Monza.',
      keyFeatures: [
        'Ascari (T8-T10) - triple-apex chicane at speed',
        'Short straight to Parabolica',
        'Parabolica (T11) taken at roughly ~240-260 km/h depending on car/conditions',
        'Poor Parabolica exit compromises entire main straight',
      ],
      criticalCorners: [
        'T8-T10 (Ascari) - High-commitment sequence, exit sets up Parabolica approach',
        'T11 (Parabolica/Alboreto) - 250+ km/h, full throttle on exit, rear stability essential',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Before Parabolica exit',
      activationPoint: 'After Parabolica',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        'Primary DRS zone on the 1.1km main straight. Cars reach 350+ km/h with DRS open. The primary overtaking opportunity — heavy braking into Turn 1 creates late-braking battles.',
      effectiveness: 'Very High',
    },
    {
      zone: 2,
      detectionPoint: 'After Lesmo 2',
      activationPoint: 'Before Ascari straight',
      deactivationPoint: 'Ascari entry',
      description:
        'Secondary DRS zone on the back straight. Sets up overtaking moves into the Ascari chicane.',
      effectiveness: 'High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Low',
      explanation:
        'Monza demands the lowest downforce configuration on the calendar — non-negotiable for competitive lap times. Teams run extreme low-drag rear wings: McLaren and Aston Martin use a gap between upper/lower planes with spooned lower plane; Ferrari, Red Bull, and Sauber use traditional horizontal lower plane with loaded upper plane; Mercedes and Alpine run unique bespoke designs. However, the "Monza Paradox" of 2025 showed that pure drag reduction doesn\'t guarantee pace — McLaren had the lowest top speed (337 km/h) but set fastest overall times, proving superior mechanical grip and braking performance can outweigh 11+ km/h straight-line deficit.',
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Standard allocation',
      primaryWearMechanism: 'Traction stress from chicane exits and high-speed braking',
      explanation:
        'Tyre degradation at Monza is relatively low due to few sustained cornering loads. The Medium compound was 0.4-0.5s faster than Hard and proved optimal for the first stint. Hard compound showed minimal degradation (~0.02s/lap). Soft was limited to 9 laps maximum (Lawson). The wide pit window (Laps 18-37) reflected the gentle tyre wear characteristics.',
      strategicNote: 'One-stop optimal: Medium → Hard (37+16 laps) used by race winner Verstappen.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium grip with significant track evolution',
      impact: 'Historic asphalt surface. Track rubbers in substantially through the weekend. High speeds mean traction and braking stability are paramount.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Low',
    primaryZone: 'Turn 1 (Rettifilo chicane, end of main straight)',
    secondaryZones: ['Ascari entry (DRS Zone 2 assistance)', 'Lesmo 1 entry (opportunistic)'],
    factors: [
      'Long main straight (1.1km) with DRS provides excellent slipstream',
      'Heavy braking into T1 creates late-braking opportunities',
      'DRS Zone 2 enables secondary moves into Ascari',
      'Chicanes allow defensive positioning but also divebomb attempts',
      'Slipstream effect very strong at 350+ km/h',
      'Pack racing possible when cars are close together',
    ],
    recommendation:
      'Position for DRS on main straight — the 350+ km/h approach to Turn 1 is the primary opportunity. Late braking into the Rettifilo chicane rewards commitment. DRS Zone 2 sets up secondary opportunities into Ascari.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Late summer, generally stable',
      airTemperature: {
        max: '30°C',
        min: '25°C',
        raceTime: '27°C',
      },
      rainProbability: 'Low (morning rain possible, afternoons typically dry)',
      wind: 'Light to moderate',
      humidity: 'Low to moderate',
    },
    sessionConditions: {
      fp1: '26°C, dry with light SW wind (60% morning rain chance)',
      fp2: '26°C, dry, mostly sunny',
      fp3: '26°C, mostly sunny, high clouds',
      qualifying: '26°C, dry, light S wind',
      race: '27°C, mostly sunny, dry throughout',
    },
    impact:
      'Consistent dry conditions throughout 2025 weekend allowed teams to optimize low-downforce setups without wet weather compromises. Late summer Italian weather provides stable, warm conditions ideal for the Temple of Speed.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:20.901',
      driver: 'Lando Norris',
      year: 2025,
    },
    polePositions: [
      {
        year: 2023,
        time: '1:20.294',
        driver: 'SAI',
      },
      {
        year: 2024,
        time: '1:19.327',
        driver: 'NOR',
      },
      {
        year: 2025,
        time: '1:18.792',
        driver: 'VER',
        note: 'Fastest qualifying lap in F1 history (264.681 km/h avg)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:18.792' },
        { position: 2, driver: 'NOR', time: '1:18.869' },
        { position: 3, driver: 'PIA', time: '1:18.982' },
        { position: 4, driver: 'LEC', time: '1:19.007' },
        { position: 5, driver: 'HAM', time: '1:19.124' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '26.219s', driver: 'HAM' },
        { sector: 2, time: '26.340s', driver: 'NOR' },
        { sector: 3, time: '26.047s', driver: 'VER' },
      ],
      overallIdealLap: '1:18.606',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '82.59s',
        gaps: [
          { driver: 'NOR', gap: '+0.27s' },
          { driver: 'PIA', gap: '+0.41s' },
          { driver: 'LEC', gap: '+0.46s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'PIA',
        meanLapTime: '83.54s',
        gaps: [
          { driver: 'NOR', gap: '+0.07s' },
          { driver: 'HAM', gap: '+0.36s' },
          { driver: 'LEC', gap: '+0.41s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Sauber cars', speed: '356 km/h' },
        range: '343-356 km/h',
      },
      race: {
        withDRS: 'Up to 365 km/h (Hamilton, DRS + slipstream)',
        withoutDRS: '336-339 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop strategy optimal (Medium → Hard)',
      factors: [
        'Wide pit window: Laps 18-37 due to low degradation',
        'Pit lane time loss ~24s seconds',
        'Medium compound ~0.5s faster than Hard',
        'Hard showed minimal degradation (~0.02s/lap)',
        'Soft limited to 9 laps maximum (Lawson)',
        'Overcut viable due to tyre longevity',
        'Verstappen strategy: 37 laps Medium + 16 laps Hard (race winner)',
      ],
    },
    keyStrategicFactors: [
      'One-stop dominant — two-stop not competitive',
      'Clean air at premium due to DRS trains',
      'Undercut potential moderate',
      'McLaren\'s extended Medium stint (46 laps) showed compound durability',
      'Esteban Ocon ran 51 laps on Hard (pitted final lap for compound rule)',
      'Ferrari had fastest pit stops (21.126s average)',
      'McLaren slow stop on Norris (+5.9s) and extended Medium stint opened gap to Verstappen',
    ],
    safetyCarLikelihood: 'Low - wide run-off areas reduce incident probability',
    historicalNotes: [
      '2025: Verstappen wins (3rd of season), multiple F1 records broken',
      '2025: Lap 1 contact Verstappen-Norris at T1, VER ordered to cede position',
      '2025: Verstappen retook lead legitimately Lap 4 around outside of Rettifilo',
      '2025: McLaren team orders — Piastri returned P2 to Norris after slow pit stop (Lap 49)',
      '2025: Fastest race in F1 history (250.706 km/h average)',
      '2025: Norris broke Barrichello\'s 21-year-old lap record (1:21.046, 2004)',
      '2024: Leclerc wins for Ferrari; Excellent tire management',
      'Ferrari most successful team at Monza (21 wins)',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Lowest Downforce',
      icon: 'aeroLow',
      description: 'Extreme low-drag rear wings — minimum downforce configuration (1/5)',
    },
    {
      tag: 'Temple of Speed',
      icon: 'speed',
      description: 'Only circuit where F1 cars consistently exceed 350 km/h (up to 365 km/h in 2025)',
    },
    {
      tag: 'Power Sensitive',
      icon: 'zap',
      description: 'Full throttle 72-76% of lap (highest on calendar), power unit efficiency critical',
    },
    {
      tag: 'Heavy Braking',
      icon: 'braking',
      description: 'T1 braking among hardest on calendar — 350+ km/h to 80 km/h',
    },
    {
      tag: 'Historic Venue',
      icon: 'trophy',
      description: 'One of world\'s oldest circuits (1922), 75+ F1 races hosted',
    },
    {
      tag: 'Record Breaker',
      icon: 'speed',
      description: '2025 broke fastest qualifying lap, fastest race, and fastest race lap records',
    },
  ],
}

