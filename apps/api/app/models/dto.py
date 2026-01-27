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
