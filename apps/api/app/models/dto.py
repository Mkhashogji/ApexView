from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelCaseModel(BaseModel):
    """Base model that serializes to camelCase for frontend compatibility."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


SessionType = Literal[
    "Practice", "Qualifying", "Sprint Qualifying", "Sprint", "Race"
]


class SessionResponse(CamelCaseModel):
    """Session information response."""
    session_id: str
    session_type: SessionType
    session_name: str
    season: int
    round: int
    is_sprint_weekend: bool
    date: Optional[datetime] = None
    circuit_name: Optional[str] = None


class LapResponse(CamelCaseModel):
    """Lap data response."""
    lap_number: int
    driver: str
    lap_time: float
    sector1_time: Optional[float] = None
    sector2_time: Optional[float] = None
    sector3_time: Optional[float] = None
    compound: Optional[str] = None
    tyre_age: Optional[int] = None
    is_personal_best: bool = False


class TelemetryResponse(CamelCaseModel):
    """
    Telemetry data response with flat arrays for performance.
    All arrays are distance-indexed and have the same length.
    """
    driver: str
    lap_number: int
    lap_time: Optional[float] = None  # Official lap time in seconds
    distance: List[float]
    speed: List[float]
    throttle: List[float]
    brake: List[float]
    gear: List[int]
    # Fields for Tier 1 delta algorithm (RelativeDistance + Time scaling)
    relative_distance: Optional[List[float]] = None  # 0-1 normalized track position
    time: Optional[List[float]] = None  # Elapsed lap time in seconds (starting at 0)
    rpm: Optional[List[int]] = None
    drs: Optional[List[int]] = None


class DeltaResponse(CamelCaseModel):
    """Time delta analysis between two drivers."""
    reference_driver: str
    compare_driver: str
    distance: List[float]
    delta: List[float]  # seconds, positive = compare driver is slower


# =============================================================================
# G0 — Honest Acquisition: native telemetry metadata (NEW endpoint /telemetry/meta;
# existing response models above are frozen against the golden contract)
# =============================================================================

class GapInterval(CamelCaseModel):
    """
    One acquisition gap on the native car stream (dt > 3x median dt, strict).

    Frame note (continuation review L1-5): t_start/t_end are on the car
    frame's raw Time axis (first sample sits at Time[0] > 0 after lap start),
    NOT the re-zeroed `time` array served by /telemetry — align with a
    constant Time[0] offset if cross-referencing. The distance bounds
    (d_start/d_end) are the consumption contract (corner-zone overlap).
    """
    t_start: float  # lap-relative seconds, car-frame Time axis (see note)
    t_end: float
    d_start: float  # metres (native car Distance)
    d_end: float
    dt: float       # interval length in seconds
    ratio: float    # dt / median dt


class NativeAcquisitionMeta(CamelCaseModel):
    """Per-lap native acquisition statistics."""
    schema_version: str
    acquisition_mode: str
    n_car: int
    n_pos: int
    median_dt_car: float
    median_dt_pos: float
    gap_dt_multiplier: float
    gap_threshold_s: float
    n_gaps: int
    lib_versions: dict


class TelemetryMetaResponse(CamelCaseModel):
    """Native acquisition metadata for one driver's lap (GET /telemetry/meta)."""
    driver: str
    lap_number: int
    gaps: List[GapInterval]
    meta: NativeAcquisitionMeta


class SectorTime(CamelCaseModel):
    """Sector times for a driver."""
    driver: str
    sector1: float  # seconds (renamed from sector_1)
    sector2: float  # seconds (renamed from sector_2)
    sector3: float  # seconds (renamed from sector_3)
    total_time: float  # seconds


class SectorInfo(CamelCaseModel):
    """Circuit sector information."""
    sector_number: int
    start_distance: float
    end_distance: float


class DRSZone(CamelCaseModel):
    """DRS zone information."""
    zone_number: int
    detection_point: float
    activation_point: float
    end_point: float
    wrap_around: Optional[bool] = None  # True if zone crosses start/finish line


class CornerInfo(CamelCaseModel):
    """Corner information for track layout."""
    corner_number: int
    distance: float
    type: str  # 'left' or 'right'
    name: Optional[str] = None


class TrackResponse(CamelCaseModel):
    """Track information response."""
    circuit_name: str
    round: int
    season: int
    length: float  # meters
    sectors: List[SectorInfo]
    drs_zones: List[DRSZone]
    corners: Optional[List[CornerInfo]] = None
    elevation_data: Optional[List[dict]] = None


