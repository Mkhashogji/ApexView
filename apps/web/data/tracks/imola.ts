import type { TrackIntelligence } from './types'

/**
 * Emilia Romagna Grand Prix - Autodromo Internazionale Enzo e Dino Ferrari
 * Round 7 of the 2025 FIA Formula 1 World Championship
 *
 * The Autodromo Internazionale Enzo e Dino Ferrari, commonly known as Imola,
 * is one of Formula 1's most beloved traditional circuits. Named after Enzo
 * Ferrari and his son Dino, the circuit sits just 40km from Ferrari's Maranello
 * headquarters, making it a spiritual second home for the Scuderia.
 *
 * Imola is characterized by its anti-clockwise direction, significant elevation
 * changes, and old-school character with limited run-off areas. The circuit
 * returned to the F1 calendar in 2020 after a 14-year absence and has hosted
 * the Emilia Romagna GP since then.
 *
 * 2025 marks the final Emilia Romagna GP as the race was not renewed for 2026,
 * being replaced by the Madrid street circuit. This was also Red Bull's 400th
 * Formula 1 Grand Prix and saw the debut of Pirelli's C6 compound.
 */
export const imolaTrackIntelligence: TrackIntelligence = {
  circuitId: 'imola',
  round: 7,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Autodromo Internazionale Enzo e Dino Ferrari',
    country: 'Italy',
    location: 'Imola, Emilia-Romagna, Italy',
    grandPrixName: 'Emilia Romagna Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1980,
    description:
      "The Autodromo Internazionale Enzo e Dino Ferrari, commonly known as Imola, is one of Formula 1's most beloved traditional circuits. Named after Enzo Ferrari and his son Alfredo 'Dino' Ferrari, the circuit sits just 40km from Ferrari's Maranello headquarters, making it the Scuderia's spiritual second home where passionate tifosi create an electric atmosphere. The anti-clockwise circuit features significant elevation changes (26m total variation), limited run-off areas that punish mistakes, and a single DRS zone that makes track position paramount. Imola hosted the Italian GP in 1980, then the San Marino GP from 1981-2006 before returning as the Emilia Romagna GP in 2020. The circuit is forever marked by the 1994 tragedies of Ayrton Senna and Roland Ratzenberger, which transformed F1 safety standards. 2025 marks the final Emilia Romagna GP as the race was not renewed for 2026, being replaced by the Madrid street circuit.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 4.909,
      miles: 3.050,
    },
    raceDistance: {
      km: 309.051, // Per FIA race classification
      miles: 192.036,
    },
    numberOfLaps: 63,
    numberOfCorners: 19,
    drsZones: 1,
    lapRecord: {
      time: '1:15.484',
      driver: 'Lewis Hamilton',
      year: 2020,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.50°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '24.5 psi',
        rear: '22.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 2,          // Low-medium - chicanes require good traction but not extreme
    asphaltGrip: 2,       // Low-medium - older resurfaced asphalt
    asphaltAbrasion: 2,   // Low-medium - moderate surface roughness
    trackEvolution: 2,    // Low-medium - consistent grip levels through weekend
    tyreStress: 3,        // Medium - balanced demands on tyres
    braking: 3,           // Medium - several heavy braking zones but not extreme
    lateral: 3,           // Medium - flowing corners require sustained lateral load
    downforce: 3,         // Medium - balanced aero requirements for mixed layout
  },

  energyProfile: {
    longitudinal: 'Medium',   // Multiple chicanes and braking zones
    lateral: 'High',          // High-speed flowing sections demand lateral grip
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T6',
      description:
        "Power and precision sector featuring two straights interrupted by the Tamburello and Villeneuve chicanes. Contains the only DRS zone on the main straight, making this the primary overtaking opportunity. The sector requires excellent traction out of slow chicanes to maximize straight-line speed.",
      keyFeatures: [
        'Main straight with single DRS zone - primary overtaking opportunity',
        'T1 (Tamburello Entry): Heavy braking from ~320 km/h to ~160 km/h',
        'T2-T3 (Variante Tamburello): Fast chicane replacing original corner after 1994',
        'T4 (Second Straight): Short blast before Villeneuve chicane',
        'T5-T6 (Variante Villeneuve): Tight chicane named after Gilles, traction critical',
        'Anti-clockwise direction unique among European circuits',
      ],
      criticalCorners: [
        'T2-T3 (Variante Tamburello) - Fast chicane at 160 km/h, site of Senna memorial',
        'T5-T6 (Variante Villeneuve) - Tight chicane, traction out of T6 determines straight speed to Tosa',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T7-T13', // FIA sector line: 190m before T14
      description:
        "The most technically demanding sector featuring Imola's signature corners. Begins with the Tosa hairpin, climbs through elevation changes at Piratella (highest point at 47m), then descends through the spectacular Acque Minerali complex where car balance is critical.",
      keyFeatures: [
        'T7 (Tosa): 180° hairpin, heavy braking, potential overtaking spot',
        'T8 (Piratella): Fast right-hander at circuit\'s highest elevation (47m)',
        'T9 (Circuit Descent): Rapid elevation drop begins',
        'T10-T12 (Acque Minerali): Spectacular downhill complex, car balance critical',
        'T13 (Variante Bassa entry): Lowest point at 21m',
        'Crest at Piratella, then a sharp drop into Acque Minerali',
      ],
      criticalCorners: [
        'T7 (Tosa) - 180° hairpin from ~260 km/h to ~80 km/h, secondary overtaking opportunity',
        'T10-T12 (Acque Minerali) - Complex of corners where car balance under braking is tested',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T14-T19', // FIA sector line: 190m before T14
      description:
        "Rhythm and commitment sector completing the lap. Features Variante Bassa exit, the back straight, Variante Alta chicane, and the famous Rivazza double-apex corner that sets up the run onto the main straight. Precision through Rivazza determines lap time potential.",
      keyFeatures: [
        'T14 (Variante Bassa exit): Leads onto back straight',
        'Back straight: Building speed toward Variante Alta',
        'T15-T16 (Variante Alta): Fast chicane requiring commitment',
        'T17-T18 (Rivazza 1 & 2): Famous double-apex left-handers',
        'T19: Final right onto main straight, exit speed critical',
        'Clean exit from Rivazza determines following lap\'s S1 time',
      ],
      criticalCorners: [
        'T15-T16 (Variante Alta) - High-speed chicane at ~180 km/h, commitment required',
        'T17-T18 (Rivazza) - Double-apex where lap time is made or lost; clean exit essential',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '385m before T17 (approach to Rivazza)',
      activationPoint: '40m after T19 (onto the main straight)',
      deactivationPoint: 'T1 braking zone (Tamburello Entry)',
      description:
        "Single DRS run on the main straight. With only one assisted straight, qualifying and clean air matter a lot, and race position is hard to recover once you're stuck in a train. The ~28s pit lane time loss (one of the longest on calendar) amplifies track position importance.",
      effectiveness: 'Medium',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium-High',
      explanation:
        "Imola requires a balanced aerodynamic setup given its mixed character—flowing high-speed sections through Piratella and Acque Minerali demand downforce, while the single DRS zone on the main straight means some drag sensitivity exists. Teams typically run medium-high downforce, slightly lower than Monaco but higher than Monza. The anti-clockwise direction creates asymmetric tyre loading, with the right-front particularly stressed. The 26m elevation change also affects aerodynamic balance as cars transition through different ride heights.",
    },
    tyreManagement: {
      compounds: ['C4 (Hard)', 'C5 (Medium)', 'C6 (Soft)'],
      allocation: 'Softest available compounds - C6 debut at Imola in 2025',
      primaryWearMechanism: 'Front-left degradation from anti-clockwise direction. The C6 soft compound proved too fragile for race stints—teams avoided it for race use, reserving it primarily for qualifying. Graining was observed on softer compounds during early stints before track evolution.',
      explanation:
        "Pirelli brought their softest range (C4-C6) to Imola, with 2025 marking the debut of the experimental C6 compound. However, the C6 proved unsuitable for race conditions—rapid degradation made it a qualifying-only tyre. The two-stop strategy dominated due to the softer compound range compared to 2024 (which used C3-C5). The undercut proved extremely powerful due to clean air advantage.",
      strategicNote: 'Two-stop dominant in 2025. C6 too soft for racing. Undercut powerful due to clean air. Hard compound (C4) offered most consistent race pace.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium - resurfaced sections provide decent grip but evolution occurs through weekend',
      impact: 'The circuit was partially resurfaced after returning to the calendar in 2020. Track evolution is moderate (rated 2/5) with consistent grip levels. The anti-clockwise direction creates unique loading patterns—right-side tyres work harder. Weather can be variable in spring, with the 2023 race famously cancelled due to Storm Minerva flooding.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'High',
    primaryZone: 'T1-T3 (Variante Tamburello) - Heavy braking from 320 km/h with DRS advantage from main straight',
    secondaryZones: [
      'T7 (Tosa Hairpin) - 180° hairpin offers secondary opportunity with heavy braking from 260 km/h',
    ],
    factors: [
      'Single DRS zone severely limits overtaking opportunities',
      'Track position premium is among the highest on calendar',
      '~28s pit lane time loss (one of longest on calendar) makes strategic overtaking costly',
      'Narrow track width through chicanes prevents side-by-side racing',
      'Anti-clockwise direction unusual—drivers less practiced at these moves',
      'Limited run-off punishes aggressive moves that go wrong',
      'Verstappen\'s 2025 Lap 1 outside pass at Tamburello was exceptional and rare',
      'Tosa hairpin offers theoretical opportunity but track position usually maintained',
    ],
    recommendation:
      'Focus overtaking attempts at Variante Tamburello (T1-T3) using DRS from the main straight—the heavy braking from 320 km/h provides the best window. Tosa hairpin (T7) offers a secondary opportunity but success rate is lower. The 2025 race demonstrated that decisive Lap 1 moves can be executed by elite drivers (Verstappen\'s stunning outside pass on Piastri), but such moves are high risk. For most situations, strategic pit stop timing via the undercut is more reliable than on-track passes.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Temperate continental climate with variable spring weather (Köppen: Cfa)',
      airTemperature: {
        max: '24°C',
        min: '12°C',
        raceTime: '18-22°C',
      },
      rainProbability: 'Medium (30-40%) - spring weather can be unpredictable',
      wind: 'Variable, typically light 5-15 km/h from varying directions',
      humidity: 'Moderate to high (55-70%)',
    },
    sessionConditions: {
      fp1: '19°C air / 38°C track, sunny',
      fp2: '20°C air / 42°C track, sunny',
      fp3: '18°C air / 35°C track, partly cloudy',
      qualifying: '21°C air / 40°C track, sunny',
      race: '22°C air / 44°C track, sunny becoming partly cloudy',
    },
    impact:
      "Imola's spring timing makes weather unpredictable. The 2023 Emilia Romagna GP was cancelled entirely due to catastrophic flooding from Storm Minerva that devastated the region. In normal conditions, the temperate climate provides comfortable racing temperatures, but cloud cover can develop quickly from the Apennine mountains. The 2025 race enjoyed optimal dry conditions throughout the weekend.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:15.484',
      driver: 'Lewis Hamilton',
      year: 2020,
    },
    polePositions: [
      {
        year: 2020,
        time: '1:13.609',
        driver: 'BOT',
        note: 'All-time qualifying record; first Imola GP in 14 years',
      },
      {
        year: 2021,
        time: '1:14.411',
        driver: 'HAM',
        note: 'Dry session; slower than 2020 due to aero regs',
      },
      {
        year: 2022,
        time: '1:27.999',
        driver: 'VER',
        note: 'Wet qualifying, not representative of pace',
      },
      {
        year: 2024,
        time: '1:14.746',
        driver: 'VER',
        note: 'Verstappen pole by 0.074s over Piastri',
      },
      {
        year: 2025,
        time: '1:14.670',
        driver: 'PIA',
        note: 'Piastri pole by 0.034s over Verstappen',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:14.670' },
        { position: 2, driver: 'VER', time: '1:14.704' },
        { position: 3, driver: 'RUS', time: '1:14.807' },
        { position: 4, driver: 'NOR', time: '1:14.962' },
        { position: 5, driver: 'ALO', time: '1:15.431' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Qualifying',
      sectors: [
        { sector: 1, time: '23.909s', driver: 'VER' },
        { sector: 2, time: '26.055s', driver: 'PIA' },
        { sector: 3, time: '24.538s', driver: 'NOR' },
      ],
      overallIdealLap: '1:14.502',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '80.31s',
        gaps: [
          { driver: 'NOR', gap: '+0.18s' },
          { driver: 'PIA', gap: '+0.24s' },
          { driver: 'LEC', gap: '+0.58s' },
          { driver: 'RUS', gap: '+0.87s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'NOR',
        meanLapTime: '80.86s',
        gaps: [
          { driver: 'VER', gap: '+0.02s' },
          { driver: 'LEC', gap: '+0.10s' },
          { driver: 'PIA', gap: '+0.21s' },
          { driver: 'RUS', gap: '+0.26s' },
        ],
      },
    ],
    topSpeedReference: {
        qualifying: {
          // Verstappen was fastest (331); Piastri was actually slowest (323) due to drag
          fastest: { driver: 'Max Verstappen', speed: '331 km/h' },
          range: '323-331 km/h',
        },
        race: {
          // Hadjar/Stroll hit 349 km/h with DRS+Tow
          withDRS: 'Up to 349 km/h (Hadjar/Stroll in traffic)',
          // Verstappen led the whole race (no DRS) peaking at 311 km/h
          withoutDRS: '~309-311 km/h (Verstappen/Norris clean air)',
        },
      },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop: Laps 16-22 (first stop), Laps 38-45 (second stop)',
      factors: [
        'Two-stop strategy dominant in 2025 due to softer compound range (C4-C6)',
        'Pit lane time loss: ~28s (one of the longest on calendar, per F1.com/Pirelli)',
        'Single DRS zone makes track position premium extremely high',
        'Undercut extremely powerful due to clean air advantage',
        'C6 soft compound too fragile for race use—qualifying only',
        'Hard compound (C4) offered most consistent race pace',
        'Long pit lane loss makes one-stop theoretically attractive but degradation forced two stops',
        'VSC/SC probability medium-high (45-55%) due to limited run-off',
      ],
    },
    keyStrategicFactors: [
      'Verstappen won from P2 with stunning Lap 1 outside pass at Tamburello',
      'McLaren locked out front row but Piastri lost lead on Lap 1',
      'Red Bull\'s 400th Grand Prix—milestone race',
      'Final Emilia Romagna GP (not renewed for 2026, replaced by Madrid)',
      'C6 compound debut—proved too soft for race conditions',
      'Ferrari home race pressure—40km from Maranello',
      'Clean pit stops critical given ~28s time loss',
    ],
    safetyCarLikelihood: 'Medium-High (~45-55% probability - limited run-off increases incident risk)',
    historicalNotes: [
      '2025: Verstappen wins from P2 with stunning Lap 1 pass; final Emilia Romagna GP',
      '2023: Race CANCELLED due to Storm Minerva flooding—regional disaster',
      '2022: Verstappen wins from pole in wet/dry conditions',
      '2021: Verstappen wins after Hamilton error at Tosa; red flag restart drama',
      '2020: Hamilton wins inaugural Emilia Romagna GP; Mercedes clinch constructors title',
      '2006: Last San Marino GP—Schumacher wins in front of tifosi',
      '1994: Tragic weekend—Ratzenberger (Sat) and Senna (Sun) fatalities transformed F1 safety',
      '1985: First Imola GP for Minardi—local team debut',
      'Michael Schumacher record 7 wins at Imola',
      'Ferrari record 8 constructor wins—true home circuit',
      'Named after Enzo Ferrari and son Alfredo "Dino" Ferrari',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Ferrari\'s Second Home',
      icon: 'flag',
      description: '40km from Maranello. Passionate tifosi atmosphere. Named after Enzo and Dino Ferrari.',
    },
    {
      tag: 'Single DRS Zone',
      icon: 'lock',
      description: 'Track position paramount. ~28s pit loss (one of longest). Qualifying critical.',
    },
    {
      tag: 'Anti-Clockwise Challenge',
      icon: 'rotate',
      description: 'One of few anti-clockwise circuits. Asymmetric tyre loading tests setups.',
    },
    {
      tag: 'Old-School Character',
      icon: 'track',
      description: 'Limited run-off areas. 26m elevation change. Mistakes are punished immediately.',
    },
    {
      tag: 'Balanced Demands',
      icon: 'balance',
      description: 'Medium Pirelli ratings across all categories. True all-rounder circuit.',
    },
    {
      tag: 'Historic Significance',
      icon: 'trophy',
      description: '1994 transformed F1 safety. Senna and Ratzenberger memorials remain.',
    },
  ],

  fuelEffectPerKg: 0.031,
}
