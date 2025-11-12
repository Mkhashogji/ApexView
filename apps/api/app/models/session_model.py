from pydantic import BaseModel
from typing import List, Literal


SessionFormat = Literal["traditional", "sprint"]


class TraditionalWeekend(BaseModel):
    """Traditional race weekend session structure."""
    format: Literal["traditional"] = "traditional"
    sessions: List[str] = ["FP1", "FP2", "FP3", "Q", "R"]


class SprintWeekend(BaseModel):
    """Sprint race weekend session structure."""
    format: Literal["sprint"] = "sprint"
    sessions: List[str] = ["FP1", "SQ", "S", "Q", "R"]


class SessionModel(BaseModel):
    """Session structure model for a race weekend."""
    season: int
    round: int
    circuit: str
    format: SessionFormat
    
    def get_sessions(self) -> List[str]:
        """Get list of session identifiers for this weekend."""
        if self.format == "traditional":
            return ["FP1", "FP2", "FP3", "Q", "R"]
        else:  # sprint
            return ["FP1", "SQ", "S", "Q", "R"]
    
    def is_practice_session(self, session: str) -> bool:
        """Check if a session is a practice session."""
        return session.startswith("FP")
    
    def is_qualifying_session(self, session: str) -> bool:
        """Check if a session is a qualifying session."""
        return session in ["Q", "SQ"]
    
    def is_race_session(self, session: str) -> bool:
        """Check if a session is a race session."""
        return session in ["R", "S"]

