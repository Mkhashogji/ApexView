from fastapi import APIRouter, Path, Query
from app.models.dto import TrackResponse
from app.services.data_service import get_data_service

router = APIRouter()


@router.get("/{round}", response_model=TrackResponse)
async def get_track_info(
    round: int = Path(..., description="Race round number"),
    season: int = Query(2025, description="Season year"),
):
    """
    Get track information including layout, sectors, DRS zones, and elevation.
    """
    service = get_data_service()
    track_info = await service.get_track_info(season, round)
    return track_info

