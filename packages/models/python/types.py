from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

SessionType = Literal["Practice", "Qualifying", "Sprint Qualifying", "Sprint", "Race"]
TyreCompound = Literal["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]


class Session(BaseModel):
    session_id: str
    session_type: SessionType
    session_name: str
    season: int
    round: int
    is_sprint_weekend: bool
    date: Optional[datetime] = None
    circuit_name: Optional[str] = None


class Lap(BaseModel):
    lap_number: int
    driver: str
    lap_time: float
    sector1_time: Optional[float] = None
    sector2_time: Optional[float] = None
    sector3_time: Optional[float] = None
    compound: Optional[TyreCompound] = None
    tyre_age: Optional[int] = None
    is_personal_best: bool = False


class TelemetryPoint(BaseModel):
    distance: float
    speed: float
    throttle: float
    brake: float
    gear: int
    rpm: Optional[int] = None
    drs: Optional[int] = None


class Telemetry(BaseModel):
    driver: str
    lap_number: int
    data: List[TelemetryPoint]

