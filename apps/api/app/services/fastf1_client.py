import fastf1
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.core.cache import enable_cache
from app.core.config import settings
from app.models.dto import (
    SessionResponse,
    LapResponse,
    TelemetryResponse,
    TrackResponse,
    DeltaResponse,
    SectorTime,
    SectorInfo,
    DRSZone,
    CornerInfo,
)
from app.services.transforms import calculate_delta, downsample_telemetry

# Enable cache on module import
enable_cache()

# Static track data directory
TRACK_DATA_DIR = Path(__file__).parent.parent / "data" / "tracks"


class FastF1Client:
    """Client for interacting with FastF1 library."""
    
    def __init__(self):
        self.downsample_threshold = settings.DOWNSAMPLE_THRESHOLD
    
    async def get_sessions(self, season: int, round: int) -> List[SessionResponse]:
        """
        Get all sessions for a race weekend.
        Handles both traditional and sprint formats.
        """
        try:
            event = fastf1.get_event(season, round)
            
            # Determine if sprint weekend
            is_sprint = hasattr(event, 'is_sprint_weekend') and event.is_sprint_weekend
            
            sessions = []
            
            if is_sprint:
                # Sprint weekend: FP1, Sprint Qualifying, Sprint, Qualifying, Race
                session_names = ['FP1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race']
            else:
                # Traditional weekend: FP1, FP2, FP3, Qualifying, Race
                session_names = ['FP1', 'FP2', 'FP3', 'Qualifying', 'Race']
            
            for session_name in session_names:
                try:
                    session_type = self._get_session_type(session_name)
                    sessions.append(
                        SessionResponse(
                            session_id=f"{season}_{round}_{session_name.replace(' ', '_')}",
                            session_type=session_type,
                            session_name=session_name,
                            season=season,
                            round=round,
                            is_sprint_weekend=is_sprint,
                            date=datetime.now(),  # FastF1 v3+ has session dates
                            circuit_name=event.EventName if hasattr(event, 'EventName') else None,
                        )
                    )
                except Exception as e:
                    print(f"Skipping session {session_name}: {e}")
                    continue
            
            return sessions
        
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return []
    
    def _get_session_type(self, session_name: str):
        """Map session name to session type."""
        if 'FP' in session_name or 'Practice' in session_name:
            return "Practice"
        elif session_name == 'Sprint':
            return "Sprint"
        elif 'Sprint' in session_name and 'Qualifying' in session_name:
            return "Sprint Qualifying"
        elif 'Qualifying' in session_name:
            return "Qualifying"
        elif 'Race' in session_name:
            return "Race"
        return "Practice"
    
    async def get_session_by_id(self, session_id: str) -> SessionResponse:
        """Get detailed session information."""
        # Parse session_id: format is "2024_1_Qualifying"
        parts = session_id.split('_')
        season = int(parts[0])
        round_num = int(parts[1])
        session_name = '_'.join(parts[2:]).replace('_', ' ')
        
        sessions = await self.get_sessions(season, round_num)
        for session in sessions:
            if session.session_name == session_name:
                return session
        
        raise ValueError(f"Session not found: {session_id}")
    
    async def get_laps(self, session: str, drivers: List[str]) -> List[LapResponse]:
        """Get lap data for specified drivers, focusing on fastest laps."""
        try:
            # Parse session identifier
            parts = session.split('_')
            season = int(parts[0])
            round_num = int(parts[1])
            session_name = '_'.join(parts[2:]).replace('_', ' ')
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            lap_responses = []
            
            for driver in drivers:
                # Get driver's fastest lap
                driver_laps = race_session.laps.pick_driver(driver)
                if len(driver_laps) == 0:
                    continue
                
                fastest_lap = driver_laps.pick_fastest()
                
                if fastest_lap is not None and not fastest_lap.empty:
                    lap_responses.append(
                        LapResponse(
                            lap_number=int(fastest_lap['LapNumber']),
                            driver=driver,
                            lap_time=float(fastest_lap['LapTime'].total_seconds()),
                            sector1_time=float(fastest_lap['Sector1Time'].total_seconds()) if pd.notna(fastest_lap['Sector1Time']) else None,
                            sector2_time=float(fastest_lap['Sector2Time'].total_seconds()) if pd.notna(fastest_lap['Sector2Time']) else None,
                            sector3_time=float(fastest_lap['Sector3Time'].total_seconds()) if pd.notna(fastest_lap['Sector3Time']) else None,
                            compound=str(fastest_lap['Compound']) if pd.notna(fastest_lap['Compound']) else None,
                            tyre_age=int(fastest_lap['TyreLife']) if pd.notna(fastest_lap['TyreLife']) else None,
                            is_personal_best=True,
                        )
                    )
            
            return lap_responses
        
        except Exception as e:
            print(f"Error loading laps: {e}")
            return []
    
    async def get_fastest_laps(self, session: str):
        """Get fastest lap for each driver in a session."""
        return await self.get_laps(session, [])  # Empty list returns all drivers
    
    async def get_telemetry(
        self, session: str, drivers: List[str], lap_type: str = "fastest"
    ) -> List[TelemetryResponse]:
        """Get telemetry data for specified drivers."""
        try:
            # Parse session identifier
            parts = session.split('_')
            season = int(parts[0])
            round_num = int(parts[1])
            session_name = '_'.join(parts[2:]).replace('_', ' ')
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            telemetry_responses = []
            
            for driver in drivers:
                # Get driver's fastest lap
                driver_laps = race_session.laps.pick_driver(driver)
                if len(driver_laps) == 0:
                    continue
                
                fastest_lap = driver_laps.pick_fastest()
                
                if fastest_lap is not None and not fastest_lap.empty:
                    # Get telemetry
                    telemetry = fastest_lap.get_telemetry()
                    
                    if telemetry is not None and len(telemetry) > 0:
                        # Extract arrays
                        distance = telemetry['Distance'].values
                        speed = telemetry['Speed'].values
                        throttle = telemetry['Throttle'].values
                        brake = telemetry['Brake'].values
                        gear = telemetry['nGear'].values.astype(int)
                        rpm = telemetry['RPM'].values.astype(int) if 'RPM' in telemetry.columns else None
                        drs = telemetry['DRS'].values.astype(int) if 'DRS' in telemetry.columns else None
                        
                        # Downsample if needed
                        if len(distance) > self.downsample_threshold:
                            if rpm is not None and drs is not None:
                                distance, speed, throttle, brake, gear, rpm, drs = downsample_telemetry(
                                    distance, speed, throttle, brake, gear, rpm, drs,
                                    max_points=self.downsample_threshold
                                )
                            else:
                                distance, speed, throttle, brake, gear = downsample_telemetry(
                                    distance, speed, throttle, brake, gear,
                                    max_points=self.downsample_threshold
                                )
                        
                        telemetry_responses.append(
                            TelemetryResponse(
                                driver=driver,
                                lap_number=int(fastest_lap['LapNumber']),
                                distance=distance.tolist(),
                                speed=speed.tolist(),
                                throttle=throttle.tolist(),
                                brake=brake.tolist(),
                                gear=gear.tolist(),
                                rpm=rpm.tolist() if rpm is not None else None,
                                drs=drs.tolist() if drs is not None else None,
                            )
                        )
            
            return telemetry_responses
        
        except Exception as e:
            print(f"Error loading telemetry: {e}")
            return []
    
    async def get_delta_analysis(
        self, session: str, reference_driver: str, compare_drivers: List[str]
    ) -> List[DeltaResponse]:
        """Calculate delta time between drivers."""
        try:
            # Parse session identifier
            parts = session.split('_')
            season = int(parts[0])
            round_num = int(parts[1])
            session_name = '_'.join(parts[2:]).replace('_', ' ')
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            # Get reference driver's fastest lap telemetry
            ref_laps = race_session.laps.pick_driver(reference_driver)
            if len(ref_laps) == 0:
                return []
            
            ref_fastest = ref_laps.pick_fastest()
            ref_telemetry = ref_fastest.get_telemetry()
            
            delta_responses = []
            
            for compare_driver in compare_drivers:
                # Get comparison driver's fastest lap telemetry
                comp_laps = race_session.laps.pick_driver(compare_driver)
                if len(comp_laps) == 0:
                    continue
                
                comp_fastest = comp_laps.pick_fastest()
                comp_telemetry = comp_fastest.get_telemetry()
                
                # Calculate delta
                distance, delta = calculate_delta(ref_telemetry, comp_telemetry)
                
                delta_responses.append(
                    DeltaResponse(
                        reference_driver=reference_driver,
                        compare_driver=compare_driver,
                        distance=distance.tolist(),
                        delta=delta.tolist(),
                    )
                )
            
            return delta_responses
        
        except Exception as e:
            print(f"Error calculating delta: {e}")
            return []
    
    async def get_sectors(self, session: str, drivers: List[str]) -> List[SectorTime]:
        """Get sector times for specified drivers."""
        laps = await self.get_laps(session, drivers)
        
        sector_times = []
        for lap in laps:
            if lap.sector1_time and lap.sector2_time and lap.sector3_time:
                sector_times.append(
                    SectorTime(
                        driver=lap.driver,
                        sector1=lap.sector1_time,
                        sector2=lap.sector2_time,
                        sector3=lap.sector3_time,
                        total_time=lap.lap_time,
                    )
                )
        
        return sector_times
    
    async def get_track_info(self, season: int, round: int) -> TrackResponse:
        """Get track layout and information from static data with FastF1 fallback."""
        try:
            # Try to load from static track data
            mapping_path = TRACK_DATA_DIR / "circuit_mapping.json"
            if not mapping_path.exists():
                raise FileNotFoundError("Circuit mapping not found")
            
            with open(mapping_path) as f:
                mapping = json.load(f)
            
            circuit_id = mapping.get(str(season), {}).get(str(round))
            if not circuit_id:
                raise KeyError(f"No circuit mapping for {season}/{round}")
            
            track_path = TRACK_DATA_DIR / f"{circuit_id}.json"
            if not track_path.exists():
                raise FileNotFoundError(f"Track data not found: {circuit_id}")
            
            with open(track_path) as f:
                track_data = json.load(f)
            
            # Build sectors from static data
            sectors = [
                SectorInfo(
                    sector_number=s["sectorNumber"],
                    start_distance=s["startDistance"],
                    end_distance=s["endDistance"]
                )
                for s in track_data.get("sectors", [])
            ]
            
            # Build DRS zones from static data
            drs_zones = [
                DRSZone(
                    zone_number=z["zoneNumber"],
                    detection_point=z["detectionPoint"],
                    activation_point=z["activationPoint"],
                    end_point=z["endPoint"]
                )
                for z in track_data.get("drsZones", [])
            ]
            
            # Build corners from static data
            corners = [
                CornerInfo(
                    corner_number=c["cornerNumber"],
                    distance=c["distance"],
                    type=c["type"],
                    name=c.get("name")
                )
                for c in track_data.get("corners", [])
            ] if track_data.get("corners") else None
            
            return TrackResponse(
                circuit_name=track_data.get("circuitName", "Unknown"),
                round=round,
                season=season,
                length=float(track_data.get("length", 5000)),
                sectors=sectors,
                drs_zones=drs_zones,
                corners=corners,
            )
            
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Track data not available: {e}, falling back to FastF1")
            # Fallback to basic FastF1 event info
            try:
                event = fastf1.get_event(season, round)
                circuit_name = event.EventName if hasattr(event, 'EventName') else "Unknown"
            except Exception:
                circuit_name = "Unknown"
            
            return TrackResponse(
                circuit_name=circuit_name,
                round=round,
                season=season,
                length=5000.0,
                sectors=[],
                drs_zones=[],
                corners=None,
            )

