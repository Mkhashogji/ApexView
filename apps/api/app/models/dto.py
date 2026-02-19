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
