from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


SessionType = Literal[
    "Practice", "Qualifying", "Sprint Qualifying", "Sprint", "Race"
]


class SessionResponse(BaseModel):
    """Session information response."""
    session_id: str
    session_type: SessionType
    session_name: str
    season: int
    round: int
    is_sprint_weekend: bool
    date: Optional[datetime] = None
    circuit_name: Optional[str] = None


class LapResponse(BaseModel):
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


class TelemetryResponse(BaseModel):
    """
    Telemetry data response with flat arrays for performance.
    All arrays are distance-indexed and have the same length.
    """
    driver: str
    lap_number: int
    distance: List[float]
    speed: List[float]
    throttle: List[float]
    brake: List[float]
    gear: List[int]
    rpm: Optional[List[int]] = None
    drs: Optional[List[int]] = None


class DeltaResponse(BaseModel):
    """Time delta analysis between two drivers."""
    reference_driver: str
    compare_driver: str
    distance: List[float]
    delta: List[float]  # seconds, positive = compare driver is slower


class SectorTime(BaseModel):
    """Sector times for a driver."""
    driver: str
    sector_1: float  # seconds
    sector_2: float  # seconds
    sector_3: float  # seconds
    total_time: float  # seconds


class SectorInfo(BaseModel):
    """Circuit sector information."""
    sector_number: int
    start_distance: float
    end_distance: float


class DRSZone(BaseModel):
    """DRS zone information."""
    zone_number: int
    detection_point: float
    activation_point: float
    end_point: float


class TrackResponse(BaseModel):
    """Track information response."""
    circuit_name: str
    round: int
    season: int
    length: float  # meters
    sectors: List[SectorInfo]
    drs_zones: List[DRSZone]
    corners: Optional[List[dict]] = None
    elevation_data: Optional[List[dict]] = None

