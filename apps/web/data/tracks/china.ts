import type { TrackIntelligence } from './types'

/**
 * Chinese Grand Prix - Shanghai International Circuit
 * Round 2 of the 2025 FIA Formula 1 World Championship
 *
 * The Shanghai International Circuit hosted the Chinese Grand Prix from 2004
 * to 2019, returning in 2024 after a four-year absence (2020–2023). Designed by Hermann Tilke at a
 * cost of approximately $450 million, this 5.451 km circuit features a unique
 * layout inspired by the Chinese character "上" (shàng), meaning "upward" or
 * "ascend"—symbolizing Shanghai's meteoric rise as a global metropolis.
 *
 * The circuit's defining characteristic is its iconic Turn 1-2 complex: a
 * 270-degree right-hand spiral that progressively tightens, demanding precise
 * throttle and brake modulation as drivers bleed speed through multiple apexes.
 * This "snail" design is mirrored at Turns 11-13, creating bookend technical
 * challenges. Between them lies one of Formula 1's longest straights—approximately 1,170m
 * between Turns 13 and 14—offering prime overtaking into the heavy braking
 * zone at the T14 hairpin.
 *
 * Pirelli rates Shanghai 5/5 for track evolution, with grip improving dramatically
 * through the weekend. The rear-left tyre experiences the most stress due to the
 * clockwise direction combining traction forces with sustained vertical loads.
 * The 2025 edition saw Oscar Piastri claim his maiden Grand Prix pole and first
 * win of the season, while Lewis Hamilton won the Sprint—Ferrari's first ever
 * Sprint victory—before a disastrous double disqualification ended Ferrari's
 * weekend on a historic low note.
 */