# =============================================================================
# Race Page DTOs (Phase 1)
# =============================================================================

LapClassificationType = Literal[
    "RACING", "IN_LAP", "OUT_LAP", "SAFETY_CAR",
    "VSC", "RED_FLAG", "FORMATION", "ANOMALY"
]


class RaceLapResponse(CamelCaseModel):
    """Single race lap with classification and enrichment."""
    lap_number: int
    driver: str
    team: Optional[str] = None
    position: Optional[int] = None
    lap_time: Optional[float] = None
    sector1_time: Optional[float] = None
    sector2_time: Optional[float] = None
    sector3_time: Optional[float] = None
    compound: Optional[str] = None
    tyre_life: Optional[int] = None
    stint: Optional[int] = None
    classification: LapClassificationType = "RACING"
    is_warm_up: bool = False
    fuel_corrected_time: Optional[float] = None
    in_traffic: bool = False
    gap_to_car_ahead: Optional[float] = None
    is_personal_best: bool = False
    track_status: Optional[str] = None
    pit_in_time: Optional[float] = None
    pit_out_time: Optional[float] = None
    cumulative_time: Optional[float] = None


class StintResponse(CamelCaseModel):
    """Stint summary for a driver."""
    driver: str
    team: Optional[str] = None
    stint_number: int
    compound: Optional[str] = None
    start_lap: int
    end_lap: int
    lap_count: int


class PitStopResponse(CamelCaseModel):
    """Single pit stop event."""
    driver: str
    team: Optional[str] = None
    stop_number: int
    lap_number: int
    pit_lane_time: Optional[float] = None
    is_anomaly: bool = False


# =============================================================================
# Race Page DTOs (Phase 4: Pit Stop Analysis)
# =============================================================================


class TeamPitStopAggregate(CamelCaseModel):
    """Per-team pit stop statistics."""
    team: str
    average_pit_lane_time: float
    stop_count: int
    consistency: Optional[float] = None        # IQR (≥3 stops) or abs diff (2 stops)
    consistency_type: Optional[str] = None     # 'iqr' | 'range' | null


class DriverPitStopAggregate(CamelCaseModel):
    """Per-driver pit stop statistics."""
    driver: str
    team: str
    average_pit_lane_time: float
    stop_count: int


class GapToFastest(CamelCaseModel):
    """Gap to the fastest team's average pit lane time."""
    team: str
    gap_to_fastest: float


class PitStopQuickestInsight(CamelCaseModel):
    """Insight data for the 'Quickest on Average' template card."""
    team: str
    average_time: float
    percentage_faster: float
    grid_average: float


class PitStopConsistencyInsight(CamelCaseModel):
    """Insight data for the 'Most Consistent' template card."""
    team: str
    consistency: float                         # The spread value (seconds)
    consistency_type: str                      # 'iqr' or 'range'


class PitStopInsights(CamelCaseModel):
    """Container for pit stop insight data."""
    quickest: Optional[PitStopQuickestInsight] = None
    most_consistent: Optional[PitStopConsistencyInsight] = None


class AnomalyNote(CamelCaseModel):
    """A flagged anomalous pit stop excluded from averages."""
    driver: str
    team: str
    stop_number: int
    lap_number: int
    pit_lane_time: Optional[float] = None


class PitStopAnalysisResponse(CamelCaseModel):
    """Complete response for the /race/pit-stops endpoint."""
    stops: List[PitStopResponse]
    team_aggregates: List[TeamPitStopAggregate]
    driver_aggregates: List[DriverPitStopAggregate]
    gap_to_fastest: List[GapToFastest]
    grid_average: float
    fastest_team: Optional[str] = None
    insights: PitStopInsights
    anomaly_notes: List[AnomalyNote]


class DriverPaceResponse(CamelCaseModel):
    """Pre-computed pace statistics for a single driver."""
    driver: str
    team: Optional[str] = None
    min_time: float
    q1: float
    median: float
    mean: float
    q3: float
    max_time: float
    outliers: List[float]
    gap_to_fastest: float
    tyre_strategy: List[str]
    consistency_score: Optional[float] = None
    laps_in_traffic: int = 0
    total_racing_laps: int
    finishing_position: Optional[int] = None
    status: Optional[str] = None


class RacePaceResponse(CamelCaseModel):
    """Complete race pace response."""
    session_id: str
    drivers: List[DriverPaceResponse]


