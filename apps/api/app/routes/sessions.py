from fastapi import APIRouter, Query
from typing import Optional
from app.models.dto import SessionResponse, SessionType
from app.services.data_service import get_data_service

router = APIRouter()


@router.get("", response_model=list[SessionResponse])
async def get_sessions(
    season: int = Query(..., description="F1 season year"),
    round: int = Query(..., description="Race round number"),
):
    """
    Get all sessions for a specific race weekend.
    Handles both traditional and sprint weekend formats.
    """
    service = get_data_service()
    sessions = await service.get_sessions(season, round)
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_by_id(session_id: str):
    """
    Get detailed information about a specific session.
    """
    service = get_data_service()
    session = await service.get_session_by_id(session_id)
    return session

