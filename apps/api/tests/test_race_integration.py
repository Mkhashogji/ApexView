"""Integration test: full pipeline from raw laps to pace stats."""
import pytest
from app.services.race.transforms import (
    classify_race_laps, apply_fuel_correction, derive_traffic
)
from app.services.race.race_data_service import (
    extract_stints, extract_pit_stops, compute_race_pace_stats
)


class TestFullPipeline:
    """End-to-end pipeline test with realistic mock data."""

    @pytest.fixture
    def realistic_race_data(self):
        """
        Generate a realistic 3-driver, 30-lap race with:
        - 1 pit stop each (lap 15 in, lap 16 out)
        - Safety car on laps 10-11
        - One anomalous lap (driver 3, lap 25 = 120s)
        - Normal pace: driver1 ~88s, driver2 ~89s, driver3 ~90s
        """
        laps = []
        drivers = [
            ("VER", "Red Bull Racing", 88.0),
            ("NOR", "McLaren", 89.0),
            ("LEC", "Ferrari", 90.0),
        ]
        for driver, team, base_time in drivers:
            stint = 1
            tyre_life = 1
            compound = "MEDIUM"
            driver_idx = drivers.index((driver, team, base_time))
            for lap_num in range(1, 31):
                lap = {
                    "driver": driver,
                    "team": team,
                    "lap_number": lap_num,
                    "lap_time": None,
                    "sector1_time": None,
                    "sector2_time": None,
                    "sector3_time": None,
                    "compound": compound,
                    "tyre_life": tyre_life,
                    "stint": stint,
                    "position": driver_idx + 1,
                    "pit_in_time": None,
                    "pit_out_time": None,
                    "track_status": "1",
                    "is_personal_best": False,
                    "cumulative_time": 5400.0 + (lap_num * 90.0) + (driver_idx * 2.0 * lap_num),
                }

                # Formation lap
                if lap_num == 1:
                    lap["lap_time"] = None
                # Safety car laps
                elif lap_num in (10, 11):
                    lap["track_status"] = "4"
                    lap["lap_time"] = 110.0
                # Pit in-lap
                elif lap_num == 15:
                    lap["pit_in_time"] = 900.0
                    lap["lap_time"] = base_time + 15.0
                # Pit out-lap
                elif lap_num == 16:
                    lap["pit_out_time"] = 925.0
                    lap["lap_time"] = base_time + 10.0
                    stint = 2
                    tyre_life = 1
                    compound = "HARD"
                # Anomalous lap for LEC
                elif driver == "LEC" and lap_num == 25:
                    lap["lap_time"] = 120.0
                else:
                    # Normal racing lap with small variation
                    import random
                    random.seed(hash((driver, lap_num)))
                    variation = random.uniform(-0.5, 0.5)
                    lap["lap_time"] = base_time + variation

                lap["stint"] = stint
                lap["tyre_life"] = tyre_life
                lap["compound"] = compound
                tyre_life += 1
                laps.append(lap)
        return laps

    def test_pipeline_produces_valid_output(self, realistic_race_data):
        """Full pipeline: classify → fuel → traffic → stints → pits → stats."""
        laps = realistic_race_data

        # Step 1: Classify
        classified = classify_race_laps(laps)
        classifications = [l["classification"] for l in classified]
        assert "RACING" in classifications
        assert "SAFETY_CAR" in classifications
        assert "IN_LAP" in classifications
        assert "OUT_LAP" in classifications

        # Step 2: Fuel correct
        corrected = apply_fuel_correction(classified, 30, 0.034)
        racing_laps = [l for l in corrected
                       if l["classification"] == "RACING"
                       and l["fuel_corrected_time"] is not None]
        assert len(racing_laps) > 0
        # Early laps should have larger correction
        early = [l for l in racing_laps if l["lap_number"] <= 5]
        late = [l for l in racing_laps if l["lap_number"] >= 25]
        if early and late:
            avg_early_diff = sum(
                l["lap_time"] - l["fuel_corrected_time"] for l in early
            ) / len(early)
            avg_late_diff = sum(
                l["lap_time"] - l["fuel_corrected_time"] for l in late
            ) / len(late)
            assert avg_early_diff > avg_late_diff

        # Step 3: Traffic
        with_traffic = derive_traffic(corrected)

        # Step 4: Stints
        stints = extract_stints(with_traffic)
        assert len(stints) == 6  # 3 drivers x 2 stints

        # Step 5: Pit stops
        pit_stops = extract_pit_stops(with_traffic)
        assert len(pit_stops) == 3  # 1 per driver

        # Step 6: Stats
        race_data = {
            "laps": with_traffic,
            "stints": stints,
            "pit_stops": pit_stops,
            "session_id": "test_integration",
        }
        stats = compute_race_pace_stats(race_data)

        # Verify structure
        assert len(stats.drivers) == 3
        # VER should be fastest
        assert stats.drivers[0].driver == "VER"
        assert stats.drivers[0].gap_to_fastest == 0.0
        # NOR second
        assert stats.drivers[1].driver == "NOR"
        assert stats.drivers[1].gap_to_fastest > 0
        # All have tyre strategies
        for d in stats.drivers:
            assert len(d.tyre_strategy) == 2
            assert d.tyre_strategy[0] == "MEDIUM"
            assert d.tyre_strategy[1] == "HARD"
            assert d.total_racing_laps > 0

    def test_pipeline_handles_all_dnf(self):
        """Edge case: all drivers DNF early (minimal data)."""
        laps = [
            {
                "driver": "VER", "team": "Red Bull Racing",
                "lap_number": 2, "lap_time": 90.0,
                "sector1_time": None, "sector2_time": None,
                "sector3_time": None, "compound": "SOFT",
                "tyre_life": 1, "stint": 1, "position": 1,
                "pit_in_time": None, "pit_out_time": None,
                "track_status": "1", "is_personal_best": False,
                "cumulative_time": 5490.0,
            }
        ]
        classified = classify_race_laps(laps)
        corrected = apply_fuel_correction(classified, 57, 0.032)
        with_traffic = derive_traffic(corrected)
        stints = extract_stints(with_traffic)
        pit_stops = extract_pit_stops(with_traffic)
        race_data = {
            "laps": with_traffic,
            "stints": stints,
            "pit_stops": pit_stops,
            "session_id": "test_dnf",
        }
        stats = compute_race_pace_stats(race_data)
        # Should produce valid output even with minimal data
        assert len(stats.drivers) >= 1
