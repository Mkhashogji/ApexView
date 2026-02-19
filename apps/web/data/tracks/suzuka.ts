import type { TrackIntelligence } from './types'

/**
 * Japanese Grand Prix - Suzuka International Racing Course
 * Round 3 of the 2025 FIA Formula 1 World Championship
 *
 * Suzuka International Racing Course stands as one of Formula 1's most revered
 * venues, consistently ranked as the favorite circuit by drivers worldwide.
 * Originally built in 1962 as a Honda test track, this 5.807 km masterpiece
 * features the only figure-8 layout in Formula 1, with the track crossing over
 * itself via an iconic overpass between the Degner Curves and the back straight.
 *
 * The circuit's defining characteristic is its relentless sequence of high-speed
 * corners that generate extreme tyre stress through sustained lateral forces.
 * The legendary S-Curves deliver rapid linked direction changes where
 * drivers experience over 5g forces in qualifying, while the iconic 130R is
 * taken flat-out at 300+ km/h—a true test of commitment. Pirelli rates Suzuka
 * 5/5 for both tyre stress and lateral forces, necessitating their hardest
 * compound allocation (C1-C3).
 *
 * Japan has crowned 13 World Champions (across Fuji and Suzuka)—more than any
 * other country in F1 history. The 2025 edition saw Max Verstappen claim his fourth consecutive
 * Suzuka victory, while rookie Kimi Antonelli set a new lap record (1:30.965) and
 * became the youngest driver to lead a race and set a fastest lap in F1 history.
 */
export const suzukaTrackIntelligence: TrackIntelligence = {
  circuitId: 'suzuka',
  round: 3,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Suzuka International Racing Course',
    country: 'Japan',
    location: 'Suzuka, Mie Prefecture, Japan',
    grandPrixName: 'Japanese Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 1987,
    description:
      "Suzuka International Racing Course is consistently ranked as the favorite circuit by Formula 1 drivers, and for good reason. Built in 1962 as a Honda test track, this 5.807 km masterpiece features the only figure-8 layout in Formula 1, with the track crossing over itself via an iconic overpass. The circuit's 18 corners create an unrelenting examination of car and driver, from the legendary S-Curves—rapid linked direction changes generating over 5g forces—to the iconic 130R taken flat-out at 300+ km/h. Suzuka's extreme tyre stress stems from consecutive fast corners that compound wear through friction power buildup: as cornering speed rises, vehicles generate more downforce, increasing contact forces and accelerating degradation. Pirelli rates the circuit 5/5 for both tyre stress and lateral forces, necessitating their hardest compound allocation (C1-C3). With only 1.2 km of the 5.807 km lap being perfectly straight and just one DRS zone, overtaking is extremely difficult—Suzuka rewards track position and qualifying performance. Japan has crowned 13 World Champions (across Fuji and Suzuka)—more than any other country in F1 history—cementing Suzuka's legendary status in the sport.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.807,
      miles: 3.608,
    },
    raceDistance: {
      km: 307.471,
      miles: 191.054,
    },
    numberOfLaps: 53,
    numberOfCorners: 18,
    drsZones: 1,
    lapRecord: {
      time: '1:30.965',
      driver: 'Kimi Antonelli',
      year: 2025,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-2.75°',
        rear: '-1.50°',
      },
      minStartingPressures: {
        front: '24.5 psi',
        rear: '23.5 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,          // Medium - limited slow corners; hairpin and chicane exits critical
    asphaltGrip: 4,       // High - good grip surface; 2025 resurfacing T1-T8 improved grip
    asphaltAbrasion: 4,   // High - significant surface wear on tyres
    trackEvolution: 3,    // Medium - moderate evolution through weekend
    tyreStress: 5,        // EXTREME - consecutive fast corners compound wear via friction power
    braking: 2,           // Low - minimal heavy braking zones; lateral loads dominate
    lateral: 5,           // EXTREME - over 5g forces in qualifying; 55% right-hand corners
    downforce: 4,         // High - required for fast corners but not maximum (single DRS zone helps)
  },

  energyProfile: {
    longitudinal: 'Medium',   // Limited heavy braking/acceleration events
    lateral: 'Maximum',       // Sustained lateral loads through Esses, Degners, Spoon, 130R
  },

