from fastapi import APIRouter, Path
from app.models.dto import TrackResponse
from app.services.fastf1_client import FastF1Client

router = APIRouter()
client = FastF1Client()


@router.get("/{round}", response_model=TrackResponse)
async def get_track_info(
    round: int = Path(..., description="Race round number"),
    season: int = 2025,
):
    """
    Get track information including layout, sectors, DRS zones, and elevation.
    """
    track_info = await client.get_track_info(season, round)
    return track_info