# =============================================================================
# Race Page DTOs (Phase 3: Tyre Degradation)
# =============================================================================


class RegressionLine(CamelCaseModel):
    """Pre-computed regression line coordinates for frontend rendering."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    slope: float            # Gradient in s/lap (the wear rate)
    intercept: float        # Y-intercept (theoretical fresh-tyre pace)
    r_squared: float        # Coefficient of determination


class DegradationDataPoint(CamelCaseModel):
    """Single lap data point for the degradation scatter plot."""
    tyre_age: int
    fuel_adjusted_time: float
    raw_time: float
    lap_number: int
    driver: str
    team: str
    stint_number: int


class DriverDegradationData(CamelCaseModel):
    """Degradation data for one driver (or team in team mode) on one compound."""
    identifier: str                                     # Driver abbreviation or team name
    team: str                                           # Team name (same as identifier in team mode)
    data_points: List[DegradationDataPoint]
    regression: Optional[RegressionLine] = None         # None if < 7 usable laps
    wear_rate: Optional[float] = None                   # slope value, None if insufficient data
    usable_lap_count: int
    total_stint_laps: int
    warm_up_laps_excluded: int


class CompoundDegradation(CamelCaseModel):
    """Degradation data for one compound across all drivers/teams."""
    compound: str
    drivers: List[DriverDegradationData]


class TyreDegradationResponse(CamelCaseModel):
    """Complete response for the tyre degradation endpoint."""
    session_id: str
    mode: str                                           # 'driver' or 'team'
    compounds: List[CompoundDegradation]
    compound_order: List[str]                           # Display order: hardest first


# =============================================================================
# Race Page DTOs (Phase 5: Team Performance Quadrant)
# =============================================================================


class TeamPerformanceData(CamelCaseModel):
    """Per-team top speed and mean speed with deltas from field average."""
    team: str
    top_speed: float                                    # km/h (mean of SpeedST)
    mean_speed: float                                   # km/h (track_length / fuel_corrected_time * 3.6)
    top_speed_delta: float                              # km/h vs field average
    mean_speed_delta: float                             # km/h vs field average


class TeamPerformanceFieldAverages(CamelCaseModel):
    """Field-level averages for crosshair reference lines."""
    top_speed: float
    mean_speed: float


class TeamPerfInsightEntry(CamelCaseModel):
    """Single insight entry: which team, what value, how much above field."""
    team: str
    value: float
    delta: float


class TeamPerformanceInsights(CamelCaseModel):
    """Deterministic insight data for template-based cards."""
    fastest_on_straights: Optional[TeamPerfInsightEntry] = None
    highest_mean_speed: Optional[TeamPerfInsightEntry] = None


class TeamPerformanceResponse(CamelCaseModel):
    """Complete response for the /race/team-performance endpoint."""
    session_id: str
    teams: List[TeamPerformanceData]
    field_averages: TeamPerformanceFieldAverages
    insights: TeamPerformanceInsights


# =============================================================================
# Practice Page DTOs (Phase 1: Long Run Pace)
# =============================================================================


class PracticeStintStats(CamelCaseModel):
    """Box plot and distribution statistics for a single practice stint."""
    lowerfence: float
    q1: float
    median: float
    q3: float
    upperfence: float
    mean: float
    std_dev: float


class PracticeLapPoint(CamelCaseModel):
    """Single lap data point within a long-run stint, for violin overlay."""
    lap_number: int
    lap_time: float
    compound: Optional[str] = None
    tyre_life: Optional[int] = None
    in_traffic: bool = False


class PracticeLongRunStint(CamelCaseModel):
    """One long-run stint with pre-computed stats and enrichments."""
    driver: str
    team: Optional[str] = None
    stint_number: int
    display_stint_number: int = 1
    compound: Optional[str] = None
    valid_lap_count: int
    total_lap_count: int
    stats: PracticeStintStats
    average_time: float
    gap_to_fastest: float
    degradation_hint: Optional[float] = None
    clean_air_pct: float
    lap_times: List['PracticeLapPoint'] = []


class PracticeLongRunResponse(CamelCaseModel):
    """Complete response for the /practice/long-runs endpoint."""
    session_id: str
    fuel_corrected: bool
    stints: List[PracticeLongRunStint]
    session_best_average: Optional[float] = None
    total_long_runs_detected: int = 0
    stints_filtered_count: int = 0


class PracticeSessionsResponse(CamelCaseModel):
    """Available practice sessions for a race weekend."""
    year: int
    round_num: int
    sessions: List[str]


# =============================================================================
# Practice Page DTOs (Phase 2: Short Run / Best Lap)
# =============================================================================


class PracticeShortRunDriver(CamelCaseModel):
    """Per-driver best lap result from short run stints."""
    driver: str
    team: str
    best_lap_time: float
    compound: str
    tyre_life: int
    gap_to_p1: float
    stint_count: int
    position: int
    # Session verification fields (None when verification unavailable)
    session_best_time: Optional[float] = None
    session_best_source: Optional[str] = None  # 'fastf1_flag' | 'computed_minimum'
    session_best_from_short_run: Optional[bool] = None
    session_best_compound: Optional[str] = None


class PracticeShortRunResponse(CamelCaseModel):
    """Response for GET /practice/short-runs endpoint."""
    session_id: str
    fuel_corrected: bool
    drivers: List[PracticeShortRunDriver]
    session_best_lap: Optional[float] = None
    total_drivers: int
    verification_available: bool = False


# =============================================================================
# Practice Page DTOs (Sector Analysis)
# =============================================================================


class PracticeSectorDriver(CamelCaseModel):
    """Per-driver sector breakdown from session-best lap + best individual sectors."""
    driver: str
    team: str
    position: int
    lap_time: float  # Session-best lap time
    # Sectors from session-best lap
    sector1: Optional[float] = None
    sector2: Optional[float] = None
    sector3: Optional[float] = None
    # Best individual sectors (may come from different laps)
    best_sector1: Optional[float] = None
    best_sector2: Optional[float] = None
    best_sector3: Optional[float] = None
    # Theoretical best (sum of best individual sectors)
    theoretical_best: Optional[float] = None
    potential_gain: Optional[float] = None  # lap_time - theoretical_best
    # Compound on session-best lap
    compound: Optional[str] = None


class PracticeSectorSummary(CamelCaseModel):
    """Session-level sector summary."""
    fastest_sector1: Optional[float] = None
    fastest_sector1_driver: Optional[str] = None
    fastest_sector2: Optional[float] = None
    fastest_sector2_driver: Optional[str] = None
    fastest_sector3: Optional[float] = None
    fastest_sector3_driver: Optional[str] = None
    theoretical_best_time: Optional[float] = None
    actual_best_time: Optional[float] = None
    theoretical_gain: Optional[float] = None


class PracticeSpeedTrapDriver(CamelCaseModel):
    """Per-driver maximum speed trap readings."""
    driver: str
    team: str
    speed_trap: Optional[float] = None
    speed_i1: Optional[float] = None
    speed_i2: Optional[float] = None
    speed_fl: Optional[float] = None


class PracticeSectorAnalysisResponse(CamelCaseModel):
    """Complete response for GET /practice/sector-analysis."""
    session_id: str
    drivers: List[PracticeSectorDriver]
    summary: PracticeSectorSummary
    speed_traps: List[PracticeSpeedTrapDriver]
    total_drivers: int


# =============================================================================
# Practice Page DTOs (Phase 3: Session Progression)
# =============================================================================


class PracticeProgressionEntry(CamelCaseModel):
    """A single driver's best lap data for one FP session."""
    session: str                    # 'FP1', 'FP2', or 'FP3'
    best_lap_time: float            # Raw lap time in seconds
    compound: str                   # Tyre compound used on best lap
    tyre_life: int                  # Tyre age at best lap
    gap_to_session_best: float      # Seconds behind session fastest (0.0 for P1)
    source: str                     # 'fastf1_flag' | 'computed_minimum'


class PracticeProgressionDriver(CamelCaseModel):
    """All session entries for one driver across the practice weekend."""
    driver: str                     # 3-letter abbreviation e.g. 'VER'
    team: str                       # Full team name e.g. 'Red Bull Racing'
    sessions: List[PracticeProgressionEntry]  # 1-3 entries depending on availability


class PracticeProgressionResponse(CamelCaseModel):
    """Response for GET /practice/progression — full weekend view."""
    year: int
    round_num: int
    available_sessions: List[str]   # e.g. ['FP1', 'FP2', 'FP3'] or ['FP1']
    is_sprint_weekend: bool         # True if only FP1 available
    drivers: List[PracticeProgressionDriver]
    total_drivers: int
