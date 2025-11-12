"""Mock data service for testing without FastF1."""

import json
import numpy as np
from pathlib import Path
from typing import List, Optional
from app.models.dto import (
    SessionResponse,
    LapResponse,
    TelemetryResponse,
    DeltaResponse,
    SectorTime,
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
        self, session: str, drivers: List[str], lap_type: str = "fastest"
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
        self, session: str, reference_driver: str, compare_drivers: List[str]
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

    async def get_sectors(self, session: str, drivers: List[str]) -> List[SectorTime]:
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
                        sector_1=lap["sector1_time"],
                        sector_2=lap["sector2_time"],
                        sector_3=lap["sector3_time"],
                        total_time=lap["lap_time"],
                    )
                )
        
        return sector_times

    async def get_track_info(self, season: int, round: int):
        """Get track layout and information (mock)."""
        return {
            "circuit_name": "Bahrain International Circuit",
            "round": round,
            "season": season,
            "length": 5412.0,
            "sectors": [
                {"sector_number": 1, "start_distance": 0, "end_distance": 1804},
                {"sector_number": 2, "start_distance": 1804, "end_distance": 3608},
                {"sector_number": 3, "start_distance": 3608, "end_distance": 5412},
            ],
            "drs_zones": [
                {
                    "zone_number": 1,
                    "detection_point": 450,
                    "activation_point": 500,
                    "end_point": 1200,
                },
                {
                    "zone_number": 2,
                    "detection_point": 2800,
                    "activation_point": 2850,
                    "end_point": 3500,
                },
            ],
        }

