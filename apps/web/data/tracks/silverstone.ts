import type { TrackIntelligence } from './types'

/**
 * British Grand Prix - Silverstone Circuit
 * Round 12 of the 2025 FIA Formula 1 World Championship
 * 
 * The spiritual home of Formula 1 and British motorsport. Built on a former
 * RAF bomber airfield, Silverstone hosted the first-ever F1 World Championship
 * race on May 13, 1950. The circuit is renowned for its high-speed corners,
 * particularly the legendary Maggotts-Becketts-Chapel complex, which demands
 * exceptional car control, aerodynamic efficiency, and driver commitment.
 */
export const silverstoneTrackIntelligence: TrackIntelligence = {
  circuitId: 'silverstone',
  round: 12,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Silverstone Circuit',
    country: 'Great Britain',
    location: 'Northamptonshire, England',
    grandPrixName: 'British Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1950,
    description:
      'The spiritual home of Formula 1 and British motorsport. Built on a former RAF bomber airfield, Silverstone hosted the first-ever F1 World Championship race on May 13, 1950. The circuit is renowned for its high-speed corners, particularly the legendary Maggotts-Becketts-Chapel complex, which demands exceptional car control, aerodynamic efficiency, and driver commitment. Despite numerous layout changes over the decades, Silverstone has maintained its essential character as one of the fastest and most challenging tracks on the calendar.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.891,
      miles: 3.661,
    },
    raceDistance: {
      km: 306.198,
      miles: 190.263,
    },
    numberOfLaps: 52,
    numberOfCorners: 18,
    drsZones: 2,
    lapRecord: {
      time: '1:27.097',
      driver: 'Max Verstappen',
      year: 2020,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-2.75°',
        rear: '-1.50°',
      },
      minStartingPressures: {
        front: '26.5 psi',
        rear: '23.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,          // Moderate - important for slow corners in Sector 1 and 3
    tyreStress: 5,        // MAXIMUM - extreme cornering forces through high-speed changes
    asphaltGrip: 4,       // High - good quality surface provides consistent grip
    asphaltAbrasion: 2,   // Low - smooth surface with minimal abrasion
    braking: 2,           // Low - limited heavy braking zones
    lateral: 5,           // MAXIMUM - sustained high-speed cornering through Copse and Maggotts-Becketts
    downforce: 3,         // Medium - balanced requirement between drag and stability
    trackEvolution: 2,    // Low - grip levels remain consistent throughout weekend
  },

  energyProfile: {
    longitudinal: 'Medium',   // Moderate braking demands
    lateral: 'Maximum',       // Extreme lateral loads through high-speed corners
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#E53935',  // Red
      corners: 'T1-T5',
      description:
        'Fast full-throttle entry corner at Abbey followed by a twisty technical section through Village and The Loop, then onto the Wellington Straight with DRS Zone 1. Sector timing line is 110m before T6. The sector demands transitioning from flat-out commitment at Abbey to precise technical driving through the slower corners.',
      keyFeatures: [
        'Abbey (T1): High-speed 280+ km/h entry, flat-out in qualifying',
        'Village (T3): Tight right-hander at 120 km/h, traction critical',
        'The Loop (T4): Hairpin-style corner, good overtaking opportunity',
        'Wellington Straight: DRS Zone 1 - primary overtaking opportunity',
        'Technical section tests car balance and driver precision',
      ],
      criticalCorners: [
        'T1 (Abbey) - 280+ km/h flat-out entry sets tone for lap',
        'T3-4 (Village/Loop) - Slowest section, traction on exit crucial',
        'T5 (Aintree) - Fast left-hander onto Wellington Straight',
      ],
    },
    {
      sector: 2,
      color: '#1E88E5',  // Blue
      corners: 'T6-T14',
      description:
        'The heart of Silverstone containing the legendary Maggotts-Becketts-Chapel complex — one of the most demanding and exhilarating sequences in all of motorsport. Sector timing line is 50m after T14. This sector separates competitive cars from the rest, requiring perfect balance between downforce for cornering grip and minimal drag for straight-line speed.',
      keyFeatures: [
        'Brooklands (T7): Heavy braking zone after Wellington Straight — end of DRS Zone 1',
        'Luffield (T8): Slow 95 km/h hairpin, sets up Copse approach',
        'Copse (T9): 290+ km/h flat-out — one of fastest corners on calendar',
        'Maggotts-Becketts-Chapel (T10-12): Rapid 260-280 km/h direction changes',
        'DRS Zone 2 detection at T11 (Becketts); Hangar Straight leads to Stowe',
        'Aerodynamic excellence is paramount — this sector defines competitiveness',
      ],
      criticalCorners: [
        'T9 (Copse) - 290+ km/h flat-out, demands full commitment',
        'T10-12 (Maggotts-Becketts-Chapel) - Ultimate test of car balance and driver bravery',
      ],
    },
    {
      sector: 3,
      color: '#FDD835',  // Yellow
      corners: 'T15-T18',
      description:
        'Vale chicane through to Club corner complex and the National Pit Straight. Stowe (T15) is the primary overtaking zone on the circuit. Maximizing braking stability into Stowe is crucial, with traction out of Club critical for lap time.',
      keyFeatures: [
        'Stowe (T15): PRIMARY overtaking zone with heavy braking — end of DRS Zone 2',
        'Vale (T16): Technical chicane section',
        'Club (T17-18): Final corner complex — traction critical for pit straight speed',
        'Speed trap located 140m before Turn 15',
        'Power advantage most visible through this sector',
      ],
      criticalCorners: [
        'T15 (Stowe) - Heavy braking, main overtaking zone on circuit',
        'T17-18 (Club) - Exit speed determines pit straight performance',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '25m before Turn 3 (Village)',
      activationPoint: '30m after Turn 5 (Wellington Straight)',
      deactivationPoint: 'Brooklands braking zone (T7)',
      description:
        'Overtaking opportunity on Wellington Straight. Detection is early (before Village), with activation after Aintree exit. Effective zone leading into the Brooklands heavy braking zone.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'Turn 11 (Becketts)',
      activationPoint: 'Turn 14 (Hangar Straight)',
      deactivationPoint: 'Stowe braking zone (T15)',
      description:
        'Primary DRS zone on Hangar Straight leading to Stowe — the circuit\'s main overtaking zone. Detection at Becketts, activation on the approach to Stowe. The combination of DRS and heavy braking creates excellent passing opportunities.',
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
        'Silverstone presents a fascinating aerodynamic challenge. While the high-speed corners demand significant downforce, the long straights (Wellington, Hangar, National Pit) reward low drag. Modern ground-effect cars produce substantial baseline downforce, allowing teams to run medium-load wings. In 2025, team approaches varied significantly: McLaren optimized for conditions with two rear wing options; Red Bull ran very low load (Verstappen\'s skinny rear wing secured pole but devastated wet race pace at 1.5s/lap deficit); Sauber\'s rain-focused high-downforce setup delivered Hulkenberg\'s historic podium.',
    },
    tyreManagement: {
      compounds: ['C2 (Hard)', 'C3 (Medium)', 'C4 (Soft)'],
      allocation: 'Standard allocation',
      primaryWearMechanism: 'Extreme lateral forces through sustained high-speed cornering — rear tyre stress particularly severe through Maggotts-Becketts complex',
      explanation:
        'Maximum 5/5 tyre stress rating makes Silverstone one of the most demanding circuits for compounds. Soft compound life is just 12-15 laps due to extreme cornering forces. High lateral loads generate significant thermal degradation despite low asphalt abrasion (2/5). 2025 race was rain-affected with multiple intermediate/slick transitions.',
      strategicNote: '2-stop preferred in dry conditions. Wet conditions highly variable with multiple tyre transitions possible.',
    },
    surfaceCharacteristics: {
      gripLevel: 'High - good quality surface provides consistent grip levels',
      impact: 'Low track evolution (2/5) means grip levels remain stable throughout the weekend with minimal rubber build-up. Smooth surface with low abrasion (2/5) somewhat offsets the extreme mechanical stress from lateral forces.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'Stowe (T15) - end of Hangar Straight with DRS Zone 2',
    secondaryZones: ['Brooklands (T7) - end of Wellington Straight with DRS Zone 1', 'The Loop (T4)'],
    factors: [
      'Two effective DRS zones create genuine overtaking opportunities',
      'Stowe is the primary passing zone with heavy braking from 300+ km/h',
      'Brooklands offers secondary opportunity after Wellington Straight',
      'The Loop (T4) provides rare slow-speed passing chance',
      'High-speed nature limits opportunities outside DRS zones',
      'Slipstream effective on long straights despite medium-load wings',
      '2025 race: Norris inherited lead after Piastri\'s 10s safety car penalty; Hulkenberg defended superbly from P19',
    ],
    recommendation:
      'Focus on DRS zones for passing opportunities. Stowe offers the best chance with heavy braking and wide entry. Track position through high-speed corners like Maggotts-Becketts is nearly impossible to attack. Undercut potential limited due to high-speed nature reducing pit stop time delta.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'British weather is notoriously unpredictable — rain is always possible regardless of forecast',
      airTemperature: {
        max: '25°C',
        min: '15°C',
        raceTime: '19°C',
      },
      rainProbability: 'High - mixed conditions should always be expected',
      wind: 'Variable, often westerly — can significantly affect car balance through high-speed corners',
      humidity: 'Variable (40-80%)',
    },
    sessionConditions: {
      fp1: '24-25°C, sunny then cloudy, dry',
      fp2: '24-25°C, dry conditions',
      fp3: '19-20°C, cloudy',
      qualifying: '19-20°C, cloudy then rainy afternoon',
      race: '19°C, unsettled with showers, westerly wind',
    },
    impact:
      'British weather creates strategic chaos. The 2025 race saw 6 drivers gamble on slicks at formation lap end (disastrous for those on hards), everyone pitting for fresh intermediates as rain intensified, then a dramatic slick window that varied by 7 laps between drivers. Verstappen\'s low-drag qualifying setup that secured pole cost him approximately 1.5s/lap in wet race conditions. Teams must always prepare intermediate and wet strategies regardless of forecast.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:27.097',
      driver: 'Max Verstappen',
      year: 2020,
    },
    polePositions: [
      {
        year: 2024,
        time: '1:25.819',
        driver: 'RUS',
        note: 'First all-British 1-2-3 in qualifying since 1968',
      },
      {
        year: 2025,
        time: '1:24.892',
        driver: 'VER',
        note: '0.927s faster than 2024 pole — top 6 within 0.229s',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:24.892' },
        { position: 2, driver: 'PIA', time: '1:24.995' },
        { position: 3, driver: 'NOR', time: '1:25.010' },
        { position: 4, driver: 'RUS', time: '1:25.029' },
        { position: 5, driver: 'HAM', time: '1:25.095' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '27.810s', driver: 'NOR' },
        { sector: 2, time: '34.396s', driver: 'LEC' },
        { sector: 3, time: '23.570s', driver: 'NOR' },
      ],
      overallIdealLap: '1:25.776',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '1:39.08',
        gaps: [
          { driver: 'PIA', gap: '+0.17s' },
          { driver: 'HUL', gap: '+1.10s' },
          { driver: 'HAM', gap: '+1.10s' },
          { driver: 'RUS', gap: '+1.17s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'HAM',
        meanLapTime: '1:33.84',
        gaps: [
          { driver: 'PIA', gap: '+0.11s' },
          { driver: 'VER', gap: '+0.14s' },
          { driver: 'NOR', gap: '+0.20s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Tsunoda', speed: '328 km/h' },
        range: '319-328 km/h',
      },
      race: {
        withDRS: 'Up to 346 km/h (Bearman)',
        withoutDRS: 'Below 310 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: '2-stop in dry conditions (Laps 14-18 first stop, 32-38 second stop)',
      factors: [
        'Soft compound life: 12-15 laps due to 5/5 tyre stress',
        'Medium provides best balance: 22-28 laps',
        'Hard can complete final stint but may lack pace',
        '2025 race: chaotic rain-affected with multiple transitions',
        '6 drivers gambled on slicks at formation lap end — hards lost multiple seconds per lap',
        'Slick window varied by 7 laps: Alonso first (15 laps to go), Norris last (8 laps to go)',
        'Undercut potential limited due to high-speed nature',
      ],
    },
    keyStrategicFactors: [
      'British weather unpredictability — always have wet contingency',
      'Setup compromise crucial — qualifying optimization can devastate race pace',
      'Maggotts-Becketts performance is key differentiator',
      'Verstappen\'s skinny rear wing: pole position but 1.5s/lap slower in wet',
      'Sauber transformation: slowest team 2024 to podium finisher 2025',
      'Pit stop performance varied: Racing Bulls/Alpine fastest, Williams/McLaren/Sauber slower',
    ],
    safetyCarLikelihood: 'Moderate - high-speed corners can catch drivers out, especially in changing conditions',
    historicalNotes: [
      '2025: Norris wins — first McLaren British GP win since Hamilton 2008',
      '2025: Hulkenberg ends 239-race podium drought — longest wait for podium in F1 history',
      '2025: Sauber first podium since Kobayashi P3 at 2012 Japanese GP',
      '2024: Hamilton wins record 9th British GP — first victory since 2021 (945-day gap)',
      '2022: Sainz maiden F1 victory',
      '2021: Hamilton-Verstappen collision at Copse sparks controversy',
      '2020: Hamilton wins on three wheels after dramatic late puncture',
      '1950: First-ever F1 World Championship race — attended by King George VI',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'High-Speed Cathedral',
      icon: 'speed',
      description: 'Legendary corners like Copse and Maggotts-Becketts demand absolute commitment.',
    },
    {
      tag: 'Aero Battlefield',
      icon: 'aero',
      description: 'Maggotts-Becketts-Chapel is the ultimate test of aerodynamic excellence.',
    },
    {
      tag: 'British Weather Roulette',
      icon: 'weather',
      description: 'Unpredictable conditions create strategic chaos — setup choices can backfire.',
    },
    {
      tag: 'Tyre Torture Test',
      icon: 'tyre',
      description: 'Maximum 5/5 tyre stress — extreme lateral forces push compounds to their limits.',
    },
    {
      tag: 'Motorsport Heritage',
      icon: 'trophy',
      description: '75 years of history — hosted the first-ever F1 World Championship race in 1950.',
    },
  ],

  fuelEffectPerKg: 0.028,
}
