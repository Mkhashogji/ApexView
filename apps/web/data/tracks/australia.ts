import type { TrackIntelligence } from './types'

/**
 * Australian Grand Prix - Albert Park Grand Prix Circuit
 * Round 1 of the 2025 FIA Formula 1 World Championship
 *
 * Albert Park is a unique semi-permanent street circuit set around the
 * picturesque Albert Park Lake, just 3 kilometers south of Melbourne's city
 * center. The track underwent significant modifications in 2021-2022, including
 * resurfacing, removing the T9-T10 chicane (reducing corners from 16 to 14),
 * and widening several corners to promote overtaking.
 *
 * The circuit is one of the few on the calendar with four DRS zones, providing
 * excellent overtaking opportunities throughout the lap. Teams run medium to
 * medium-high downforce configurations, balancing corner speed against the need
 * to exploit DRS effectiveness on the four straights.
 *
 * Pirelli brings the softest compounds (C3-C5) to Albert Park, indicating the
 * low-to-moderate forces required on tyres during a lap. The circuit features
 * medium-low grip and abrasion, with cornering performance more critical than
 * braking and traction. Track evolution is significant as the street circuit
 * rubbers in through the weekend.
 *
 * The 2025 edition was the season opener, returning to its traditional slot
 * for the first time since 2019. Lando Norris claimed pole position with a new
 * track record (1:15.096) and won a chaotic wet-dry race ahead of Max Verstappen
 * and George Russell. Rookie Andrea Kimi Antonelli impressed with P4 from P16.
 */
