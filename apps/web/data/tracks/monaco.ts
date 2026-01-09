import type { TrackIntelligence } from './types'

/**
 * Monaco Grand Prix - Circuit de Monaco
 * Round 8 of the 2025 FIA Formula 1 World Championship
 *
 * The Circuit de Monaco is Formula 1's most iconic and demanding street circuit,
 * winding through the narrow streets of Monte Carlo since 1929. As Nelson Piquet
 * famously described it: "like riding a bicycle around your living room."
 *
 * Monaco is unique in that modern F1 cars barely fit through its streets, yet it
 * remains the ultimate test of driver precision and concentration. The circuit
 * features F1's slowest corner (Fairmont Hairpin at ~48 km/h), the legendary
 * tunnel section, and barriers mere centimeters from the racing line.
 *
 * 2025 marks the introduction of mandatory 2-stop rules specifically for Monaco
 * to improve racing spectacle after the dull 2024 race saw zero overtakes in top 10.
 */
export const monacoTrackIntelligence: TrackIntelligence = {
  circuitId: 'monaco',
  round: 8,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Circuit de Monaco',
    country: 'Monaco',
    location: 'Monte Carlo, Monaco',
    grandPrixName: 'Monaco Grand Prix',
    circuitType: 'Street',
    firstGrandPrix: 1950,
    description:
      "The Circuit de Monaco is Formula 1's most iconic and demanding street circuit, winding through the narrow streets of Monte Carlo since 1929. As Nelson Piquet famously described it: 'like riding a bicycle around your living room.' The circuit features extreme elevation changes, F1's slowest corner (Fairmont Hairpin at ~48 km/h requiring special steering racks), and the legendary tunnel section where drivers transition from bright sunlight to darkness at over 260 km/h. Monaco is unique in that qualifying determines the race result more than any other circuit—overtaking is virtually impossible. The 2024 race saw zero overtakes in the top 10, prompting the FIA to introduce mandatory 2-stop rules for 2025 to improve racing. Part of motorsport's prestigious Triple Crown alongside Indianapolis 500 and Le Mans 24 Hours.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 3.337,
      miles: 2.074,
    },
    raceDistance: {
      km: 260.286,
      miles: 161.734,
    },
    numberOfLaps: 78,
    numberOfCorners: 19,
    drsZones: 1,
    lapRecord: {
      time: '1:12.909',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.25°',
        rear: '-2.25°',
      },
      minStartingPressures: {
        front: '20.0 psi',
        rear: '19.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - CORRECTED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 5,          // Maximum - slow corner exits determine majority of lap time
    tyreStress: 1,        // Minimum - lowest tyre stress on calendar due to slow speeds
    asphaltGrip: 2,       // Low - smooth street surface offers limited mechanical grip
    asphaltAbrasion: 1,   // Minimum - smooth asphalt causes very little tyre wear
    braking: 2,           // Low - limited heavy braking zones; stop-and-go nature
    lateral: 1,           // Minimum - slow corner speeds prevent high lateral loading
    downforce: 5,         // Maximum - every Newton of downforce helps; zero drag penalty
    trackEvolution: 5,    // Maximum - extreme evolution as rubber builds on clean streets
  },

  energyProfile: {
    longitudinal: 'Low',   // Slow speeds minimize acceleration/braking energy
    lateral: 'Low',        // Slow corners prevent high lateral energy demands
  },

  // =========================================================================
  // Sector Breakdown (FIA timing lines: S1 ends ~60m before T5, S2 ends ~67m before T13)
  // =========================================================================
  sectors: [
    {
      sector: 1,
      color: '#FF0000', // Red
      corners: 'T1-T4',
      description:
        "Power and traction sector featuring the only DRS zone on the main straight, leading to heavy braking at Sainte Devote. Continues uphill through Beau Rivage with a blind crest, then the blind Massenet left-hander on a steep climb (often cited at ~12% max gradient), and technical Casino Square.",
      keyFeatures: [
        'Main straight with single DRS zone',
        'T1 (Sainte Devote): 90° right, heavy braking, first-lap incident hotspot',
        'T2 (Beau Rivage): Full-throttle uphill climb with blind crest',
        'T3 (Massenet): Blind entry left on steep gradient, near Monte Carlo Opera',
        'T4 (Casino): Technical right-hander with elevation change',
      ],
      criticalCorners: [
        'T1 (Sainte Devote) - Heavy braking from ~280 km/h to ~110 km/h, first-lap chaos',
        'T3 (Massenet) - Blind entry requires total commitment on steep uphill',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T5-T12',
      description:
        "Precision and commitment sector containing F1's slowest corner (Fairmont Hairpin at ~48 km/h) immediately followed by the fastest section through the famous tunnel at 260+ km/h. The T10-T11 Nouvelle Chicane after tunnel exit serves as Monaco's only realistic overtaking opportunity.",
      keyFeatures: [
        'T5 (Mirabeau Haute): Downhill right compromising entry for upcoming hairpin',
        'T6 (Fairmont Hairpin): F1 slowest corner at ~48 km/h, requires special steering rack',
        'T7-T8 (Mirabeau Bas/Portier): Tight rights leading to tunnel',
        'T9 (Tunnel): Flat-out at 260+ km/h, light-to-dark-to-light transition challenge',
        'T10-T11 (Nouvelle Chicane): Primary overtaking zone, heavy braking from tunnel speed',
        'T12 (Tabac): Fast left, barriers extremely close',
      ],
      criticalCorners: [
        'T6 (Fairmont Hairpin) - Full steering lock at ~48 km/h; teams redesign steering for Monaco',
        'T10-T11 (Nouvelle Chicane) - Heavy braking from ~260 km/h, only overtaking spot',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T13-T19',
      description:
        "Rhythm and commitment sector featuring the legendary Swimming Pool chicanes taken at 200+ km/h, demanding ultimate car stability through rapid direction changes. Concludes with tight La Rascasse (site of Schumacher's controversial 2006 incident) and Antony Noghes corners requiring full steering lock.",
      keyFeatures: [
        'T13-T16 (Swimming Pool 1 & 2): 200+ km/h chicanes alongside harbour',
        'T17: Kink leading into La Rascasse complex',
        'T18 (La Rascasse): 135° right requiring full lock, famous incident site',
        'T19 (Antony Noghes): Final tight right, named after circuit founder',
      ],
      criticalCorners: [
        'T13-T16 (Swimming Pool) - 200+ km/h direction changes, ultimate car stability test',
        'T18 (La Rascasse) - Full steering lock, site of Schumacher 2006 controversy',
      ],
    },
  ],

  // =========================================================================
  // DRS Zones (per FIA 2025 Event Notes)
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '~80m after T16 (post Swimming Pool run)',
      activationPoint: '~18m after T19 (as you unwind onto the pit straight)',
      deactivationPoint: 'Into T1 braking (Sainte Devote)',
      description:
        "Single DRS stretch on the pit straight. If you're close enough through the Swimming Pool exit, you can deploy as you straighten the wheel from the final corner—but the straight is short, and T1 arrives fast, so DRS mainly helps you pressure rather than pass.",
      effectiveness: 'Low',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Maximum',
      explanation:
        "Monaco is the only circuit where teams run absolute maximum downforce with zero drag trade-off consideration—the straights are too short for any drag penalty to matter. Every Newton of downforce provides grip on the low-grip street surface. Ferrari leaned on a proven 2024 Monaco-spec rear wing solution again in 2025, likely to avoid one-off development under cost-cap pressure. Mercedes ran a very deep, high-downforce rear wing profile with pronounced central shaping. Some teams redesign steering racks and suspension geometry specifically for Monaco's unique demands, particularly the Fairmont Hairpin.",
    },
    tyreManagement: {
      compounds: ['C4 (Hard)', 'C5 (Medium)', 'C6 (Soft)'],
      allocation: 'Softest available compounds (3 steps softer than Barcelona)',
      primaryWearMechanism: 'Tyre stress is the lowest on the calendar. Hard compound can last 70+ laps (Tsunoda did 72 laps on hards in 2025). The main limitation is graining in early laps before track rubbers in, not thermal degradation.',
      explanation:
        "Pirelli brings the softest compound range (C4-C6) to Monaco—tyre stress is minimal due to slow speeds. The smooth street surface causes very little abrasion. Traction out of slow corners determines majority of lap time. The 2025 mandatory 2-stop rule opened strategic variety—teams can now push harder knowing they must stop twice.",
      strategicNote: 'Mandatory 2-stop rule unique to Monaco in 2025. Longest stint: 72 laps on hards (Tsunoda). Soft durability limited; quick degradation made pushing difficult. Hards marginally faster than Mediums due to ability to push consistently.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Low initial grip - extreme evolution throughout weekend as rubber accumulates',
      impact: 'Street surface provides limited mechanical grip initially but improves dramatically as rubber builds. Painted road markings become treacherous in wet conditions. Tunnel creates additional wet-dry transition challenges if rain occurs. Moderate Mediterranean temperatures (air low-20s°C, track typically high-30s to low-40s°C) keep thermal stress manageable.',
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Very High',
    primaryZone: 'T10-T11 (Nouvelle Chicane) - Only realistic overtaking zone after tunnel exit with heavy braking',
    secondaryZones: [
      'T1 (Sainte Devote) - Possible with significant speed advantage, but tight corner limits opportunity',
    ],
    factors: [
      'Track position is paramount—qualifying effectively determines race result',
      '2024 race saw ZERO overtakes in top 10, top 10 finished in exact qualifying order',
      '2003 race had zero on-track passes throughout entire Grand Prix (analysis)',
      'Single DRS zone has minimal effectiveness due to short straight',
      'Narrow streets (~7-8m width) physically prevent side-by-side racing',
      'Barriers centimeters from racing line punish any mistakes immediately',
      'Only Nouvelle Chicane offers genuine passing opportunity with heavy braking',
      '2025 mandatory 2-stop rule aims to create strategic overtaking via pit stops',
    ],
    recommendation:
      'Focus all overtaking attempts at the Nouvelle Chicane (T10-T11) after the tunnel—the heavy braking from ~260 km/h provides the only realistic opportunity. Sainte Devote (T1) is theoretically possible but extremely risky given the tight 90° corner. Avoid forcing moves elsewhere—any contact results in barrier collision. In 2025, strategic pit stop timing offers the best path to gaining positions.',
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  // Note: Session conditions below are 2025 forecast data, not measured readings
  weatherProfile: {
    typical: {
      conditions: 'Mediterranean climate (Köppen: Csa) with warm, stable late-May conditions',
      airTemperature: {
        max: '23°C',
        min: '18°C',
        raceTime: '20-22°C',
      },
      rainProbability: 'Low (20-30%) - maritime moderation prevents extreme conditions',
      wind: 'Light southerly sea breeze, 2-5 km/h, minimal impact',
      humidity: 'Moderate (50-60%)',
    },
    sessionConditions: {
      fp1: '21°C, sunny (2025 forecast)',
      fp2: '22°C, sunny (2025 forecast)',
      fp3: '20°C, partly cloudy (2025 forecast)',
      qualifying: '21°C, 60% rain chance — stayed dry (2025 forecast)',
      race: '22°C, sunny, dry conditions (2025 forecast)',
    },
    impact:
      "Rain transforms Monaco into an extremely high-risk circuit—painted road markings become treacherous, and the tunnel creates additional wet-dry transition challenges. The 1984 race saw Senna's legendary wet-weather mastery; the 1996 race had only 4 finishers due to wet conditions. Maritime moderation generally keeps temperatures comfortable, but cloudy conditions can develop quickly. Track temps sat in the high-30s to low-40s across 2025 sessions (~38-44°C observed).",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:12.909',
      driver: 'Lewis Hamilton',
      year: 2021,
    },
    polePositions: [
      {
        year: 2022,
        time: '1:11.376',
        driver: 'LEC',
        note: 'First Monaco pole for Leclerc (DNS in 2021 due to driveshaft failure after taking pole)',
      },
      {
        year: 2023,
        time: '1:11.365',
        driver: 'VER',
        note: 'Verstappen snatches pole with an incredible final sector',
      },
      {
        year: 2024,
        time: '1:10.270',
        driver: 'LEC',
        note: 'Leclerc finally wins at home after years of heartbreak',
      },
      {
        year: 2025,
        time: '1:09.954',
        driver: 'NOR',
        note: 'NEW ALL-TIME TRACK RECORD. First McLaren Monaco pole since 2012 (Hamilton)',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'NOR', time: '1:09.954' },
        { position: 2, driver: 'LEC', time: '1:10.063' },
        { position: 3, driver: 'PIA', time: '1:10.129' },
        { position: 4, driver: 'VER', time: '1:10.669' },
        { position: 5, driver: 'HAD', time: '1:10.923' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '18.665s', driver: 'LEC' },
        { sector: 2, time: '34.009s', driver: 'PIA' },
        { sector: 3, time: '18.955s', driver: 'HAM' },
      ],
      overallIdealLap: '1:11.355',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'NOR',
        meanLapTime: '75.40s',
        gaps: [
          { driver: 'LEC', gap: '+0.02s' },
          { driver: 'PIA', gap: '+0.04s' },
          { driver: 'VER', gap: '+0.28s' },
          { driver: 'HAM', gap: '+0.61s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'HAM',
        meanLapTime: '78.24s',
        gaps: [
          { driver: 'VER', gap: '+0.04s' },
          { driver: 'SAI', gap: '+0.20s' },
          { driver: 'LEC', gap: '+0.20s' },
          { driver: 'PIA', gap: '+0.21s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        // Ocon and Albon tied at 292, but Ocon is listed first in the chart
        fastest: { driver: 'Esteban Ocon', speed: '292 km/h' },
        range: '285-292 km/h',
      },
      race: {
        // "STR reached 295km/h while stuck in traffic"
        withDRS: 'Up to 295 km/h (Stroll in traffic)',
        // Heatmap averages show consistent tunnel exit speeds around 288
        withoutDRS: '~286-289 km/h (Tunnel exit)', 
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'Two-stop mandatory: Laps 19-25 (first stop), Laps 48-55 (second stop)',
      factors: [
        '2025 UNIQUE: Mandatory 2-stop rule',
        'Must use at least 2 different compounds if race is dry',
        'Pit lane time loss approximately 24.5 seconds (60 km/h pit limit adds time)',
        'Track position is everything—losing position nearly impossible to recover',
        'Undercut extremely valuable due to clean air advantage',
        'Late stops viable hoping for Safety Car (several drivers pitted in final 6 laps)',
        'Hard tyres can last 70+ laps; Tsunoda did 72-lap stint on hards',
        'Soft durability limited despite low stress—graining issue in early laps',
      ],
    },
    keyStrategicFactors: [
      'Qualifying determines race result more than any other circuit',
      'Hamilton received 3-place grid penalty in 2025 for impeding',
      'Only 5 drivers finished on lead lap in 2025; 2 scored points while lapped twice',
      'Mercedes struggled from poor grid positions despite strong underlying pace',
      'VER dropped from podium to P4 after pitting on final lap',
      'Clean pit stops paramount—botched stop ruins race with no recovery possible',
    ],
    safetyCarLikelihood: 'Moderate-High (~45% probability - narrow streets increase incident risk)',
    historicalNotes: [
      '2025: Norris wins from pole, McLaren first Monaco win since Hamilton 2008',
      '2025: First Monaco GP with mandatory 2-stop rule',
      '2024: Leclerc finally wins at home—first Monegasque winner since Chiron 1931',
      '2024: Zero overtakes in top 10; top 10 finished in exact qualifying order',
      '2022: Leclerc pole but strategy disaster drops him to P4; Pérez wins',
      '2021: Leclerc pole but DNS due to driveshaft failure; Verstappen wins',
      '1992: Legendary Senna vs Mansell final-lap battle—one of F1 greatest finishes',
      '1984: Senna wet-weather mastery in Toleman—announced himself to the world',
      '1996: Only 4 finishers due to rain—Panis wins for Ligier',
      'Ayrton Senna record 6 wins (5 consecutive 1989-1993)',
      'Graham Hill "Mr. Monaco" with 5 wins; only Triple Crown winner',
      'Contract extended through 2035—Monaco secured on F1 calendar',
    ],
  },

  // =========================================================================
  // Defining Characteristics
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Track Position Premium',
      icon: 'lock',
      description: 'Qualifying determines result. 2024: zero top-10 overtakes, exact grid order finish.',
    },
    {
      tag: 'Maximum Downforce',
      icon: 'aero',
      description: 'Only circuit with zero drag trade-off. Teams run absolute maximum wing angles.',
    },
    {
      tag: "F1's Slowest Corner",
      icon: 'braking',
      description: 'Fairmont Hairpin at ~48 km/h. Special steering racks required; full lock.',
    },
    {
      tag: 'Minimal Tyre Stress',
      icon: 'tyre',
      description: 'Lowest energy demands on calendar. Hards last 70+ laps. 2025 mandatory 2-stop introduced.',
    },
    {
      tag: 'Millimetric Precision',
      icon: 'target',
      description: 'Barriers centimeters from racing line. Single mistake ends race immediately.',
    },
    {
      tag: 'Triple Crown Prestige',
      icon: 'trophy',
      description: 'Part of motorsport Triple Crown. Senna 6 wins. Graham Hill only Triple Crown winner.',
    },
  ],
}