// =========================================================================
// Sector Breakdown
// =========================================================================
sectors: [
  {
    sector: 1,
    color: '#FF0000', // Red
    corners: 'T1-T7',
    description:
      "The iconic Esses Complex—Suzuka's defining sector and one of the most demanding sequences in motorsport. After heavy braking from 315 km/h into T1 (the only DRS-assisted overtaking zone), drivers navigate T2 before committing to the S-Curves—a rapid sequence of linked direction changes demanding total commitment. This 'tyre-killing sector' generates extreme lateral forces exceeding 5g, with speeds ranging from 180-295 km/h. The sector demands absolute commitment—there is no margin for error through the Esses, and stability during rapid direction changes is paramount. Resurfacing from T1 to T8 entry in 2025 improved grip levels. In FP2, Leclerc (30.62s), Russell (30.65s), and Alonso (30.65s) were fastest through S1.",
    keyFeatures: [
        'T1 primary overtaking zone—heavy braking from approximately 315 km/h to around 75 km/h with DRS',
        'S-Curves: Rapid linked direction changes at approximately 180-295 km/h',
      'Over 5g lateral forces in qualifying trim—extreme front-left tyre stress',
      'Tyre-killing sector—friction power compounds wear through sustained speed and force',
      '2025 resurfacing from T1 to T8 entry improved grip levels',
      'Stability during direction changes is critical—no margin for error',
      'FP2 fastest S1: Leclerc (30.62s); Russell and Alonso tied second (30.65s)',
    ],
    criticalCorners: [
        'T1 (First Curve) - Heavy braking from ~315 to ~75 km/h; only DRS zone; primary overtaking spot',
        'S-Curves - Rapid linked direction changes; flat-out commitment; defines lap pace',
    ],
  },
  {
    sector: 2,
    color: '#0066FF', // Blue
    corners: 'T8-T14',
    description:
      "The technical heart of Suzuka featuring the figure-8 crossover, demanding Degner Curves, the only hairpin overtaking opportunity, and the crucial Spoon exit. The Degner Curves (T8-T9) are high-speed downhill right-handers with dangerously limited run-off—this is where Ernst Degner crashed in 1962, giving the corner its name. After the underpass (where the track crosses beneath itself), drivers navigate the Hairpin (T11)—the main overtaking opportunity outside T1—before the long, flowing Spoon Curve (T13-T14). Spoon is a double-apex left-hander where exit speed is paramount, as it determines velocity onto the back straight leading to 130R. In FP2, Norris was fastest through S2 (39.83s), with Piastri second (39.97s)—demonstrating McLaren's downforce advantage.",
    keyFeatures: [
      'Degner Curves (T8-T9): High-speed downhill right-handers with limited run-off',
      'Figure-8 crossover—track passes under itself between T9 and back straight',
        'T11 Hairpin: Main overtaking opportunity outside T1; heavy braking from ~260 to ~60 km/h',
      'Spoon Curve (T13-T14): Double-apex left-hander; exit speed defines back straight',
      'Mixed-speed technical section tests mechanical grip and car balance',
      'FP2 fastest S2: Norris (39.83s); Piastri second (39.97s)—McLaren downforce advantage',
        'Longest sector by distance and time',
    ],
    criticalCorners: [
      'T8-T9 (Degner Curves) - High-speed downhill; dangerous with minimal run-off; named after 1962 crash',
        'T11 (Hairpin) - Secondary overtaking zone; ~260 to ~60 km/h; traction on exit critical',
      'T13-T14 (Spoon) - Double-apex; exit speed paramount for back straight performance',
    ],
  },
  {
    sector: 3,
    color: '#FFCC00', // Yellow
    corners: 'T15-T18',
    description:
      "The shortest but most iconic sector, featuring the legendary 130R and the setup-compromising Casio Triangle chicane. The back straight from Spoon exit builds speed to 295-310+ km/h before 130R (T15)—one of Formula 1's most famous corners, named for its original 130-meter radius. In qualifying trim, 130R is taken flat-out, requiring total commitment and confidence in the car's aerodynamic grip. Immediately following is the Casio Triangle (T16-T17), a sharp chicane requiring heavy braking from 300 km/h to 70 km/h. This creates a fundamental setup dilemma: cars need stiff suspension for 130R stability but compliant suspension for chicane kerb riding. The chicane exit leads onto the main straight and the only DRS zone. In FP2, Norris was fastest through S3 (17.28s), with Antonelli second (17.40s).",
    keyFeatures: [
      '130R (T15): Iconic corner at 295-310+ km/h—flat-out in qualifying trim',
      'One of F1s most famous corners—tests commitment and aerodynamic confidence',
        'Casio Triangle (T16-T17): Sharp chicane; heavy braking from ~300 to ~70 km/h',
      'Setup compromise zone—stiff for 130R stability vs. compliant for chicane kerbs',
      'Chicane exit leads to only DRS zone and main straight',
      'Long full-throttle section from Spoon through 130R to chicane braking',
      'FP2 fastest S3: Norris (17.28s); Antonelli second (17.40s)',
    ],
    criticalCorners: [
      'T15 (130R) - Ultra high-speed 295-310+ km/h; flat-out in qualifying; separates legends',
      'T16-T17 (Casio Triangle) - Sharp chicane; kerb usage critical; exit sets up main straight',
    ],
  },
],

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: '~40m after T15 (130R)',
      activationPoint: '~100m before the control line on the pit straight',
      deactivationPoint: 'T1 braking zone',
      description:
        "Suzuka's only DRS zone runs the length of the main straight to the T1 braking zone. Detection occurs shortly after 130R, meaning drivers must be within 1 second through the high-speed S3 complex to benefit—rewarding those who can follow closely through 130R itself. The combination of DRS and slipstream creates a meaningful speed advantage into the T1 braking zone, where speeds drop from approximately 315 km/h to around 75 km/h. This heavy braking event represents the widest overtaking window on the circuit.",
      effectiveness: 'High',
    },
  ],

  // =========================================================================
  // Technical Insights
  // =========================================================================
  technicalInsights: {
    aerodynamicSetup: {
      wingLevel: 'Medium-High',
      explanation:
        "Suzuka demands high downforce to maximize performance through its relentless sequence of fast corners, reflected in Pirelli's 4/5 downforce rating. The circuit's unique character—only approximately 1.2 km of straight from 5.807 km total—means corner speed gains far outweigh any straight-line penalty. In 2025, observed top speeds ranged from approximately 319-326 km/h across the grid, with teams adopting varied aero philosophies. Based on visible rear-wing configurations, higher-downforce setups appeared to provide advantages through the S-Curves, Degners, Spoon, and 130R despite some straight-line speed penalty. The single DRS zone reduces the penalty for high-drag configurations, making downforce the clear priority for qualifying pace.",
    },
    tyreManagement: {
      compounds: ['C1 (Hard)', 'C2 (Medium)', 'C3 (Soft)'],
      allocation: 'Hardest selection on calendar (shared with Bahrain)—required for extreme lateral stress',
      primaryWearMechanism: 'Front-left degradation through consecutive right-hand corners. The Esses (T3-T7), Degner Curves, and Spoon deliver sustained lateral loading that compounds wear through friction power buildup—as cornering speed increases, downforce rises, contact forces grow, and temperatures escalate.',
      explanation:
        "Suzuka's extreme tyre stress (5/5 Pirelli rating) stems from a unique combination of sustained high-speed corners that generate continuous lateral forces. Unlike circuits with heavy braking zones that stress tyres in discrete events, Suzuka's consecutive fast corners create cumulative thermal stress through friction power—the product of speed and force. The 55/45 right-to-left corner split (10 right, 8 left) creates asymmetric wear, particularly punishing the front-left tyre. In 2025, the Hard compound proved both faster AND more durable than the Medium—an unusual characteristic highlighting how Suzuka's demands differ from typical circuits. The Soft compound degraded rapidly and was not recommended for race stints.",
      strategicNote: 'One-stop optimal: Medium (19-21 laps) → Hard (32-34 laps). Alternative: Hard (28-31) → Medium (22-25). Antonelli extended first stint to Lap 31 (M31-H22) with excellent final pace. Undercut potential MEDIUM—difficult to create gap through single-file S1/S2. Safety Car plausible due to narrow track and gravel traps at key corners.',
    },
    surfaceCharacteristics: {
      gripLevel: 'High (4/5) - Good grip surface with 2025 resurfacing from T1 to T8 entry',
      impact: "Suzuka's surface provides relatively high grip (4/5 Pirelli rating), especially following the 2025 resurfacing from T1 to T8 entry. However, the circuit's extreme tyre stress comes not from surface abrasion but from the sustained lateral forces through consecutive fast corners. Track evolution is moderate (3/5), with grip improving steadily through the weekend as rubber is laid down. The figure-8 layout creates an interesting characteristic: the mix of clockwise (Esses) and anti-clockwise (Spoon, 130R) sections helps balance overall tyre wear compared to circuits with directional bias. Weather is notoriously unpredictable at Suzuka, with rain common during the April race date—teams often bring higher downforce options as wet-weather backup.",
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Very High',
    primaryZone: 'T1 (First Curve) - Heavy braking from ~315 km/h to ~75 km/h with DRS; only realistic passing opportunity',
    secondaryZones: [
      'T11 (Hairpin) - Secondary option; heavy braking ~260 to ~60 km/h but narrower approach',
      'T16 (Casio Triangle) - Risky divebomb opportunity; rarely successful due to chicane nature',
    ],
    factors: [
      'Only ONE DRS zone on entire circuit—severely limits passing opportunities',
      'Narrow track width through technical sections prevents side-by-side racing',
      'Dirty air devastates following car through Esses, Degners, and Spoon',
      'High-speed corner sequences make following within 1 second extremely difficult',
      '29 of 34 Suzuka races won from front row (18 from pole)—track position paramount',
      'Qualifying performance essentially determines race result',
      'T1 offers best chance but requires significant speed delta to complete move',
      'Defending driver has advantage through technical S1 and S2',
    ],
    recommendation:
      "Focus all overtaking attempts at T1 using the DRS zone and main straight slipstream. The combination of DRS advantage and heavy braking from approximately 315 km/h to around 75 km/h creates the only realistic passing window. Conserve battery deployment through S1 and S2 when following (accepting time loss to dirty air), then deploy fully on the main straight for T1 attack. The T11 Hairpin provides a secondary option but the narrower approach and shorter braking zone reduce success probability. Do not attempt moves through the Esses, Degners, Spoon, or 130R—the risk-reward ratio is extremely unfavorable. Qualifying position is critical at Suzuka; historical data shows 29 of 34 races have been won from the front row.",
  },

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Variable spring weather; mild temperatures with significant rain risk',
      airTemperature: {
        max: '22°C',
        min: '15°C',
        raceTime: '18-20°C (afternoon race)',
      },
      rainProbability: 'Significant—April weather can swing quickly; rain not uncommon',
      wind: 'Variable—can significantly affect high-speed corners (Esses, 130R)',
      humidity: '60-80% (coastal location)',
    },
    sessionConditions: {
      fp1: 'Variable—2025 saw grass fires cause red flags',
      fp2: 'Typically representative of race conditions',
      fp3: 'Dry in 2025; final setup confirmation',
      qualifying: 'Dry, cool conditions in 2025—track temperature 25-30°C',
      race: 'Morning rain in 2025 cleared; dry race with cool track (25-30°C)',
    },
    impact:
      "Suzuka's weather is notoriously unpredictable, with the circuit's location near the coast of Mie Prefecture exposing it to rapidly changing conditions. Rain is not uncommon during the April race date, and several memorable wet races have occurred here—including Verstappen's 2022 title-clinching race in torrential conditions. The variable wind can significantly affect car behavior through high-speed corners like the Esses and 130R, where small changes in aerodynamic loading become magnified. Teams typically bring higher downforce rear wing options as backup for wet conditions. The 2025 weekend saw unusual incidents including grass fires during practice sessions that caused red flags, highlighting the unpredictable nature of this venue.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:30.965',
      driver: 'Kimi Antonelli',
      year: 2025,
    },
    polePositions: [
      {
        year: 2022,
        time: '1:29.304',
        driver: 'VER',
        note: 'Verstappen edges pole by 0.010s over Leclerc; clinched title in rain-shortened race',
      },
      {
        year: 2023,
        time: '1:28.877',
        driver: 'VER',
        note: 'Verstappen dominant weekend',
      },
      {
        year: 2024,
        time: '1:28.197',
        driver: 'VER',
        note: 'Verstappen third consecutive Suzuka pole',
      },
      {
        year: 2025,
        time: '1:26.983',
        driver: 'VER',
        note: 'NEW ALL-TIME POLE RECORD; beat Norris by 0.012s',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'VER', time: '1:26.983' },
        { position: 2, driver: 'NOR', time: '1:26.995' },
        { position: 3, driver: 'PIA', time: '1:27.027' },
        { position: 4, driver: 'LEC', time: '1:27.299' },
        { position: 5, driver: 'RUS', time: '1:27.318' },
      ],
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Practice 2',
      sectors: [
        { sector: 1, time: '30.62s', driver: 'LEC' },
        { sector: 2, time: '39.83s', driver: 'NOR' },
        { sector: 3, time: '17.28s', driver: 'NOR' },
      ],
      overallIdealLap: '1:27.730',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'VER',
        meanLapTime: '92.46s',
        gaps: [
          { driver: 'NOR', gap: '+0.00s (identical pace)' },
          { driver: 'PIA', gap: '+0.03s' },
          { driver: 'ANT', gap: '+0.26s' },
          { driver: 'LEC', gap: '+0.28s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '96.05s',
        gaps: [
          { driver: 'PER', gap: '+0.28s' },
          { driver: 'SAI', gap: '+0.42s' },
          { driver: 'NOR', gap: '+0.54s' },
          { driver: 'PIA', gap: '+0.84s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'George Russell / Charles Leclerc', speed: '326 km/h' },
        range: '319-326 km/h',
      },
      race: {
        withDRS: 'Up to 343 km/h (Bortoleto with slipstream + DRS)',
        withoutDRS: '~316-318 km/h (Antonelli clean air pace)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop: Laps 19-25 (OPTIMAL)',
      factors: [
        'One-stop strategy optimal due to resilient 2025 Hard compound',
        'First stop window: Laps 19-25 (front-runners pitted L19-L21)',
        'Antonelli extended first stint to Lap 31 (M31-H22) with excellent final pace',
        'Pit lane time loss: ~23-24 seconds',
        'Pit stop execution varied across teams; slow stops can be costly at track-position-critical Suzuka',
      ],
    },
    keyStrategicFactors: [
      'Hard compound faster AND more durable than Medium in 2025 (unusual)',
      'Undercut potential: MEDIUM—difficult to create gap through single-file technical sectors',
      'Track position paramount—29 of 34 Suzuka races won from front row',
      'Pit exit drama: Red Bull slow stop nearly cost Verstappen lead; Norris forced onto grass',
      'Only 1.423s separated VER and NOR after 53 laps; qualifying result decided the win',
    ],
    safetyCarLikelihood: 'Plausible—narrow track, gravel traps, limited run-off at Degners',
    historicalNotes: [
      '2025: Verstappen 4th consecutive Suzuka win; Antonelli youngest to lead/set FL',
      '2022: Verstappen clinches 2nd title in rain-shortened race',
      '2014: Jules Bianchi tragic accident led to major safety changes (Halo, VSC)',
      '2005: Raikkonen wins from P17; Alonso legendary 130R pass on Schumacher',
      '1989/1990: Senna-Prost collisions—defining moments of F1 greatest rivalry',
      'Japan has crowned 13 champions (Fuji/Suzuka)—more than any other country',
    ],
  },

  // =========================================================================
  // Defining Characteristics (60-80 chars max per description)
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Figure-8 Legend',
      icon: 'route',
      description: 'Only F1 circuit with overpass. Track crosses itself uniquely.',
    },
    {
      tag: 'Maximum Lateral',
      icon: 'gauge',
      description: '5/5 Pirelli lateral rating. Over 5g forces in qualifying.',
    },
    {
      tag: "Driver's Circuit",
      icon: 'trophy',
      description: 'Ranked #1 by drivers. Tests all aspects of car and skill.',
    },
    {
      tag: '130R Challenge',
      icon: 'speed',
      description: 'Iconic corner at 300+ km/h. Flat-out commitment required.',
    },
    {
      tag: 'Title Decider',
      icon: 'flag',
      description: 'Japan crowned 13 champions (Fuji/Suzuka)—most of any country.',
    },
    {
      tag: 'Hardest Compounds',
      icon: 'tyre',
      description: 'C1-C3 selection. Extreme tyre stress demands hardest rubber.',
    },
  ],

  fuelEffectPerKg: 0.029,
}
