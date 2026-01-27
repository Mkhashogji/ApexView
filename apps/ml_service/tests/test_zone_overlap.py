"""Tests for zone overlap prevention in corner analysis."""
import pytest
import numpy as np
from typing import List

from services.corner_analysis import (
    _clamp_zones_to_prevent_overlap,
    CornerResultV2,
    MIN_ZONE_LENGTH,
)
from services.delta_analysis import DeltaResult


class TestZoneOverlapPrevention:
    """Tests for _clamp_zones_to_prevent_overlap function."""

    def _make_corner_result(
        self, corner_num: int, apex: float, zone_start: float, zone_end: float
    ) -> CornerResultV2:
        """Helper to create test corner results."""
        return CornerResultV2(
            corner_number=corner_num,
            name=f"T{corner_num}",
            apex_distance=apex,
            brake_distance=zone_start + 20,
            zone_start=zone_start,
            zone_end=zone_end,
            delta_change=0.1,
            cause="apex",
            confidence="low",
            detected_apex=apex,
            entry_speed=200,
            apex_speed=100,
            exit_distance=zone_end,
            detection_metadata={}
        )

    def _make_delta_result(self) -> DeltaResult:
        """Helper to create test delta result."""
        dist = np.linspace(0, 5000, 1000).tolist()
        delta = np.linspace(0, -0.3, 1000).tolist()
        return DeltaResult(
            reference_driver="LEC",
            compare_driver="NOR",
            distance=dist,
            delta=delta,
            raw_delta=delta,
            official_gap=-0.3,
            scaling_factor=1.0,
            telemetry_gap=-0.3,
            confidence=1.0
        )

    def test_no_overlap_no_change(self):
        """When zones don't overlap, they should remain unchanged."""
        corners = [
            self._make_corner_result(1, apex=500, zone_start=200, zone_end=600),
            self._make_corner_result(2, apex=1000, zone_start=700, zone_end=1100),
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        assert result[0].zone_end == 600
        assert result[1].zone_start == 700

    def test_overlapping_zones_are_clamped(self):
        """Overlapping zones should be clamped to midpoint."""
        corners = [
            self._make_corner_result(1, apex=500, zone_start=200, zone_end=800),  # Extends past midpoint
            self._make_corner_result(2, apex=700, zone_start=400, zone_end=900),  # Starts before midpoint
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        midpoint = (500 + 700) / 2  # 600
        assert result[0].zone_end == midpoint
        # Zone start of second corner should now be at first corner's zone_end
        assert result[1].zone_start == midpoint

    def test_multiple_overlaps(self):
        """Multiple consecutive overlapping zones."""
        corners = [
            self._make_corner_result(1, apex=300, zone_start=0, zone_end=500),
            self._make_corner_result(2, apex=500, zone_start=200, zone_end=700),
            self._make_corner_result(3, apex=700, zone_start=400, zone_end=900),
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        # Check no overlaps remain
        for i in range(len(result) - 1):
            assert result[i].zone_end <= result[i + 1].zone_start, \
                f"Overlap between T{result[i].corner_number} and T{result[i+1].corner_number}"

    def test_clamped_metadata_is_set(self):
        """Clamped zones should have metadata indicating the adjustment."""
        corners = [
            self._make_corner_result(1, apex=500, zone_start=200, zone_end=800),
            self._make_corner_result(2, apex=700, zone_start=400, zone_end=900),
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        assert result[0].detection_metadata.get("zone_clamped") == True
        assert "original_zone_end" in result[0].detection_metadata

    def test_single_corner_unchanged(self):
        """Single corner should remain unchanged."""
        corners = [
            self._make_corner_result(1, apex=500, zone_start=200, zone_end=700),
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        assert len(result) == 1
        assert result[0].zone_start == 200
        assert result[0].zone_end == 700

    def test_empty_list(self):
        """Empty list should return empty."""
        delta = self._make_delta_result()
        result = _clamp_zones_to_prevent_overlap([], delta)
        assert result == []

    def test_corner_order_preserved(self):
        """Original corner number order should be preserved."""
        corners = [
            self._make_corner_result(3, apex=700, zone_start=400, zone_end=900),
            self._make_corner_result(1, apex=300, zone_start=0, zone_end=500),
            self._make_corner_result(2, apex=500, zone_start=200, zone_end=700),
        ]
        delta = self._make_delta_result()

        result = _clamp_zones_to_prevent_overlap(corners, delta)

        assert [r.corner_number for r in result] == [1, 2, 3]


class TestMexicoCornerSpacing:
    """Tests to verify Mexico-like corner spacing doesn't cause massive overlap."""

    def test_mexico_fallback_overlap_with_fix(self):
        """Test that Mexico corner spacing with fallback zones is handled correctly."""
        # Approximate Mexico corner apexes
        mexico_apexes = [250, 550, 850, 1100, 1300, 1650, 2050, 2400, 2800,
                        3150, 3350, 3700, 3900, 4050, 4150, 4300, 4400]

        # Create corner results with old fallback-style large zones
        # Old fallback: zone_start = apex - 320, zone_end = apex + 200
        corners = []
        for i, apex in enumerate(mexico_apexes):
            zone_start = max(0, apex - 320)
            zone_end = apex + 200
            corners.append(CornerResultV2(
                corner_number=i + 1,
                name=f"T{i + 1}",
                apex_distance=apex,
                brake_distance=zone_start + 20,
                zone_start=zone_start,
                zone_end=zone_end,
                delta_change=0.1,
                cause="apex",
                confidence="low",
                detected_apex=apex,
                entry_speed=200,
                apex_speed=100,
                exit_distance=zone_end,
                detection_metadata={}
            ))

        # Create delta result
        dist = np.linspace(0, 4500, 900).tolist()
        delta = np.linspace(0, -0.262, 900).tolist()
        delta_result = DeltaResult(
            reference_driver="LEC",
            compare_driver="NOR",
            distance=dist,
            delta=delta,
            raw_delta=delta,
            official_gap=-0.262,
            scaling_factor=1.0,
            telemetry_gap=-0.262,
            confidence=1.0
        )

        # Apply zone clamping
        result = _clamp_zones_to_prevent_overlap(corners, delta_result)

        # Verify NO overlaps after clamping
        overlap_count = 0
        total_overlap_distance = 0

        sorted_result = sorted(result, key=lambda x: x.apex_distance)
        for i in range(len(sorted_result) - 1):
            current = sorted_result[i]
            next_corner = sorted_result[i + 1]

            if current.zone_end > next_corner.zone_start:
                overlap_count += 1
                total_overlap_distance += current.zone_end - next_corner.zone_start

        assert overlap_count == 0, \
            f"Found {overlap_count} overlapping zone pairs after clamping"
        assert total_overlap_distance == 0, \
            f"Total overlap distance {total_overlap_distance:.0f}m should be 0"

    def test_zone_coverage_reasonable(self):
        """After clamping, total zone coverage should be <= track length."""
        mexico_apexes = [250, 550, 850, 1100, 1300, 1650, 2050, 2400, 2800,
                        3150, 3350, 3700, 3900, 4050, 4150, 4300, 4400]
        track_length = 4400

        corners = []
        for i, apex in enumerate(mexico_apexes):
            zone_start = max(0, apex - 320)
            zone_end = min(track_length, apex + 200)
            corners.append(CornerResultV2(
                corner_number=i + 1,
                name=f"T{i + 1}",
                apex_distance=apex,
                brake_distance=zone_start + 20,
                zone_start=zone_start,
                zone_end=zone_end,
                delta_change=0.1,
                cause="apex",
                confidence="low",
                detected_apex=apex,
                entry_speed=200,
                apex_speed=100,
                exit_distance=zone_end,
                detection_metadata={}
            ))

        dist = np.linspace(0, 4500, 900).tolist()
        delta = np.linspace(0, -0.262, 900).tolist()
        delta_result = DeltaResult(
            reference_driver="LEC",
            compare_driver="NOR",
            distance=dist,
            delta=delta,
            raw_delta=delta,
            official_gap=-0.262,
            scaling_factor=1.0,
            telemetry_gap=-0.262,
            confidence=1.0
        )

        result = _clamp_zones_to_prevent_overlap(corners, delta_result)

        # Calculate total zone coverage
        total_coverage = sum(r.zone_end - r.zone_start for r in result)

        # Should be <= track length (no double counting)
        assert total_coverage <= track_length, \
            f"Total zone coverage {total_coverage:.0f}m exceeds track length {track_length}m"


class TestReducedFallbackZones:
    """Test that reduced fallback zone sizes help prevent overlap."""

    def test_new_fallback_zone_sizes(self):
        """Verify new default zone sizes are smaller."""
        from services.corner_analysis import DEFAULT_ZONE_BEFORE_APEX, DEFAULT_ZONE_AFTER_APEX

        # New sizes should be 150 before and 80 after (total 230m)
        assert DEFAULT_ZONE_BEFORE_APEX == 150, \
            f"Expected DEFAULT_ZONE_BEFORE_APEX=150, got {DEFAULT_ZONE_BEFORE_APEX}"
        assert DEFAULT_ZONE_AFTER_APEX == 80, \
            f"Expected DEFAULT_ZONE_AFTER_APEX=80, got {DEFAULT_ZONE_AFTER_APEX}"

        # Total fallback zone should be 230m
        total_zone = DEFAULT_ZONE_BEFORE_APEX + DEFAULT_ZONE_AFTER_APEX
        assert total_zone == 230, f"Expected total zone 230m, got {total_zone}m"

    def test_min_zone_length_defined(self):
        """Verify MIN_ZONE_LENGTH is defined."""
        assert MIN_ZONE_LENGTH == 50, \
            f"Expected MIN_ZONE_LENGTH=50, got {MIN_ZONE_LENGTH}"