export const australiaTrackIntelligence: TrackIntelligence = {
  circuitId: 'albert_park',
  round: 1,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Albert Park Grand Prix Circuit',
    country: 'Australia',
    location: 'Melbourne, Victoria, Australia',
    grandPrixName: 'Australian Grand Prix',
    circuitType: 'Semi-Permanent',
    firstGrandPrix: 1996,
    description:
      "Albert Park is a unique semi-permanent street circuit set around the picturesque Albert Park Lake, just 3 kilometers south of Melbourne's city center. The circuit underwent significant modifications in 2021-2022, including resurfacing, removing the T9-T10 chicane (reducing corners from 16 to 14), and widening several corners to promote overtaking. The circuit is one of the few on the calendar with four DRS zones, providing excellent overtaking opportunities throughout the lap. Teams run medium to medium-high downforce configurations, balancing corner speed against the need to exploit DRS effectiveness on the four straights. The fast-flowing T8-T10 section is a standout, with the T9-T10 left-right taken at roughly 310-330 km/h with peak lateral loads of around 5g through the direction change. Pirelli brings the softest compounds (C3-C5), indicating the low-to-moderate forces on tyres. Track evolution is significant as the street circuit rubbers in through the weekend. Charles Leclerc holds the race lap record (1:19.813, 2024), while Lando Norris set the all-time track record in 2025 qualifying (1:15.096). The Melbourne event has hosted the season opener numerous times, with its vibrant atmosphere and lakeside setting making it one of F1's most beloved venues.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.278,
      miles: 3.280,
    },
    raceDistance: {
      km: 306.124,
      miles: 190.226,
    },
    numberOfLaps: 58,
    numberOfCorners: 14,
    drsZones: 4,
    lapRecord: {
      time: '1:19.813',
      driver: 'Charles Leclerc',
      year: 2024,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '25.5 psi',
        rear: '22.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED & CORRECTED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 2,          // Low - smooth power application; not critical
    asphaltGrip: 2,       // Low - street circuit surface; medium-low grip
    asphaltAbrasion: 2,   // Low - smooth surface; low abrasion enables soft compounds
    trackEvolution: 3,    // Medium - significant evolution as rubber builds on street surface
    tyreStress: 3,        // Medium - moderate stress despite soft compounds
    braking: 2,           // Low - cornering more critical than braking
    lateral: 3,           // Medium - moderate lateral loads; T8-T10 most demanding
    downforce: 3,         // Medium - medium to medium-high downforce required
  },

  energyProfile: {
    longitudinal: 'Low', // Limited heavy braking zones; good traction requirements
    lateral: 'Medium',   // Fast-flowing sections with moderate cornering loads
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
        "Sector 1 is a slower, technical section featuring the T1-T2 chicane and T3-T4 right-hand sequence. The lap begins with heavy braking from the main straight into the T1 left-right chicane—a prime overtaking zone after DRS Zone 3 (main straight). DRS Zone 4 then activates after Turn 2, providing a follow-up opportunity into the heavy braking at Turn 3. Agility and a responsive front end are essential for the quick direction changes through this section.",
      keyFeatures: [
        'T1-T2 Chicane: heavy braking zone; primary overtaking opportunity after DRS Zone 3',
        'DRS Zone 4 activates after T2, enabling follow-up attacks into T3',
        'Quick direction changes require agility and responsive front end',
        'T3-T4 right-hand sequence rewards car balance and stability',
        'DRS detection for Zones 3 & 4 occurs before T13 in Sector 3',
      ],
      criticalCorners: [
        'T1 - Heavy braking from main straight; primary overtaking zone (end of DRS Zone 3)',
        'T3 - Heavy braking; secondary overtaking opportunity (end of DRS Zone 4)',
        'T5 - Exit sets up the run to T6 and the crucial DRS detection point',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T6-T10',
      description:
        "Sector 2 is the fastest sector, predominantly full-throttle through the flowing lakeside section. The DRS detection point for Zones 1 & 2 is located 40m after Turn 6—getting within 1 second here enables DRS activation at both T8 and T10. The T8-T10 complex is the standout feature—a flat-out run into the high-speed T9-T10 left-right, taken at roughly 310-330 km/h with peak lateral loads of around 5g through the direction change. DRS Zone 1 activates after T8, and Zone 2 after T10, creating sustained pressure opportunities.",
      keyFeatures: [
        'DRS detection point (Zones 1 & 2): 40m after Turn 6—critical timing reference',
        'DRS Zone 1: activates on Lakeside Drive straight between T8-T9',
        'DRS Zone 2: activates 100m after T10; runs to T11 braking',
        'T8–T10: flat-out run into the high-speed T9–T10 left–right, taken at roughly 310–330 km/h with peak lateral loads of around 5 g through the T9–T10 change of direction.',
        'Being within 1s at T6 detection enables DRS for both Zone 1 and Zone 2',
      ],
      criticalCorners: [
        'T6 - Exit speed + positioning determines DRS eligibility for Zones 1 & 2',
        'T9 - Fast left-hander; DRS Zone 1 ends at braking zone',
        'T10 - Quick right; DRS Zone 2 activates after exit',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T11-T14',
      description:
        "Sector 3 is a slower technical section containing the critical DRS detection point for Zones 3 & 4 (90m before Turn 13). T11 presents a heavy braking opportunity where DRS Zone 2 ends—a key overtaking spot. Turn 14 exit speed is absolutely crucial—it defines advantage down the main straight where DRS Zone 3 activates, feeding into the primary overtaking zone at Turn 1.",
      keyFeatures: [
        'T11: heavy braking zone; end of DRS Zone 2; secondary overtaking spot',
        'DRS detection point (Zones 3 & 4): 90m before Turn 13—must be within 1s here',
        'T13: chicane entry requiring precision and braking stability',
        'T14: exit speed defines main straight advantage—DRS Zone 3 activates 30m after',
        'Being within 1s at T13 detection enables DRS for both Zone 3 (main straight) and Zone 4 (T2-T3)',
      ],
      criticalCorners: [
        'T11 - Heavy braking; end of DRS Zone 2; key overtaking opportunity',
        'T13 - DRS detection point 90m before; must be within 1s for Zones 3 & 4',
        'T14 - Exit speed defines DRS Zone 3 effectiveness; most critical corner',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones 
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '40m after Turn 6',
      activationPoint: 'Lakeside Drive straight between Turns 8 and 9',
      deactivationPoint: 'Turn 9 braking zone',
      description:
        "DRS Zone 1 runs along the Lakeside Drive straight between Turn 8 and Turn 9. Detection occurs 40m after Turn 6—the same detection point also serves Zone 2. This unique configuration means getting within 1 second at Turn 6 exit enables DRS for both Zone 1 and Zone 2 consecutively, creating sustained pressure through the Lakeside section.",
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: '40m after Turn 6 (shared with Zone 1)',
      activationPoint: '100m after Turn 10',
      deactivationPoint: 'Turn 11 braking zone',
      description:
        "DRS Zone 2 runs from Turn 10 to Turn 11, the second part of the Lakeside straight section. It shares the same detection point as Zone 1 (40m after Turn 6), so a driver within 1 second at that point gets DRS for both zones. This creates a prime overtaking opportunity into the heavy braking zone at Turn 11.",
      effectiveness: 'High',
    },
    {
      zone: 3,
      detectionPoint: '90m before Turn 13',
      activationPoint: '30m after Turn 14 (main straight)',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        "DRS Zone 3 is the longest and most important zone—the main straight from Turn 14 (final corner) to Turn 1. Detection occurs 90m before Turn 13, which also serves Zone 4. This is the primary overtaking zone on the circuit, with heavy braking into the Turn 1 chicane providing the best passing opportunity of the lap.",
      effectiveness: 'Very High',
    },
    {
      zone: 4,
      detectionPoint: '90m before Turn 13 (shared with Zone 3)',
      activationPoint: '30m after Turn 2',
      deactivationPoint: 'Turn 3 braking zone',
      description:
        "DRS Zone 4 runs from Turn 2 to Turn 3, providing a follow-up opportunity after the Turn 1 chicane. It shares the same detection point as Zone 3 (90m before Turn 13), so a successful Turn 1 defense can still be challenged into Turn 3. This second chance at the start of the lap makes Albert Park's opening sequence highly action-packed.",
      effectiveness: 'High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium',
      explanation:
        "Albert Park suits medium to medium-high levels of wing loads, with both approaches viable. Higher downforce gains in tyre wear, cornering, braking, and traction, but sacrifices straight-line speed. Lower downforce improves performance over the four main straights—the difference is modest with DRS available (qualifying, attacking) but very significant when defending or in clear air. Teams adjust wing levels through sessions as weather forecasts evolve. Based on observed 2025 weekend configurations: Ferrari ran the most loaded wing (same as Bahrain tests), Red Bull took a similar approach, while McLaren and Mercedes went one step lower in downforce. Among midfielders, Alpine ran the least loaded wing, while Williams/Haas/Aston chose similar medium configurations. McLaren's performance advantage appeared more whole-lap than straight-line led; any wing trade-off still had to work across the four DRS zones and the high-speed lakeside section.",
    },
    tyreManagement: {
      compounds: ['C3 (Hard)', 'C4 (Medium)', 'C5 (Soft)'],
      allocation: 'Softest compounds—low-to-moderate forces required on tyres',
      primaryWearMechanism: 'Front-limited circuit with moderate overall degradation. The low-to-moderate forces on tyres allow softest compounds. Medium-low grip and abrasion enable extended stint lengths. Cornering performance is more critical than braking and traction for lap time.',
      explanation:
        "Albert Park's tyre characteristics are defined by the low-to-moderate forces required during a lap, allowing Pirelli to bring the softest compounds (C3-C5). The circuit features medium-low grip and abrasion, enabling these soft tyres to sustain several laps effectively. Cornering performance is more critical than braking and traction—teams prioritize lateral grip over longitudinal stability. Track evolution is significant on this street circuit as rubber builds through the weekend. In 2024, 80% of race laps were completed on the Hard compound (C3), with two-stop strategies most common. The C4 and C5 have been modified for 2025 to reduce graining, potentially expanding strategic options. Front tyre temperature management is important given the front-limited nature of the circuit.",
      strategicNote: 'Two-stop optimal in dry conditions: Soft → Medium → Hard or Medium → Hard → Medium. Hard compound (C3) capable of 22+ lap stints. 2025 race affected by rain—strategy shifted to multiple compound changes including Intermediates. Safety Car risk elevated due to narrow escape roads, wall proximity, and variable weather.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium-Low (2/5) - Street circuit surface with low grip',
      impact: "Albert Park's surface was renewed in 2022 and is relatively smooth with medium-low abrasion. As a semi-permanent street circuit, the track is 'green' at the start of the weekend—dirty with low grip. It evolves rapidly as F1 cars and support series lay down rubber, making early practice sessions less representative. This evolution makes it difficult for engineers to distinguish between setup improvements and natural track improvement. Some bumps remain despite resurfacing, requiring careful negotiation. The circuit demands a well-sorted chassis with a reactive front end to handle the quick direction changes. Weather can significantly impact track evolution—rain washes away rubber buildup, potentially resetting grip levels.",
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone:
      'T1 (Chicane) - Main passing spot after DRS Zone 3 (main straight); heavy braking from 320+ km/h',
    secondaryZones: [
      'T3 - End of DRS Zone 4; follow-up opportunity after T1 chicane',
      'T11 - End of DRS Zone 2; heavy braking after fast T8-T10 section',
    ],
    factors: [
      'Four DRS zones with only TWO detection points—unique configuration on the calendar',
      'Detection at T6 exit enables both Zone 1 (T8-T9) and Zone 2 (T10-T11) consecutively',
      'Detection before T13 enables both Zone 3 (main straight) and Zone 4 (T2-T3) consecutively',
      'Main straight (DRS Zone 3) creates strongest closing speed into T1—primary overtaking zone',
      'DRS Zone 4 provides follow-up chance into T3 if T1 move fails',
      'T11 heavy braking zone (end of DRS Zone 2) offers secondary opportunity',
      'Getting within 1s at either detection point grants two consecutive DRS activations',
      '2025 race: Antonelli recovered from P16 to P4, demonstrating overtaking potential',
    ],
    recommendation:
      "Prioritize attacks into T1 by ensuring you're within 1 second at the T13 detection point (90m before T13). This grants DRS for both Zone 3 (main straight) and Zone 4 (T2-T3), providing two consecutive chances to pass. If T1 fails, immediately prepare for T3. For Lakeside battles, focus on being within 1s at the T6 exit detection—this enables both Zone 1 and Zone 2, creating pressure into T9 and T11. The dual-detection system means a failed attempt doesn't end the battle; maintain proximity to trigger the next detection point.",
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Variable autumn weather; mild temperatures with significant day-to-day swings',
      airTemperature: {
        max: '~35°C',
        min: '~15°C',
        raceTime: 'Typically mid-20s°C',
      },
      rainProbability: 'Moderate to high—autumn transition highly unpredictable',
      wind: 'Variable—gusts possible; affects high-speed lakeside sections',
      humidity: 'Moderate',
    },
    sessionConditions: {
      fp1: 'Typically sunny; track green with low grip',
      fp2: 'Track improving; long run data collection',
      fp3: 'Variable; final setup confirmation',
      qualifying: 'Variable conditions possible',
      race: 'Highly variable; 2025 saw wet-dry conditions with multiple Safety Cars',
    },
    impact:
      "Melbourne's position in autumn (March) creates highly variable weather conditions. Temperature swings between days are common, requiring teams to adapt setups continuously. Rain has featured prominently in recent Australian GPs, with the 2023 race holding the record for most red flags (3) in a GP. The 2025 race saw mixed wet-dry conditions, shifting strategy from dry two-stop to wet/dry combinations. Wind can significantly affect car behavior through the exposed T8-T10 complex and main straight. As a street circuit, track evolution is heavily weather-dependent—rain washes away rubber buildup and resets grip levels.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:19.813',
      driver: 'Charles Leclerc',
      year: 2024,
    },
    polePositions: [
      {
        year: 2022,
        time: '1:17.868',
        driver: 'LEC',
        note: 'First pole on faster new layout; Leclerc dominant Grand Slam weekend',
      },
      {
        year: 2023,
        time: '1:16.732',
        driver: 'VER',
        note: "Verstappen's first Australian pole; Mercedes surprise front row (Russell P2)",
      },
      {
        year: 2024,
        time: '1:15.915',
        driver: 'VER',
        note: 'Previous track record; beat Sainz (returning from surgery) by 0.27s',
      },
      {
        year: 2025,
        time: '1:15.096',
        driver: 'NOR',
        note: 'NEW ALL-TIME TRACK RECORD; McLaren 1-2 lockout',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:15.096' },
        { position: 2, driver: 'PIA', time: '1:15.180' },
        { position: 3, driver: 'VER', time: '1:15.481' },
        { position: 4, driver: 'RUS', time: '1:15.546' },
        { position: 5, driver: 'TSU', time: '1:15.670' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '26.460s', driver: 'TSU' },
        { sector: 2, time: '17.315s', driver: 'DOO' },
        { sector: 3, time: '32.567s', driver: 'PIA' },
      ],
      overallIdealLap: '1:16.342',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '89.79s',
        gaps: [
          { driver: 'PIA', gap: '+0.43s' },
          { driver: 'VER', gap: '+0.63s' },
          { driver: 'RUS', gap: '+1.29s' },
          { driver: 'ANT', gap: '+1.73s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'SAI',
        meanLapTime: '81.46s',
        gaps: [
          { driver: 'LEC', gap: '+0.05s' },
          { driver: 'NOR', gap: '+0.11s' },
          { driver: 'PIA', gap: '+0.34s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Max Verstappen', speed: '334 km/h' },
        range: '326-334 km/h',
      },
      race: {
        withDRS: 'Up to 333 km/h (LEC with DRS)',
        withoutDRS: '~307-314 km/h (clean air)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop optimal in dry: Laps 15-20, 35-40',
      factors: [
        'Two-stop strategy most common in dry conditions (2024: 80% of laps on Hard)',
        'One-stop possible but risky due to moderate tyre degradation',
        'Soft compound viable for short opening stints (7-10 laps max)',
        'Medium compound: 15-20 lap stints typical',
        'Hard compound: 20-25+ lap stints comfortable',
        'Pit lane time loss: ~19-20 seconds',
        'McLaren fastest pit stops in 2025 (baseline); Ferrari +1.6s behind',
      ],
    },
    keyStrategicFactors: [
      'Four DRS zones make track position less critical than pure pace circuits',
      'Weather unpredictability requires flexible strategy approach',
      'Track evolution (3/5) means qualifying pace advantage moderate vs. race pace',
        'Safety Car probability high (~50%)—narrow escape roads, wall proximity',
      '2025 race: 3 Safety Car periods, 6 retirements (all accidents)',
      'Variable conditions in 2025 saw Inter-Slick-Inter strategy patterns',
      'Starting tyre choice less critical due to multiple compound viability',
    ],
    safetyCarLikelihood: 'High (~50%)—Narrow escape roads, wall proximity, weather variability. 2023 race saw 3 red flags (record); 2025 saw 3 Safety Car periods',
    historicalNotes: [
      '2025: Race officially completed after 57 laps (300.846 km)—extra formation lap required after Hadjar crashed at T2 during initial formation in wet conditions',
      '2025: Season opener returns to Melbourne for first time since 2019',
      '2025: Lando Norris wins with new track record pole (1:15.096); McLaren 1-2 in quali',
      '2025: Antonelli P4 from P16—impressive debut recovery drive',
      '2025: Wet-dry conditions; 6 retirements including multiple rookies',
      '2024: Sainz wins for Ferrari; Verstappen DNF with brake fire',
      '2023: Record 3 red flags; Verstappen wins chaotic race',
      '2022: Leclerc dominates; circuit returned after COVID absence',
      '1996: Inaugural Melbourne GP; Martin Brundle infamous T3 crash',
      '28 Australian GPs at Albert Park (1996-2019, 2022-2025); no Australian winner yet',
    ],
  },

  // =========================================================================
  // Defining Characteristics (60-80 chars max per description)
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Four DRS Zones',
      icon: 'zap',
      description: 'One of few circuits with four zones; excellent overtaking.',
    },
    {
      tag: 'Weather Lottery',
      icon: 'cloud-rain',
      description: 'Melbourne autumn highly unpredictable; rain transforms races.',
    },
    {
      tag: 'Track Evolution',
      icon: 'trending-up',
      description: 'Street circuit grip improves dramatically through weekend.',
    },
    {
      tag: 'Lakeside Speed',
      icon: 'wind',
      description: 'T8-T10 complex: ~310-330 km/h, 5g lateral—signature sequence.',
    },
    {
      tag: 'Soft Compound Venue',
      icon: 'circle',
      description: 'C3-C5 allocation; low forces allow softest Pirelli tyres.',
    },
    {
      tag: 'Season Opener Drama',
      icon: 'flag',
      description: 'First competitive test reveals true pecking order.',
    },
  ],
}

