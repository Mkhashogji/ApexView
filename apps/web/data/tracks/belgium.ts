import type { TrackIntelligence } from './types'

/**
 * Belgian Grand Prix - Circuit de Spa-Francorchamps
 * Round 13 of the 2025 FIA Formula 1 World Championship
 * 
 * The legendary "Ardennes Rollercoaster" is F1's longest circuit at 7.004 km,
 * featuring the iconic Eau Rouge/Raidillon complex, extreme elevation changes
 * (~100m), and notoriously unpredictable weather. One of seven circuits from
 * the inaugural 1950 championship, Spa presents F1's ultimate aero compromise
 * with long straights demanding low drag while Sector 2's high-speed corners
 * require maximum downforce for both pace and tyre preservation.
 */
export const belgiumTrackIntelligence: TrackIntelligence = {
  circuitId: 'spa-francorchamps',
  round: 13,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit de Spa-Francorchamps',
    country: 'Belgium',
    location: 'Stavelot, Liège, Belgium',
    grandPrixName: 'Belgian Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1950,
    description:
      'The legendary "Ardennes Rollercoaster" is F1\'s longest circuit at 7.004 km, featuring the iconic Eau Rouge/Raidillon complex and extreme elevation changes of approximately 100 metres. One of seven circuits from the inaugural 1950 championship, Spa presents F1\'s ultimate aero compromise — long straights demand low drag while Sector 2\'s high-speed corners require maximum downforce for both lap time and tyre preservation. Spa has a long history of rain-affected Belgian GPs, and it\'s common to see mixed conditions across the lap. The 2021 race became F1\'s shortest ever when only 3 laps were completed behind the Safety Car.',
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 7.004,
      miles: 4.352,
    },
    raceDistance: {
      km: 308.052,
      miles: 191.415,
    },
    numberOfLaps: 44,
    numberOfCorners: 19,
    drsZones: 2,
    lapRecord: {
      time: '1:44.701',
      driver: 'Sergio Pérez',
      year: 2024,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-2.75°',
        rear: '-1.50°',
      },
      minStartingPressures: {
        front: '26.5 psi',
        rear: '24.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings)
  // =========================================================================
  circuitCharacteristics: {
    traction: 4,          // High - elevation changes and varied corner speeds require strong rear grip
    tyreStress: 4,        // High - demanding corners concentrated in Sector 2
    asphaltGrip: 3,       // Moderate - reasonable grip, weather can alter dramatically
    asphaltAbrasion: 3,   // Moderate - Ardennes surface reasonably kind to tyres
    braking: 4,           // High - heavy braking into La Source and Bus Stop from 320+ km/h
    lateral: 5,           // MAXIMUM - Sector 2's Pouhon/Fagnes create extreme lateral loads
    downforce: 2,         // Low - long straights demand low-drag configurations
    trackEvolution: 3,    // Moderate - circuit length distributes rubber more thinly
  },

  energyProfile: {
    longitudinal: 'High',    // Heavy braking zones and long straights
    lateral: 'Maximum',      // Sector 2's continuous high-speed corners
  },

  // =========================================================================
  // Sector Breakdown
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000',  // Red
      corners: 'T1-T5',
      description:
        'The iconic opening sector containing La Source hairpin and the legendary Eau Rouge/Raidillon complex. DRS Zone 2 on pit straight creates the primary overtaking opportunity into La Source with heavy braking from 320+ km/h to 70 km/h. Eau Rouge/Raidillon is taken flat in qualifying with fresh tyres — any marginal lift loses significant time. DRS Zone 1 activates on the Kemmel Straight after Raidillon, enabling passes into Les Combes.',
      keyFeatures: [
        'DRS Zone 2 on pit straight approaching La Source',
        'La Source hairpin: 320+ km/h to 70 km/h braking zone',
        'Iconic Eau Rouge/Raidillon taken flat in qualifying',
        'DRS Zone 1 on Kemmel Straight (after Raidillon)',
        'Les Combes chicane: secondary overtaking zone after Kemmel DRS',
        'Low-drag setups excel — Haas, Red Bull gained time here in 2025',
      ],
      criticalCorners: [
        'T1 (La Source) - Hairpin, heavy braking zone, primary passing opportunity (end of DRS Zone 2)',
        'T2-4 (Eau Rouge/Raidillon) - Flat at 290-300 km/h, ultimate test of commitment',
        'T5 (Les Combes) - Chicane after Kemmel Straight DRS Zone 1, secondary passing zone',
      ],
    },
    {
      sector: 2,
      color: '#0000FF',  // Blue
      corners: 'T6-T13',
      description:
        'The "Technical Rollercoaster" featuring sustained high-speed corners that create maximum lateral loads on tyres. This sector is the limiting factor for tyre wear — cars with higher downforce dominate here but pay the price on straights. McLaren\'s high-downforce philosophy dominated this sector in 2025, with Piastri nearly 0.5 seconds faster than the next best car.',
      keyFeatures: [
        'Maximum lateral g-force demands on the calendar',
        'Double Gauche du Pouhon (T10-11): 250 km/h double apex',
        'Fagnes/Piff Paff (T12-13): Quick 200 km/h direction changes',
        'Downforce gains significant time AND preserves tyres',
        'Less loaded aero setup = faster qualifying but higher tyre wear',
        'McLaren utterly dominant — Piastri 0.3-0.5s quicker than any rival in 2025',
      ],
      criticalCorners: [
        'T9 (Speaker\'s Corner) - Fast right at 210 km/h, sets up Pouhon entry',
        'T10-11 (Pouhon) - 250 km/h double apex, tests sustained lateral grip',
        'T12-13 (Fagnes/Piff Paff) - 200 km/h sequence, punishes setup imbalance',
      ],
    },
    {
      sector: 3,
      color: '#FFFF00',  // Yellow
      corners: 'T14-T19',
      description:
        'The "Power Run" sector featuring a very long full-throttle section after Curve Paul Frère — car drag and ERS effectiveness are crucial differentiators. Blanchimont is flat in qualifying, and the tight Bus Stop chicane requires precision for clean pit straight entry. DRS Zone 2 detection is before Bus Stop, with activation on the pit straight after the chicane.',
      keyFeatures: [
        'Campus/Stavelot (T14): 160 km/h slow right',
        'Curve Paul Frère (T15): 240 km/h fast sweeper',
        'Blanchimont (T16): 300 km/h flat in qualifying',
        'Long uphill straight — ERS deployment critical',
        'Bus Stop chicane: 320+ km/h to 75 km/h tight chicane',
        'DRS Zone 2 detection before Bus Stop; activates on pit straight after T19',
      ],
      criticalCorners: [
        'T15 (Curve Paul Frère) - Exit speed crucial for long uphill straight',
        'T16 (Blanchimont) - 300 km/h flat, requires commitment',
        'T18-19 (Bus Stop) - Tight chicane, precision for clean S/F line crossing',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Before Eau Rouge (T2)',
      activationPoint: 'After Raidillon (T4) — Kemmel Straight',
      deactivationPoint: 'Les Combes braking zone (T5)',
      description:
        'DRS zone on the Kemmel Straight after Eau Rouge/Raidillon. Detection before Eau Rouge means drivers must be within 1 second before the iconic uphill complex. Highly effective due to the long straight and slipstream effect — Piastri passed Norris here on Lap 5 of the 2025 race.',
      effectiveness: 'High',
    },
    {
      zone: 2,
      detectionPoint: 'Before Bus Stop (T18)',
      activationPoint: 'After Bus Stop (T19) — Pit straight',
      deactivationPoint: 'La Source braking zone (T1)',
      description:
        'DRS zone on the pit straight after the Bus Stop chicane. The primary overtaking opportunity with heavy braking from 320+ km/h into La Source hairpin. Medium effectiveness due to medium-low drag configurations reducing DRS benefit somewhat.',
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
        'Spa presents F1\'s ultimate aero compromise. Long straights (Kemmel, Sector 3 uphill) demand low-drag configurations, while Sector 2\'s high-speed corners punish insufficient downforce. In 2025, significant team divergence was observed: Red Bull and Haas ran very low drag; Aston Martin debuted their first proper low-drag V-shape wing; McLaren and Ferrari opted for medium-high drag. The 9 km/h top speed spread between Tsunoda (346 km/h) and Norris (337 km/h) in Sprint Qualifying showed the setup variance. Crucially, McLaren\'s "draggy" setup dominated overall lap time through sheer Sector 2 dominance.',
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C3 (Medium)', 'C4 (Soft)'],
      allocation: '2-step gap between Hard and Medium compounds',
      primaryWearMechanism: 'Lateral grip through Sector 2\'s sustained high-speed corners — rear tyre stress highest through Pouhon and Fagnes',
      explanation:
        'Lateral forces are the limiting factor for tyre wear at Spa. The demanding corners are concentrated in Sector 2 rather than distributed throughout the lap. Cool Ardennes temperatures (19-21°C) help tyre longevity. The 2025 race featured an 80-minute rain delay — all cars started on intermediates, switching to slicks by Lap 12-13 as the track dried. Norris opted for Hard tyres vs. the field\'s Mediums, which provided more consistent performance throughout the stint.',
      strategicNote: 'One-stop typical in dry conditions. Pirelli mandates very high starting pressures (26.5 psi front, 24.5 psi rear) — over 1.8 bar at the front.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Moderate grip with potential for dramatic weather-induced changes',
      impact: 'The Ardennes circuit surface is reasonably kind to tyres. However, unpredictable weather can alter grip levels mid-session. Track evolution is moderate (3/5) due to the circuit\'s 7km length distributing rubber more thinly across the surface than shorter circuits.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone: 'La Source hairpin (T1) - end of main straight',
    secondaryZones: ['Les Combes (T5) - end of Kemmel Straight', 'Bus Stop chicane (T18-19)'],
    factors: [
      'Long straights create genuine overtaking opportunities',
      'Medium-low drag wings reduce DRS effectiveness somewhat',
      'La Source offers heavy braking from 320+ km/h — primary passing zone',
      'Kemmel Straight allows slipstream into Les Combes',
      'Track position less critical than at Hungary/Singapore due to passing options',
      'Weather can create significant tyre delta opportunities',
      'Piastri overtook Norris on Lap 5 using slipstream into Les Combes (2025)',
      'Verstappen passed Piastri into Les Combes on Lap 1 of Sprint using slipstream',
    ],
    recommendation:
      'While qualifying remains important, Spa offers more overtaking opportunities than most circuits. Long straights and DRS zones create passing possibilities, especially with tyre delta. The undercut is effective (~19s pit loss), and fresh rubber gains significant time through Sector 2. Weather variability can completely reshuffle positions.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Maritime influenced — Ardennes microclimate creates notoriously unpredictable weather',
      airTemperature: {
        max: '22°C',
        min: '12°C',
        raceTime: '21°C',
      },
      rainProbability: 'High (Ardennes microclimate frequently brings rain)',
      wind: 'Light northwesterly',
      humidity: 'High — frequently misty',
    },
    sessionConditions: {
      fp1: '19°C, wet start with high chance of light rain/drizzle',
      sprintQuali: '20°C, brighter conditions',
      sprint: '19°C, partly cloudy, slight shower chance',
      qualifying: '20°C, partly cloudy',
      race: '21°C, heavy rain pre-race caused 80-minute delay, dried throughout race',
    },
    impact:
      'Spa is infamous for unpredictable weather — rain can fall on one part of the circuit while another remains dry. The 2021 race was red-flagged after only 2 laps due to persistent rain (shortest F1 race in history). In 2025, heavy pre-race rain caused an 80-minute delay; all cars started on intermediates with a rolling start on Lap 5, switching to slicks by Lap 12-13. Teams must decide pre-parc fermé whether to optimize for wet or dry — Red Bull\'s high-downforce rain setup backfired when the race was delayed until the track dried.',
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:44.701',
      driver: 'Sergio Pérez',
      year: 2024,
    },
    polePositions: [
      {
        year: 2020,
        time: '1:41.252',
        driver: 'HAM',
        note: 'Previous unofficial all-time lap record',
      },
      {
        year: 2025,
        time: '1:40.510',
        driver: 'PIA',
        session: 'Sprint Qualifying',
        note: 'New unofficial all-time lap record — 0.477s ahead of P2',
      },
      {
        year: 2025,
        time: '1:40.562',
        driver: 'NOR',
        note: 'Pole position',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:40.562' },
        { position: 2, driver: 'PIA', time: '1:40.647' },
        { position: 3, driver: 'LEC', time: '1:40.900' },
        { position: 4, driver: 'VER', time: '1:40.903' },
        { position: 5, driver: 'ALB', time: '1:41.201' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Sprint Qualifying; sector leaders correct, split times are approximate (official sector splits not sourced)',
      sectors: [
        { sector: 1, time: '~26.5s (est.)', driver: 'OCO' },
        { sector: 2, time: '~43.2s (est.)', driver: 'PIA' },
        { sector: 3, time: '~30.8s (est.)', driver: 'PIA' },
      ],
      overallIdealLap: '1:40.510 (Sprint Qualifying P1)',
    },    
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '1:46.41',
        gaps: [
          { driver: 'PIA', gap: '+0.33s' },
          { driver: 'LEC', gap: '+0.45s' },
          { driver: 'VER', gap: '+0.47s' },
          { driver: 'RUS', gap: '+0.88s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'HAM',
        meanLapTime: '1:48.2s',
        gaps: [
          { driver: 'PIA', gap: '+0.03s' },
          { driver: 'VER', gap: '+0.17s' },
          { driver: 'LEC', gap: '+0.27s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Ocon', speed: '345 km/h' },
        range: '337-346 km/h',
      },
      race: {
        withDRS: 'Up to 356 km/h (Antonelli)',
        withoutDRS: '322-326 km/h',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop (weather permitting). 2025 race: Inters to Slicks on Lap 12-13',
      factors: [
        'Pit lane time loss approximately 19 seconds',
        '2025 race delayed 80 minutes for rain — started on intermediates',
        'Transition to slicks occurred Laps 12-13 as track dried',
        'Norris chose Hard compound vs. field\'s Mediums — provided better consistency',
        'Ferrari\'s dry-focused setup hurt on intermediates but excelled on slicks',
        'Red Bull\'s rain-optimized setup backfired when race was delayed',
        'ERS management crucial for long uphill sections without DRS',
      ],
    },
    keyStrategicFactors: [
      'Weather unpredictability paramount — can rain on one sector while dry on another',
      'Track position less critical than other circuits due to overtaking opportunities',
      'Hamilton\'s early slick switch from pit lane (Lap 11) forced leaders to respond',
      'Safety Car likelihood high — Spa\'s 7km length means SC bunches field significantly',
      'Pre-parc fermé setup gamble: wet or dry focus can define the race',
      'Pit lane loss (~19s) is moderate — undercut can be effective with fresh rubber',
    ],
    safetyCarLikelihood: 'High — weather-induced Safety Cars common, circuit length creates significant bunching',
    historicalNotes: [
      '2025: Piastri wins — first McLaren Belgian GP victory since Button 2012',
      '2025: Hamilton Q1 exit (lap deleted) — first in Ferrari career',
      '2025: Verstappen Sprint win — 12th career Sprint victory',
      '2024: Russell crossed line P1 but DSQ for underweight car — Hamilton inherited victory',
      '2022: Verstappen P14 to P1 — second-lowest position race has been won from',
      '2021: Shortest F1 race in history — only 3 laps behind SC before red flag (half points)',
      '2000: Häkkinen\'s legendary pass on Schumacher around Zonta at 300+ km/h',
      '1998: Circuit redesigned for safety after drivers\' concerns',
      '1950: Fangio wins inaugural Belgian GP for Alfa Romeo',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Ultimate Aero Compromise',
      icon: 'balance',
      description: 'Long straights demand low drag while Sector 2 punishes insufficient downforce.',
    },
    {
      tag: 'Weather Roulette',
      icon: 'weather',
      description: 'Notorious Ardennes microclimate — rain on one sector while another stays dry.',
    },
    {
      tag: 'Eau Rouge Courage',
      icon: 'courage',
      description: 'F1\'s ultimate test of bravery. Flat in qualifying — any lift costs big time.',
    },
    {
      tag: 'Lateral Force Maximum',
      icon: 'lateral',
      description: 'Sector 2\'s high-speed corners generate maximum lateral tyre loads.',
    },
    {
      tag: 'Power Unit Endurance',
      icon: 'power',
      description: 'F1\'s longest circuit with 68-69% full throttle tests engine reliability.',
    },
  ],
}

