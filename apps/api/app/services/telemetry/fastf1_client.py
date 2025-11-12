import fastf1
import numpy as np
import pandas as pd
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
)
from app.services.telemetry.transforms import calculate_delta, downsample_telemetry
from app.services.cache.parquet_cache import parquet_cache

# Enable cache on module import
enable_cache()


class FastF1Client:
    """Client for interacting with FastF1 library with Parquet caching."""
    
    def __init__(self):
        self.downsample_threshold = settings.DOWNSAMPLE_THRESHOLD
        self.cache = parquet_cache
    
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
                print(f"✓ Loaded laps from Parquet cache for {session}")
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
                
                fastest_lap = driver_laps.pick_fastest()
                
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
                print(f"✓ Cached laps to Parquet for {session}")
            
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
        """Get telemetry data for specified drivers with Parquet cache."""
        try:
            # Try Parquet cache first
            drivers_str = '_'.join(sorted(drivers))
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
                                distance=json.loads(row['distance']),
                                speed=json.loads(row['speed']),
                                throttle=json.loads(row['throttle']),
                                brake=json.loads(row['brake']),
                                gear=json.loads(row['gear']),
                                rpm=json.loads(row['rpm']) if pd.notna(row.get('rpm')) else None,
                                drs=json.loads(row['drs']) if pd.notna(row.get('drs')) else None,
                            )
                        )
                print(f"✓ Loaded telemetry from Parquet cache for {session}")
                return telemetry_responses
            
            # Cache miss - fetch from FastF1
            # Parse session identifier
            parts = session.split('_')
            season = int(parts[0])
            round_num = int(parts[1])
            session_name = '_'.join(parts[2:]).replace('_', ' ')
            
            # Load session
            race_session = fastf1.get_session(season, round_num, session_name)
            race_session.load()
            
            telemetry_responses = []
            telemetry_data_for_cache = []
            
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
                        
                        telemetry_response = TelemetryResponse(
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
                        telemetry_responses.append(telemetry_response)
                        
                        # Prepare for cache (store as JSON strings for Parquet compatibility)
                        import json
                        telemetry_data_for_cache.append({
                            'driver': driver,
                            'lap_number': telemetry_response.lap_number,
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
                print(f"✓ Cached telemetry to Parquet for {session}")
            
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
                        sector_1=lap.sector1_time,
                        sector_2=lap.sector2_time,
                        sector_3=lap.sector3_time,
                        total_time=lap.lap_time,
                    )
                )
        
        return sector_times
    
    async def get_track_info(self, season: int, round: int) -> TrackResponse:
        """Get track layout and information."""
        # FastF1 doesn't provide detailed track info, so this would need static data
        # For now, return minimal info
        event = fastf1.get_event(season, round)
        
        return TrackResponse(
            circuit_name=event.EventName if hasattr(event, 'EventName') else "Unknown",
            round=round,
            season=season,
            length=5000.0,  # Default, would need static data
            sectors=[],
            drs_zones=[],
        )

