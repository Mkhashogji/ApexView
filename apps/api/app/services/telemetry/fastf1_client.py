import fastf1
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Literal
from datetime import datetime

logger = logging.getLogger(__name__)
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
from app.services.telemetry.transforms import calculate_delta, downsample_telemetry
from app.services.cache.parquet_cache import parquet_cache

# Enable cache on module import
enable_cache()

# Static track data directory
TRACK_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "tracks"


class FastF1Client:
    """Client for interacting with FastF1 library with Parquet caching."""
    
    def __init__(self):
        self.downsample_threshold = settings.DOWNSAMPLE_THRESHOLD
        self.cache = parquet_cache
    
    def _filter_laps_by_session_part(
        self, 
        laps, 
        session_part: Optional[str] = None,
        session_status = None
    ):
        """
        Filter laps to only include those from specified qualifying part (Q1, Q2, or Q3).
        
        Uses either:
        1. Q1/Q2/Q3 boolean columns if available (older FastF1 data)
        2. Time-based filtering using session_status boundaries (2025+ data)
        
        Args:
            laps: FastF1 Laps object
            session_part: Optional session part filter ('Q1', 'Q2', or 'Q3')
            session_status: Optional session status DataFrame for time-based filtering
            
        Returns:
            Filtered laps, or original laps if no filter specified
        """
        if not session_part:
            return laps
        
        session_part_upper = session_part.upper()
        if session_part_upper not in ['Q1', 'Q2', 'Q3']:
            return laps
        
        # Try method 1: FastF1 boolean columns (if available)
        if session_part_upper in laps.columns:
            filtered = laps[laps[session_part_upper] == True]
            if len(filtered) > 0:
                return filtered
        
        # Method 2: Time-based filtering using session status
        if session_status is not None and 'LapStartTime' in laps.columns:
            try:
                # Find session boundaries from session_status
                # Sessions alternate: Started -> Finished for each Q1, Q2, Q3
                started_times = session_status[session_status['Status'] == 'Started']['Time'].values
                finished_times = session_status[session_status['Status'] == 'Finished']['Time'].values
                
                if len(started_times) >= 3 and len(finished_times) >= 3:
                    # Q1 = index 0, Q2 = index 1, Q3 = index 2
                    part_idx = {'Q1': 0, 'Q2': 1, 'Q3': 2}[session_part_upper]
                    
                    start_time = pd.Timedelta(started_times[part_idx])
                    end_time = pd.Timedelta(finished_times[part_idx])
                    
                    # Filter laps by start time within the session part
                    filtered = laps[
                        (laps['LapStartTime'] >= start_time) & 
                        (laps['LapStartTime'] <= end_time)
                    ]
                    
                    if len(filtered) > 0:
                        return filtered
                    else:
                        # Driver didn't participate in this session part
                        return laps.iloc[0:0]
            except Exception as e:
                logger.warning(f"Time-based filtering failed: {e}")

        # Fallback: return all laps if filtering fails
        return laps

    def _filter_valid_laps(self, laps) -> "pd.DataFrame":
        """
        Filter out invalid laps to ensure data quality.

        Removes:
        - Laps deleted for track limit violations
        - Pit in laps (entry to pit lane)
        - Pit out laps (exit from pit lane)

        This ensures only valid, representative laps are used for analysis.

        Args:
            laps: FastF1 Laps DataFrame

        Returns:
            Filtered DataFrame with only valid laps.
            Falls back to original if all laps would be filtered.
        """
        if laps is None or len(laps) == 0:
            return laps

        filtered = laps.copy()
        original_count = len(filtered)

        # Step 1: Filter deleted laps (track limits violations)
        if 'Deleted' in filtered.columns:
            # Keep laps where Deleted is False OR NaN (older data compatibility)
            deleted_mask = (filtered['Deleted'] == False) | (filtered['Deleted'].isna())
            filtered = filtered[deleted_mask]
            deleted_count = original_count - len(filtered)
            if deleted_count > 0:
                logger.debug(f"Filtered {deleted_count} deleted laps")

        # Step 2: Filter pit in laps
        if 'PitInTime' in filtered.columns:
            pre_pit_count = len(filtered)
            filtered = filtered[filtered['PitInTime'].isna()]
            pit_in_removed = pre_pit_count - len(filtered)
            if pit_in_removed > 0:
                logger.debug(f"Filtered {pit_in_removed} pit-in laps")

        # Step 3: Filter pit out laps
        if 'PitOutTime' in filtered.columns:
            pre_pit_count = len(filtered)
            filtered = filtered[filtered['PitOutTime'].isna()]
            pit_out_removed = pre_pit_count - len(filtered)
            if pit_out_removed > 0:
                logger.debug(f"Filtered {pit_out_removed} pit-out laps")

        # Step 4: Fallback - if all laps filtered, return original with warning
        if len(filtered) == 0:
            logger.warning(
                f"All {original_count} laps were invalid (deleted/pit). "
                f"Falling back to unfiltered laps."
            )
            return laps

        final_count = len(filtered)
        if final_count < original_count:
            logger.info(
                f"Lap filtering: {original_count} -> {final_count} valid laps "
                f"({original_count - final_count} removed)"
            )

        return filtered
    
    def _parse_session_id(self, session: str):
        """
        Parse session identifier into components.
        
        Args:
            session: Session ID (e.g., "2025_24_Qualifying")
            
        Returns:
            Tuple of (season, round_num, session_name)
        """
        parts = session.split('_')
        season = int(parts[0])
        round_num = int(parts[1])
        session_name = '_'.join(parts[2:]).replace('_', ' ')
        return season, round_num, session_name
    
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
                    logger.debug(f"Skipping session {session_name}: {e}")
                    continue
            
            return sessions
        
        except Exception as e:
            logger.error(f"Error loading sessions: {e}", exc_info=True)
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
        """Get lap data for specified drivers, focusing on fastest laps with Parquet cache."""
        try:
            # Try Parquet cache first
            drivers_str = '_'.join(sorted(drivers)) if drivers else 'all'
            cached_df = self.cache.read(session, "laps", drivers=drivers_str)
            
            if cached_df is not None:
                # Convert cached DataFrame to LapResponse objects
                lap_responses = []
                for _, row in cached_df.iterrows():
                    lap_responses.append(
                        LapResponse(
                            lap_number=int(row['lap_number']),
                            driver=row['driver'],
                            lap_time=float(row['lap_time']),
                            sector1_time=float(row['sector1_time']) if pd.notna(row.get('sector1_time')) else None,
                            sector2_time=float(row['sector2_time']) if pd.notna(row.get('sector2_time')) else None,
                            sector3_time=float(row['sector3_time']) if pd.notna(row.get('sector3_time')) else None,
                            compound=str(row['compound']) if pd.notna(row.get('compound')) else None,
                            tyre_age=int(row['tyre_age']) if pd.notna(row.get('tyre_age')) else None,
                            is_personal_best=bool(row.get('is_personal_best', True)),
                        )
                    )
                logger.info(f"Loaded laps from Parquet cache for {session}")
                return lap_responses
            
            # Cache miss - fetch from FastF1
            # Parse session identifier
            parts = session.split('_')
            season = int(parts[0])
            round_num = int(parts[1])
            session_name = '_'.join(parts[2:]).replace('_', ' ')
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            lap_responses = []
            lap_data_for_cache = []
            
            for driver in drivers:
                # Get driver's fastest lap
                driver_laps = race_session.laps.pick_driver(driver)
                if len(driver_laps) == 0:
                    continue

                # Filter out deleted and pit laps for data quality
                valid_laps = self._filter_valid_laps(driver_laps)
                if len(valid_laps) == 0:
                    logger.warning(f"No valid laps for driver {driver} after filtering")
                    continue

                fastest_lap = valid_laps.pick_fastest()
                
                if fastest_lap is not None and not fastest_lap.empty:
                    lap_response = LapResponse(
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
                    lap_responses.append(lap_response)
                    
                    # Prepare for cache
                    lap_data_for_cache.append({
                        'lap_number': lap_response.lap_number,
                        'driver': lap_response.driver,
                        'lap_time': lap_response.lap_time,
                        'sector1_time': lap_response.sector1_time,
                        'sector2_time': lap_response.sector2_time,
                        'sector3_time': lap_response.sector3_time,
                        'compound': lap_response.compound,
                        'tyre_age': lap_response.tyre_age,
                        'is_personal_best': lap_response.is_personal_best,
                    })
            
            # Write to Parquet cache
            if lap_data_for_cache:
                cache_df = pd.DataFrame(lap_data_for_cache)
                self.cache.write(cache_df, session, "laps", drivers=drivers_str)
                logger.info(f"Cached laps to Parquet for {session}")
            
            return lap_responses
        
        except Exception as e:
            logger.error(f"Error loading laps: {e}", exc_info=True)
            return []
    
    async def get_fastest_laps(self, session: str):
        """Get fastest lap for each driver in a session."""
        return await self.get_laps(session, [])  # Empty list returns all drivers
    
    async def get_telemetry(
        self, 
        session: str, 
        drivers: List[str], 
        lap_type: str = "fastest",
        session_part: Optional[str] = None
    ) -> List[TelemetryResponse]:
        """
        Get telemetry data for specified drivers.
        
        Args:
            session: Session identifier (e.g., "2025_24_Qualifying")
            drivers: List of driver codes
            lap_type: Type of lap to retrieve
            session_part: Optional qualifying session part ('Q1', 'Q2', or 'Q3')
        """
        try:
            # Define drivers_str before cache check (needed for cache write later)
            drivers_str = '_'.join(sorted(drivers))
            
            # Skip cache when filtering by session_part (cache doesn't store by session part)
            if not session_part:
                # Try Parquet cache first
                cached_df = self.cache.read(session, "telemetry", drivers=drivers_str, lap_type=lap_type)
                
                if cached_df is not None:
                    # Convert cached DataFrame to TelemetryResponse objects
                    telemetry_responses = []
                    for driver in drivers:
                        driver_data = cached_df[cached_df['driver'] == driver]
                        if len(driver_data) > 0:
                            row = driver_data.iloc[0]
                            # Parse list strings back to lists
                            import json
                            telemetry_responses.append(
                                TelemetryResponse(
                                    driver=driver,
                                    lap_number=int(row['lap_number']),
                                    lap_time=float(row['lap_time']) if pd.notna(row.get('lap_time')) else None,
                                    distance=json.loads(row['distance']),
                                    speed=json.loads(row['speed']),
                                    throttle=json.loads(row['throttle']),
                                    brake=json.loads(row['brake']),
                                    gear=json.loads(row['gear']),
                                    rpm=json.loads(row['rpm']) if pd.notna(row.get('rpm')) else None,
                                    drs=json.loads(row['drs']) if pd.notna(row.get('drs')) else None,
                                )
                            )
                    logger.info(f"Loaded telemetry from Parquet cache for {session}")
                    return telemetry_responses
            
            # Fetch from FastF1
            season, round_num, session_name = self._parse_session_id(session)
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            telemetry_responses = []
            telemetry_data_for_cache = []
            
            # Get session status for time-based filtering
            session_status = race_session.session_status if hasattr(race_session, 'session_status') else None
            
            for driver in drivers:
                # Get driver's laps
                driver_laps = race_session.laps.pick_driver(driver)
                if len(driver_laps) == 0:
                    continue
                
                # Filter by session part if specified
                filtered_laps = self._filter_laps_by_session_part(driver_laps, session_part, session_status)
                if len(filtered_laps) == 0:
                    continue

                # Filter out deleted and pit laps for data quality
                valid_laps = self._filter_valid_laps(filtered_laps)
                if len(valid_laps) == 0:
                    logger.warning(f"No valid laps for driver {driver} after filtering")
                    continue

                fastest_lap = valid_laps.pick_fastest()

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
                        
                        # Extract official lap time
                        lap_time_seconds = None
                        if pd.notna(fastest_lap['LapTime']):
                            lap_time_seconds = float(fastest_lap['LapTime'].total_seconds())
                        
                        telemetry_response = TelemetryResponse(
                            driver=driver,
                            lap_number=int(fastest_lap['LapNumber']),
                            lap_time=lap_time_seconds,
                            distance=distance.tolist(),
                            speed=speed.tolist(),
                            throttle=throttle.tolist(),
                            brake=brake.tolist(),
                            gear=gear.tolist(),
                            rpm=rpm.tolist() if rpm is not None else None,
                            drs=drs.tolist() if drs is not None else None,
                        )
                        telemetry_responses.append(telemetry_response)
                        
                        # Prepare for cache (store as JSON strings for Parquet compatibility)
                        import json
                        telemetry_data_for_cache.append({
                            'driver': driver,
                            'lap_number': telemetry_response.lap_number,
                            'lap_time': telemetry_response.lap_time,
                            'distance': json.dumps(telemetry_response.distance),
                            'speed': json.dumps(telemetry_response.speed),
                            'throttle': json.dumps(telemetry_response.throttle),
                            'brake': json.dumps(telemetry_response.brake),
                            'gear': json.dumps(telemetry_response.gear),
                            'rpm': json.dumps(telemetry_response.rpm) if telemetry_response.rpm else None,
                            'drs': json.dumps(telemetry_response.drs) if telemetry_response.drs else None,
                        })
            
            # Write to Parquet cache
            if telemetry_data_for_cache:
                cache_df = pd.DataFrame(telemetry_data_for_cache)
                self.cache.write(cache_df, session, "telemetry", drivers=drivers_str, lap_type=lap_type)
                logger.info(f"Cached telemetry to Parquet for {session}")
            
            return telemetry_responses
        
        except Exception as e:
            logger.error(f"Error loading telemetry: {e}", exc_info=True)
            return []
    
    async def get_delta_analysis(
        self, 
        session: str, 
        reference_driver: str, 
        compare_drivers: List[str],
        session_part: Optional[str] = None
    ) -> List[DeltaResponse]:
        """
        Calculate delta time between drivers.
        
        Args:
            session: Session identifier
            reference_driver: Driver code for reference lap
            compare_drivers: List of driver codes to compare against reference
            session_part: Optional qualifying session part ('Q1', 'Q2', or 'Q3')
        """
        try:
            season, round_num, session_name = self._parse_session_id(session)
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            # Get session status for time-based filtering
            session_status = race_session.session_status if hasattr(race_session, 'session_status') else None
            
            # Get reference driver's laps and filter by session part
            ref_laps = race_session.laps.pick_driver(reference_driver)
            if len(ref_laps) == 0:
                return []
            
            ref_filtered = self._filter_laps_by_session_part(ref_laps, session_part, session_status)
            if len(ref_filtered) == 0:
                return []

            # Filter out deleted and pit laps for reference driver
            ref_valid = self._filter_valid_laps(ref_filtered)
            if len(ref_valid) == 0:
                logger.warning(f"No valid laps for reference driver {reference_driver}")
                return []

            ref_fastest = ref_valid.pick_fastest()
            ref_telemetry = ref_fastest.get_telemetry()
            
            delta_responses = []
            
            for compare_driver in compare_drivers:
                # Get comparison driver's laps and filter by session part
                comp_laps = race_session.laps.pick_driver(compare_driver)
                if len(comp_laps) == 0:
                    continue
                
                comp_filtered = self._filter_laps_by_session_part(comp_laps, session_part, session_status)
                if len(comp_filtered) == 0:
                    continue

                # Filter out deleted and pit laps for comparison driver
                comp_valid = self._filter_valid_laps(comp_filtered)
                if len(comp_valid) == 0:
                    logger.warning(f"No valid laps for comparison driver {compare_driver}")
                    continue

                comp_fastest = comp_valid.pick_fastest()
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
            logger.error(f"Error calculating delta: {e}", exc_info=True)
            return []
    
    async def get_sectors(
        self, 
        session: str, 
        drivers: List[str],
        session_part: Optional[str] = None
    ) -> List[SectorTime]:
        """
        Get sector times for specified drivers.
        
        Args:
            session: Session identifier
            drivers: List of driver codes
            session_part: Optional qualifying session part ('Q1', 'Q2', or 'Q3')
        """
        try:
            season, round_num, session_name = self._parse_session_id(session)
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            # Get session status for time-based filtering
            session_status = race_session.session_status if hasattr(race_session, 'session_status') else None
            
            sector_times = []
            
            for driver in drivers:
                driver_laps = race_session.laps.pick_driver(driver)
                if len(driver_laps) == 0:
                    continue
                
                # Filter by session part if specified
                filtered_laps = self._filter_laps_by_session_part(driver_laps, session_part, session_status)
                if len(filtered_laps) == 0:
                    continue

                # Filter out deleted and pit laps for data quality
                valid_laps = self._filter_valid_laps(filtered_laps)
                if len(valid_laps) == 0:
                    logger.warning(f"No valid laps for driver {driver} after filtering")
                    continue

                fastest_lap = valid_laps.pick_fastest()

                if fastest_lap is not None and not fastest_lap.empty:
                    s1 = float(fastest_lap['Sector1Time'].total_seconds()) if pd.notna(fastest_lap['Sector1Time']) else None
                    s2 = float(fastest_lap['Sector2Time'].total_seconds()) if pd.notna(fastest_lap['Sector2Time']) else None
                    s3 = float(fastest_lap['Sector3Time'].total_seconds()) if pd.notna(fastest_lap['Sector3Time']) else None
                    lap_time = float(fastest_lap['LapTime'].total_seconds()) if pd.notna(fastest_lap['LapTime']) else None
                    
                    if s1 and s2 and s3 and lap_time:
                        sector_times.append(
                            SectorTime(
                                driver=driver,
                                sector1=s1,
                                sector2=s2,
                                sector3=s3,
                                total_time=lap_time,
                            )
                        )
            
            return sector_times
        
        except Exception as e:
            logger.error(f"Error getting sectors: {e}", exc_info=True)
            return []
    
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
                    end_point=z["endPoint"],
                    wrap_around=z.get("wrapAround")  # Handle wrap-around zones crossing start/finish
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
            logger.warning(f"Track data not available: {e}, falling back to FastF1")
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

