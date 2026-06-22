"""Mock data service for testing without FastF1."""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
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
from app.core.config import settings


class MockDataService:
    """
    Service providing mock data for development and testing.
    Simulates FastF1 responses with synthetic but realistic data.
    """

    def __init__(self):
        self.fixtures_dir = settings.MOCK_DATA_DIR

    def _load_fixture(self, filename: str) -> dict:
        """Load a JSON fixture file."""
        filepath = self.fixtures_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture not found: {filename}")
        with open(filepath, "r") as f:
            return json.load(f)

    async def get_sessions(self, season: int, round: int) -> List[SessionResponse]:
        """
        Get qualifying session metadata.
        Returns pre-defined qualifying session.
        """
        session_data = self._load_fixture("qualifying_session.json")
        # Update with requested season/round
        session_data["season"] = season
        session_data["round"] = round
        session_data["session_id"] = f"{season}_{round}_Q"
        
        return [SessionResponse(**session_data)]

    async def get_session_by_id(self, session_id: str) -> SessionResponse:
        """Get detailed session information."""
        session_data = self._load_fixture("qualifying_session.json")
        session_data["session_id"] = session_id
        return SessionResponse(**session_data)

    async def get_laps(self, session: str, drivers: List[str]) -> List[LapResponse]:
        """
        Get lap data for specified drivers.
        Filters mock data by requested driver list.
        """
        lap_data = self._load_fixture("lap_data.json")
        laps = lap_data["laps"]
        
        # Filter by requested drivers
        filtered_laps = [lap for lap in laps if lap["driver"] in drivers]
        
        return [LapResponse(**lap) for lap in filtered_laps]

    async def get_fastest_laps(self, session: str):
        """Get fastest lap for each driver."""
        lap_data = self._load_fixture("lap_data.json")
        return lap_data["laps"]

    async def get_telemetry(
        self,
        session: str,
        drivers: List[str],
        lap_type: str = "fastest",
        session_part: Optional[str] = None,  # Accept but ignore for mock data
        acquisition: Optional[str] = None  # G0: accept but ignore (mock has no native path)
    ) -> List[TelemetryResponse]:
        """
        Generate synthetic telemetry data for specified drivers.
        Creates realistic speed, throttle, brake, gear traces.
        """
        telemetry_responses = []
        
        for i, driver in enumerate(drivers):
            # Generate distance array (0 to 5000 meters)
            distance = np.linspace(0, 5000, 1000).tolist()
            
            # Generate synthetic speed curve (80-330 km/h)
            # Simulate corners and straights
            t = np.linspace(0, 4 * np.pi, 1000)
            base_speed = 200 + 80 * np.sin(t) + 50 * np.sin(2 * t + i * 0.1)
            speed = np.clip(base_speed, 80, 330).tolist()
            
            # Generate throttle (0-100%)
            # High on straights, low in corners
            throttle_base = 50 + 40 * np.sin(t - 0.5) + 10 * np.sin(3 * t)
            throttle = np.clip(throttle_base, 0, 100).tolist()
            
            # Generate brake (0-100%)
            # Inverse of speed zones
            brake_zones = (base_speed < 150).astype(float) * 80
            brake = (brake_zones + np.random.normal(0, 5, len(brake_zones))).clip(0, 100).tolist()
            
            # Generate gear (1-8)
            gear_base = (np.array(speed) / 40).astype(int)
            gear = np.clip(gear_base, 1, 8).tolist()
            
            # Generate RPM (10000-12000)
            rpm_base = 10000 + (np.array(speed) / 330 * 2000)
            rpm = rpm_base.astype(int).tolist()
            
            # Generate DRS (0 or 1)
            drs = ((np.array(speed) > 250) & (np.array(throttle) > 80)).astype(int).tolist()
            
            telemetry_responses.append(
                TelemetryResponse(
                    driver=driver,
                    lap_number=1,
                    distance=distance,
                    speed=speed,
                    throttle=throttle,
                    brake=brake,
                    gear=gear,
                    rpm=rpm,
                    drs=drs,
                )
            )
        
        return telemetry_responses

    async def get_delta_analysis(
        self,
        session: str,
        reference_driver: str,
        compare_drivers: List[str],
        session_part: Optional[str] = None,  # Accept but ignore for mock data
        acquisition: Optional[str] = None  # G0: accept but ignore (mock has no native path)
    ) -> List[DeltaResponse]:
        """
        Calculate delta between reference and comparison drivers.
        Uses synthetic telemetry to compute time deltas.
        """
        # Get telemetry for all drivers
        all_drivers = [reference_driver] + compare_drivers
        telemetry_data = await self.get_telemetry(session, all_drivers, "fastest")
        
        # Find reference telemetry
        ref_telem = next(t for t in telemetry_data if t.driver == reference_driver)
        
        delta_responses = []
        
        for compare_driver in compare_drivers:
            comp_telem = next(t for t in telemetry_data if t.driver == compare_driver)
            
            # Calculate time delta based on speed difference
            # Delta accumulates over distance based on speed differences
            ref_speeds = np.array(ref_telem.speed)
            comp_speeds = np.array(comp_telem.speed)
            distance = np.array(ref_telem.distance)
            
            # Simple delta calculation: time = distance / speed
            # Cumulative time at each point
            delta_distances = np.diff(distance, prepend=0)
            ref_times = np.cumsum(delta_distances / (ref_speeds / 3.6))  # Convert km/h to m/s
            comp_times = np.cumsum(delta_distances / (comp_speeds / 3.6))
            
            # Delta is comparison time minus reference time
            delta = (comp_times - ref_times).tolist()
            
            delta_responses.append(
                DeltaResponse(
                    reference_driver=reference_driver,
                    compare_driver=compare_driver,
                    distance=distance.tolist(),
                    delta=delta,
                )
            )
        
        return delta_responses

    async def get_sectors(
        self, 
        session: str, 
        drivers: List[str],
        session_part: Optional[str] = None  # Accept but ignore for mock data
    ) -> List[SectorTime]:
        """
        Get sector times for specified drivers.
        """
        lap_data = self._load_fixture("lap_data.json")
        laps = lap_data["laps"]
        
        sector_times = []
        for lap in laps:
            if lap["driver"] in drivers:
                sector_times.append(
                    SectorTime(
                        driver=lap["driver"],
                        sector1=lap["sector1_time"],
                        sector2=lap["sector2_time"],
                        sector3=lap["sector3_time"],
                        total_time=lap["lap_time"],
                    )
                )
        
        return sector_times

    async def get_race_laps(self, session: str) -> dict:
        """
        Generate synthetic race lap data for development/testing.
        Returns dict with 'laps' (~228 laps) and 'finishing_positions'.
        """
        drivers = [
            ('VER', 'Red Bull Racing'),
            ('NOR', 'McLaren'),
            ('LEC', 'Ferrari'),
            ('HAM', 'Mercedes'),
        ]
        total_laps = 57
        result = []

        for driver_idx, (driver, team) in enumerate(drivers):
            # Base pace varies by driver (faster drivers have lower base)
            base_time = 92.0 + driver_idx * 0.3
            stint_boundary = 25  # Pit on lap 25

            for lap_num in range(1, total_laps + 1):
                # Determine stint and compound
                if lap_num <= stint_boundary:
                    stint = 1
                    compound = 'MEDIUM'
                    tyre_life = lap_num
                else:
                    stint = 2
                    compound = 'HARD'
                    tyre_life = lap_num - stint_boundary

                # Lap time with tyre degradation and small random variation
                deg = 0.02 * tyre_life  # 0.02s per lap of tyre age
                variation = np.random.normal(0, 0.15)
                lap_time = base_time + deg + variation

                pit_in = None
                pit_out = None
                track_status = '1'
                position = driver_idx + 1

                # Pit stop on stint boundary
                if lap_num == stint_boundary:
                    pit_in = lap_time * lap_num  # Approximate session time
                    lap_time += 20.0  # Pit lane adds ~20s

                if lap_num == stint_boundary + 1:
                    pit_out = lap_time * lap_num

                # Safety car on laps 15-16
                if lap_num in (15, 16):
                    track_status = '4'
                    lap_time = 120.0 + np.random.normal(0, 0.5)

                # One anomalous lap per driver
                if lap_num == 40 and driver_idx == 0:
                    lap_time = base_time * 1.15  # 15% slower

                result.append({
                    'driver': driver,
                    'team': team,
                    'lap_number': lap_num,
                    'lap_time': round(lap_time, 3),
                    'sector1_time': round(lap_time * 0.30, 3),
                    'sector2_time': round(lap_time * 0.38, 3),
                    'sector3_time': round(lap_time * 0.32, 3),
                    'compound': compound,
                    'tyre_life': tyre_life,
                    'stint': stint,
                    'position': position,
                    'pit_in_time': pit_in,
                    'pit_out_time': pit_out,
                    'track_status': track_status,
                    'is_personal_best': False,
                    'cumulative_time': round(5400.0 + (lap_num * base_time) + (driver_idx * 2.0 * lap_num), 3),
                    'speed_trap': round(310.0 + driver_idx * 2.0 + np.random.normal(0, 1.5), 1),
                    'speed_i1': round(280.0 + driver_idx * 1.5 + np.random.normal(0, 1.0), 1),
                    'speed_i2': round(265.0 + driver_idx * 1.0 + np.random.normal(0, 1.2), 1),
                    'speed_fl': round(290.0 + driver_idx * 1.8 + np.random.normal(0, 1.3), 1),
                })

        finishing_positions = {driver: idx + 1 for idx, (driver, _) in enumerate(drivers)}
        return {'laps': result, 'finishing_positions': finishing_positions}

    async def get_practice_laps(self, session: str) -> dict:
        """
        Generate synthetic practice session lap data for development/testing.
        Returns dict with 'laps' (~120 laps: 4 drivers × 30 laps each).
        Practice sessions have multiple stints with mixed compounds.
        """
        drivers = [
            ('VER', 'Red Bull Racing'),
            ('NOR', 'McLaren'),
            ('LEC', 'Ferrari'),
            ('HAM', 'Mercedes'),
        ]
        result = []

        for driver_idx, (driver, team) in enumerate(drivers):
            # Base pace varies by driver
            base_time = 92.0 + driver_idx * 0.3

            # Stint 1: laps 1-12 on MEDIUM (installation + long run)
            # Stint 2: laps 13-20 on SOFT (short runs)
            # Stint 3: laps 21-30 on HARD (long run)
            stints = [
                (1, 1, 12, 'MEDIUM'),
                (2, 13, 20, 'SOFT'),
                (3, 21, 30, 'HARD'),
            ]

            for stint_num, start_lap, end_lap, compound in stints:
                for lap_num in range(start_lap, end_lap + 1):
                    tyre_life = lap_num - start_lap + 1

                    # Tyre degradation
                    deg = 0.02 * tyre_life
                    variation = np.random.normal(0, 0.15)
                    lap_time = base_time + deg + variation

                    pit_in = None
                    pit_out = None
                    track_status = '1'

                    # Pit stops at stint boundaries
                    if lap_num == end_lap and stint_num < 3:
                        pit_in = lap_time * lap_num
                        lap_time += 20.0

                    if lap_num == start_lap and stint_num > 1:
                        pit_out = lap_time * lap_num
                        lap_time += 5.0  # Out-lap slower

                    # One anomalous lap per driver (lap 8)
                    if lap_num == 8 and driver_idx == 0:
                        lap_time = base_time * 1.15

                    result.append({
                        'driver': driver,
                        'team': team,
                        'lap_number': lap_num,
                        'lap_time': round(lap_time, 3),
                        'sector1_time': round(lap_time * 0.30, 3),
                        'sector2_time': round(lap_time * 0.38, 3),
                        'sector3_time': round(lap_time * 0.32, 3),
                        'compound': compound,
                        'tyre_life': tyre_life,
                        'stint': stint_num,
                        'position': None,  # Practice has no positional data
                        'pit_in_time': pit_in,
                        'pit_out_time': pit_out,
                        'track_status': track_status,
                        'is_personal_best': False,
                        'cumulative_time': None,  # Often unavailable in practice
                        'speed_trap': round(310.0 + driver_idx * 2.0 + np.random.normal(0, 1.5), 1),
                        'speed_i1': round(280.0 + driver_idx * 1.5 + np.random.normal(0, 1.0), 1),
                        'speed_i2': round(265.0 + driver_idx * 1.0 + np.random.normal(0, 1.2), 1),
                        'speed_fl': round(290.0 + driver_idx * 1.8 + np.random.normal(0, 1.3), 1),
                    })

        # Set is_personal_best on each driver's fastest valid lap
        # (exclude pit laps to mimic real FastF1 behaviour)
        driver_fastest: Dict[str, tuple] = {}  # {driver: (lap_time, index)}
        for idx, lap in enumerate(result):
            if lap['pit_in_time'] is not None or lap['pit_out_time'] is not None:
                continue
            driver = lap['driver']
            lt = lap['lap_time']
            if driver not in driver_fastest or lt < driver_fastest[driver][0]:
                driver_fastest[driver] = (lt, idx)
        for _, (_, idx) in driver_fastest.items():
            result[idx]['is_personal_best'] = True

        return {'laps': result}

    async def get_track_info(self, season: int, round: int) -> TrackResponse:
        """Get track layout and information (mock)."""
        return TrackResponse(
            circuit_name="Bahrain International Circuit",
            round=round,
            season=season,
            length=5412.0,
            sectors=[
                SectorInfo(sector_number=1, start_distance=0, end_distance=1804),
                SectorInfo(sector_number=2, start_distance=1804, end_distance=3608),
                SectorInfo(sector_number=3, start_distance=3608, end_distance=5412),
            ],
            drs_zones=[
                DRSZone(zone_number=1, detection_point=450, activation_point=500, end_point=1200),
                DRSZone(zone_number=2, detection_point=2800, activation_point=2850, end_point=3500),
            ],
            corners=[
                CornerInfo(corner_number=1, distance=400, type="right", name="Turn 1"),
                CornerInfo(corner_number=2, distance=700, type="left"),
                CornerInfo(corner_number=3, distance=900, type="left"),
                CornerInfo(corner_number=4, distance=1300, type="right"),
            ],
        )