export const chinaTrackIntelligence: TrackIntelligence = {
  circuitId: 'shanghai',
  round: 2,

  // =========================================================================
  // Circuit Overview
  // =========================================================================
  circuitOverview: {
    circuitName: 'Shanghai International Circuit',
    country: 'China',
    location: 'Jiading District, Shanghai, China',
    grandPrixName: 'Chinese Grand Prix',
    circuitType: 'Permanent',
    firstGrandPrix: 2004,
    description:
      "The Shanghai International Circuit hosted the Chinese Grand Prix from 2004 to 2019, returning in 2024 after a four-year absence. Designed by Hermann Tilke at a cost of approximately $450 million, this 5.451 km masterpiece features a unique layout inspired by the Chinese character '上' (shàng), meaning 'upward'—symbolizing Shanghai's rise as a global metropolis. The circuit's defining characteristic is its iconic Turn 1-2 complex: a 270-degree right-hand spiral that progressively tightens, demanding precise throttle and brake modulation. This 'snail' design is mirrored at Turns 11-13, creating bookend technical challenges. Between them lies one of Formula 1's longest straights—approximately 1,170m between Turns 13 and 14—offering prime overtaking into the heavy braking T14 hairpin. Shanghai features a diverse mix of low, medium, and high-speed corners, with Turn 7 taken at over 270 km/h in qualifying—the fastest non-full-throttle corner on the circuit. Pirelli rates Shanghai 5/5 for track evolution, with grip improving dramatically through the weekend. The rear-left tyre experiences the most stress due to the clockwise direction combining traction forces with sustained vertical loads. Lewis Hamilton holds the record for most Chinese GP wins (6), and the circuit returned to the calendar in 2024 after a five-year COVID-induced hiatus.",
  },

  // =========================================================================
  // Circuit Statistics
  // =========================================================================
  circuitStats: {
    lapLength: {
      km: 5.451,
      miles: 3.387,
    },
    raceDistance: {
      km: 305.066,
      miles: 189.568,
    },
    numberOfLaps: 56,
    numberOfCorners: 16,
    drsZones: 2,
    lapRecord: {
      time: '1:32.238',
      driver: 'Michael Schumacher',
      year: 2004,
    },
    tyreSpecs: {
      camberLimits: {
        front: '-3.00°',
        rear: '-1.75°',
      },
      minStartingPressures: {
        front: '26.5 psi',
        rear: '23.0 psi',
      },
    },
  },

  // =========================================================================
  // Circuit Characteristics (Pirelli Ratings) - VERIFIED & CORRECTED VALUES
  // =========================================================================
  circuitCharacteristics: {
    traction: 3,          // Medium - important for hairpin and snail complex exits
    asphaltGrip: 3,       // Medium - standard grip surface
    asphaltAbrasion: 3,   // Medium - moderate surface wear on tyres
    trackEvolution: 5,    // MAXIMUM - grip improves dramatically through weekend
    tyreStress: 4,        // High - rear-left stressed from clockwise direction
    braking: 4,           // High - T14 hairpin one of heaviest braking zones on calendar
    lateral: 4,           // High - sustained lateral loads through T7-T8 complex
    downforce: 3,         // Medium - balance between corner speed and straight-line performance
  },

  energyProfile: {
    longitudinal: 'High', // Heavy braking at T14, moderate elsewhere
    lateral: 'High',      // Sustained loads through T1-T2, T7-T8, T11-T13 complexes
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
        "Shanghai’s lap begins with the famous ever-tightening Turns 1–2 ‘snail’ (over 270 degrees), which forces drivers to bleed speed progressively while keeping the car balanced. After that, the track changes direction with a quick left sequence through Turns 3–4, rewarding a stable front end and clean positioning for the next braking/rotation phase into Turn 6. Because the circuit runs clockwise, the left-side tyres (especially the rear-left under traction) begin accumulating load early.",
      keyFeatures: [
        'T1-T2 Snail Complex: ever-tightening right-hander (270°+) demanding balance and patience',
        'Direction change through T3-T4 (quick left sequence) rewards front-end stability',
        'Early traction phases can stress the left-side tyres on a clockwise circuit',
      ],
      criticalCorners: [
        'T1-T2 (Snail) - Ever-tightening radius; precision and balance critical',
        'T4 Exit - Important for positioning into the next complex',
        'T6 - Key rotation/traction corner to set up the following sequence',
      ],
    },
    {
      sector: 2,
      color: '#0066FF', // Blue
      corners: 'T7-T10',
      description:
        "This sector blends fast, high-load direction changes with a flowing sequence that tests aerodynamic stability and mechanical grip. The high-g Turns 7–8 are a standout feature of the circuit and punish tyre management if the car slides. The sector finishes by setting up the approach into the Turns 11–13 complex, where getting the car ‘pointed’ correctly becomes crucial for the long back straight.",
      keyFeatures: [
        'T7: fastest non-full-throttle corner on the circuit (over 270 km/h in qualifying)',
        'T7-T8: high lateral load / high-g section that rewards aero stability and confident turn-in',
        'Sustained direction change and balance demands through T7-T10',
        'Exit quality matters because it influences the approach and positioning for T11-T13',
      ],
      criticalCorners: [
        'T7-T8 - High-load sequence; stability and tyre management are key',
        'T10 Exit - Helps position the car cleanly for the next complex',
      ],
    },
    {
      sector: 3,
      color: '#FFCC00', // Yellow
      corners: 'T11-T16',
      description:
        "Sector 3 contains the long Turns 11–13 complex that feeds onto Shanghai’s back straight (often cited around 1.2km / ~1,170m) leading into the heavy-braking Turn 14 hairpin. Exit speed from the T13 area is vital because it dictates how effective the slipstream and DRS will be on the straight. The main DRS zone’s detection point is at Turn 12, and the pit-straight DRS detection is shortly before Turn 16, with activation after Turn 16.",
      keyFeatures: [
        'Turns 11–13 complex: prioritises stability and exit speed onto the long back straight',
        'Back straight is one of the longest on the F1 calendar (~1,170m)',
        'DRS (back straight): detection at T12; activation moved closer to T13 exit in recent configs',
        'Turn 14 hairpin: prime overtaking/braking zone after the long straight',
        'Second DRS zone: detection 35m before T16; activation 98m after T16 (pit straight)',
      ],
      criticalCorners: [
        'T12 (DRS detection reference) - Crucial point to be within 1s for back-straight DRS',
        'T13 Exit - Determines back-straight speed and overtaking potential',
        'T14 (Hairpin) - Major braking/overtaking zone after the long straight',
        'T16 (Last Corner) - Sets up pit straight and DRS Zone 2 activation after the corner',
      ],
    },
  ],  

  // =========================================================================
  // DRS Zones
  // =========================================================================
  drsZones: [
    {
      zone: 1,
      detectionPoint: 'Turn 12',
      activationPoint:
        'After Turn 13 onto the back straight (2025: activation moved 75m closer to T13 exit)',
      deactivationPoint: 'Turn 14 braking zone',
      description:
        "Shanghai's primary DRS zone runs the length of the back straight (~1,170m) leading into the Turn 14 hairpin. The detection point is at Turn 12, so drivers must be within 1 second at that reference to gain DRS on the straight. For 2025, activation was moved 75m closer to the T13 exit, increasing DRS time before the T14 braking phase.",
      effectiveness: 'Very High',
    },
    {
      zone: 2,
      detectionPoint: '35m before Turn 16',
      activationPoint: '98m after Turn 16 (pit straight)',
      deactivationPoint: 'Turn 1 braking zone',
      description:
        "The secondary DRS zone runs along the pit straight from Turn 16 to the Turn 1 braking zone. Detection is set shortly before Turn 16, and activation begins after Turn 16. While shorter than the back-straight zone, it can create opportunities into Turn 1, especially with slipstream and strong exits from the final corner.",
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
        "Shanghai demands a careful balance between corner speed and straight-line performance, reflected in Pirelli's 3/5 downforce rating. The ~1,170m back straight and pit straight punish excessive drag, while the high-speed T7 complex and technical snail sections reward downforce. Based on observed 2025 weekend configurations and speed-trap data, most teams appeared to opt for medium-load rear wings. Top speeds ranged from approximately 327–336 km/h in qualifying, with varied approaches across the grid. Higher-downforce setups showed advantages through the technical sections despite some straight-line speed penalty, demonstrating that aerodynamic efficiency through corners remains important at this circuit.",
    },
    tyreManagement: {
      compounds: ['C2 (Hard)', 'C3 (Medium)', 'C4 (Soft)'],
      allocation: 'One step harder than Australia—required due to higher-than-average tyre stress',
      primaryWearMechanism: 'Rear-left degradation from clockwise circuit direction. The combination of traction forces exiting slow corners (T3, T4, T14) and sustained vertical load through high-speed sections creates asymmetric stress. The track evolution rating of 5/5 means grip improves dramatically through the weekend.',
      explanation:
        "Shanghai's tyre characteristics are defined by its clockwise direction and maximum track evolution rating (5/5). The rear-left tyre experiences the most stress due to the combination of traction forces and sustained vertical loads through right-hand corners. Pirelli brought compounds one step harder than Australia, anticipating the elevated stress levels. In 2025, the Hard compound (C2) proved exceptionally durable, enabling comfortable one-stop strategies for the entire field. The Medium compound (C3) worked well for opening stints of 13-17 laps before transitioning to Hards. Track evolution was dramatic—qualifying times were over 1 second faster than early practice as rubber laid down improved grip significantly.",
      strategicNote: 'One-stop optimal: Medium (13-17 laps) → Hard (39-43 laps). Hard compound extremely durable in 2025—some drivers extended Hard stints beyond 40 laps. Hamilton attempted two-stop (M13-H24-H19) to chase podium but lost position. Low tyre degradation made one-stop clearly superior. Generous run-off at most corners reduces Safety Car risk.',
    },
    surfaceCharacteristics: {
      gripLevel: 'Medium (3/5) - Standard grip surface with maximum track evolution',
      impact: "Shanghai's surface provides medium grip levels (3/5 Pirelli rating), but the circuit's defining characteristic is its maximum track evolution rating (5/5). Grip improves dramatically from Friday to Sunday as rubber is laid down on the racing line. This evolution means early practice sessions provide limited representative data, and teams must extrapolate setup changes for qualifying and race conditions. The clockwise direction creates asymmetric tyre wear, particularly stressing the rear-left through the sustained right-hand corners of the T1-T2 and T11-T13 snail complexes. Weather can significantly impact track evolution—rain washes away rubber buildup, potentially resetting grip levels.",
    },
  },

  // =========================================================================
  // Overtaking Analysis
  // =========================================================================
  overtakingAnalysis: {
    difficulty: 'Medium',
    primaryZone:
      'T14 (Hairpin) - Main passing spot after the long back straight with DRS Zone 1; heavy braking from ~320 km/h to low-70s km/h',
    secondaryZones: [
      'T1 (Snail Entry) - DRS Zone 2 can create a follow-up chance into T1 before the radius tightens',
      'T6 - Recognised secondary passing spot under heavy braking (no direct DRS activation into the corner itself)',
    ],
    factors: [
      'Two DRS zones increase passing chances compared to single-DRS circuits',
        'Long back straight (~1,170m) builds strong closing speed into T14',
      'Back-straight DRS detection is at T12, so staying within 1s there is crucial for a T14 attempt',
      'Pit-straight DRS detection is 35m before T16 (activation 98m after T16), enabling follow-up pressure into T1',
      'T14 is the most reliable late-braking move due to the long straight and heavy stop',
      'T1 can work as a secondary opportunity, but the tightening radius quickly punishes poor positioning',
      'Turn 6 is a credible alternative passing spot under braking if T14/T1 are not possible',
      '2025 example: McLaren finished 1–2, showing how pace plus execution can convert strong overtaking potential into results',
    ],
    recommendation:
      "Prioritise attacks into T14 by maximising exit quality from the T11–T13 complex and ensuring you are within 1s at the T12 detection point. If the T14 move does not stick, focus on a clean exit to remain close and trigger DRS Zone 2 (detection before T16, activation after T16) for pressure into T1. Use T6 as an opportunistic braking-zone move when the car ahead is compromised or defending hard. Avoid forcing moves through the high-load mid-lap direction changes, where dirty air and risk are higher.",
  },  

  // =========================================================================
  // Weather Profile
  // =========================================================================
  weatherProfile: {
    typical: {
      conditions: 'Variable spring weather; mild temperatures',
      airTemperature: {
        max: '~27°C',
        min: '~18°C',
        raceTime: 'Typically mid-20s°C (afternoon race)',
      },
      rainProbability: 'Possible—spring weather can be unpredictable',
      wind: 'Variable—can affect high-speed corners (T7, T11-T13)',
      humidity: 'Moderate to high (coastal proximity)',
    },
    sessionConditions: {
      fp1: 'Variable—track evolution begins; limited representative data',
      fp2: 'More representative; teams focus on race simulations and long runs',
      fp3: 'Final setup confirmation; track grip improving significantly',
      qualifying: 'Dry in 2025; windy conditions affected consistency',
      race: 'Dry in 2025; warm conditions; optimal for one-stop strategy',
    },
    impact:
      "Shanghai's spring weather is generally mild but variable, with rain always a possibility during the weekend. Air quality can vary given the circuit's location. Wind can significantly affect car behavior through the high-speed T7 complex and the exposed back straight—gusts were a factor in qualifying in 2025, with drivers reporting inconsistent grip levels between runs. Warm track temperatures in 2025 contributed to lower-than-expected tyre degradation, making one-stop strategies comfortable for all frontrunners.",
  },

  // =========================================================================
  // Benchmark Lap Times
  // =========================================================================
  benchmarkLapTimes: {
    lapRecord: {
      time: '1:32.238',
      driver: 'Michael Schumacher',
      year: 2004,
    },
    polePositions: [
      {
        year: 2019,
        time: '1:31.547',
        driver: 'BOT',
        note: 'Last pole before COVID hiatus; Bottas beats Hamilton by 0.023s',
      },
      {
        year: 2024,
        time: '1:33.660',
        driver: 'VER',
        note: 'Return after 5-year absence; cooler conditions',
      },
      {
        year: 2025,
        time: '1:30.641',
        driver: 'PIA',
        note: 'NEW ALL-TIME QUALIFYING RECORD; Piastri maiden GP pole',
      },
    ],
    qualifyingReference: {
      year: 2025,
      top5: [
        { position: 1, driver: 'PIA', time: '1:30.641' },
        { position: 2, driver: 'RUS', time: '1:30.723' },
        { position: 3, driver: 'NOR', time: '1:30.793' },
        { position: 4, driver: 'VER', time: '1:30.817' },
        { position: 5, driver: 'HAM', time: '1:30.927' },
      ],
    },
    sprintReference: {
      year: 2025,
      sprintPole: {
        driver: 'HAM',
        time: '1:30.849',
        note: 'First Ferrari Sprint pole',
      },
      sprintWinner: {
        driver: 'Lewis Hamilton',
        team: 'Ferrari',
        note: 'First Ferrari Sprint victory in F1',
      },
    },
    sectorBenchmarks: {
      year: 2025,
      session: 'Sprint Qualifying',
      sectors: [
        { sector: 1, time: '24.01s', driver: 'NOR' },
        { sector: 2, time: '27.25s', driver: 'HAM' },
        { sector: 3, time: '39.24s', driver: 'VER' },
      ],
      overallIdealLap: '1:30.500',
    },
    racePaceBenchmarks: [
      {
        year: 2025,
        fastestDriver: 'PIA',
        meanLapTime: '96.89s',
        gaps: [
          { driver: 'HAM', gap: '+0.02s (two-stop inflated pace)' },
          { driver: 'NOR', gap: '+0.19s' },
          { driver: 'RUS', gap: '+0.22s' },
          { driver: 'VER', gap: '+0.26s' },
        ],
      },
      {
        year: 2024,
        fastestDriver: 'VER',
        meanLapTime: '99.76s',
        gaps: [
          { driver: 'PER', gap: '+0.67s' },
          { driver: 'NOR', gap: '+0.88s' },
          { driver: 'ALO', gap: '+0.99s' },
        ],
      },
    ],
    topSpeedReference: {
      qualifying: {
        fastest: { driver: 'Kimi Antonelli / Max Verstappen', speed: '336 km/h' },
        range: '327-336 km/h',
      },
      race: {
        withDRS: 'Up to 351 km/h (Hamilton with DRS)',
        withoutDRS: '~316-324 km/h (clean air)',
      },
    },
  },

  // =========================================================================
  // Strategic Insights
  // =========================================================================
  strategicInsights: {
    pitStopWindow: {
      typical: 'One-stop: Laps 13-17 (OPTIMAL)',
      factors: [
        'One-stop strategy optimal due to unexpectedly low tyre degradation in 2025',
        'First stop window: Laps 13-17 (front-runners pitted L13-L15)',
        'Hamilton attempted two-stop gamble (M13-H24-H19) but lost positions',
        'Pit lane time loss: ~23-24 seconds',
        'Pit stop execution varied across teams in 2025',
      ],
    },
    keyStrategicFactors: [
      'Hard compound extremely durable—40+ lap stints comfortable',
      'Track evolution (5/5) means qualifying pace advantage carries into race',
      'Low degradation made Hamilton two-stop gamble unsuccessful',
      'Undercut potential: LOW—difficult to create gap with similar tyre performance',
      'Starting on Hards (Stroll, Bearman, Lawson) proved equally viable to Medium start',
      'DRS trains formed in midfield—track position more valuable than tyre strategy',
    ],
    safetyCarLikelihood: 'Historically not uncommon—generous run-off reduces but does not eliminate risk',
    historicalNotes: [
      '2025: First Ferrari double DSQ in F1 history (Leclerc/Hamilton technical infringement)',
      '2025: Lewis Hamilton wins Sprint—Ferrari first ever Sprint victory',
      '2025: Oscar Piastri maiden GP pole and first win of season',
      '2024: Return after 5-year COVID hiatus; Verstappen dominant',
      '2019: Last race before hiatus; Hamilton wins 6th Chinese GP',
      '2007: Hamilton gravel trap pit entry—cost him championship to Räikkönen',
      '2004: Inaugural race; Barrichello wins; Schumacher sets lap record (still stands)',
      '18 Chinese GPs held at Shanghai; Hamilton record 6 wins',
    ],
  },

  // =========================================================================
  // Defining Characteristics (60-80 chars max per description)
  // =========================================================================
  definingCharacteristics: [
    {
      tag: 'Snail Complex',
      icon: 'route',
      description: 'Iconic T1-T2 spiral tightens through 270°. Signature corner.',
    },
    {
      tag: 'Mega Straight',
      icon: 'arrow-right',
      description: '~1,170m back straight—among longest on F1 calendar.',
    },
    {
      tag: 'T14 Hairpin',
      icon: 'target',
      description: 'Premier overtaking zone. Heavy braking from ~320 km/h.',
    },
    {
      tag: 'Track Evolution',
      icon: 'trending-up',
      description: '5/5 Pirelli rating. Grip transforms through weekend.',
    },
    {
      tag: 'Dual DRS',
      icon: 'zap',
      description: 'Two DRS zones enhance passing—better than most Tilke tracks.',
    },
    {
      tag: 'Shàng Symbol',
      icon: 'map',
      description: 'Layout inspired by Chinese character meaning "upward".',
    },
  ],

  fuelEffectPerKg: 0.032,
}
