"""
G0 — Honest Acquisition: analysis-service tests for the native substrate.

Covers (per the G0 Phase 6 spec):
- detector-on-native against synthetic corner fixtures (clean, strictly
  monotonic distance arrays — the native substrate property)
- gap_flag overlap logic (apply_gap_flags / _gap_overlaps_zone)
- response-schema freeze: gap_flag is internal, never serialized
- DeltaResult grid metadata population (native-sample bookkeeping)

Run inside the f1-analysis container:
    pytest tests/test_g0_native_substrate.py -v
"""
import numpy as np
import pytest

from core.corner_config import CornerAnalysisConfig
from services.corner_analysis import (
    CornerAnalysisResult,
    CornerResult,
    CornerResultV2,
    compute_deceleration,
    detect_braking_zone_v2,
)
from services.delta_analysis import calculate_scaled_delta
from services.performance_orchestrator import (
    _corner_result_to_dict,
    _gap_overlaps_zone,
    apply_gap_flags,
)


# =============================================================================
# Fixtures
# =============================================================================

def _native_corner_fixture(spacing_m=18.0, apex=550.0, brake_onset=400.0,
                           v_high=300.0, v_low=100.0):
    """
    Synthetic native-substrate corner: strictly monotonic distance at a
    realistic ~18 m high-speed sample spacing (the measured native floor),
    speed constant until brake_onset then linear to v_low at apex,
    boolean brake asserted from brake_onset.
    """
    distance = np.arange(0.0, apex + 200.0, spacing_m)
    speed = np.where(
        distance < brake_onset, v_high,
        np.clip(v_high + (v_low - v_high) * (distance - brake_onset) / (apex - brake_onset),
                v_low, v_high),
    )
    brake = (distance >= brake_onset).astype(float) * 100.0
    return distance, speed, brake


def _make_corner_result(corner_number, zone_start, zone_end, **kw):
    return CornerResultV2(
        corner_number=corner_number,
        name=f"T{corner_number}",
        apex_distance=(zone_start + zone_end) / 2,
        brake_distance=zone_start + 10,
        zone_start=zone_start,
        zone_end=zone_end,
        delta_change=0.01,
        cause="braking",
        confidence="medium",
        **kw,
    )


def _make_analysis_result(corner_results):
    return CornerAnalysisResult(
        reference_driver="PIA",
        compare_driver="RUS",
        corner_results=corner_results,
        total_delta_change=sum(c.delta_change for c in corner_results),
        corners_gaining=0,
        corners_losing=len(corner_results),
    )


# =============================================================================
# Detector on the native substrate
# =============================================================================

class TestDetectorOnNativeSubstrate:
    def test_brake_detection_on_clean_native_arrays(self):
        """
        The V2 two-stage detector, algorithmically unchanged, run on a
        native-like substrate (strictly monotonic, no near-duplicate
        distances). Detection must land within one sample spacing of the
        true onset.
        """
        spacing = 18.0
        distance, speed, brake = _native_corner_fixture(spacing_m=spacing)
        config = CornerAnalysisConfig()  # production default (orchestrator passes no circuit_id)
        decel = compute_deceleration(distance, speed, config.decel_smoothing_window)

        brake_dist, confidence, meta = detect_braking_zone_v2(
            distance, brake, speed, decel, apex_distance=550.0, config=config)

        # True onset 400 m. Resolution envelope on the native substrate:
        # one sample spacing (quantisation) + decel_smoothing_window//2
        # samples (compute_deceleration's moving average smears the onset
        # backward by up to half the window). For the default window of 5
        # at 18 m spacing: 18 * (1 + 2) = 54 m.
        envelope = spacing * (1 + config.decel_smoothing_window // 2)
        assert brake_dist == pytest.approx(400.0, abs=envelope + 1e-6)
        # With brake asserted exactly at onset, this fixture deterministically
        # exercises the two-stage path (review L5-11: unconditional — a
        # degradation to decel_only would be a detector regression).
        assert meta["stage"] == "two_stage"
        # The Stage-2 walk only ever moves the point EARLIER (backward):
        # detection must never land after the boolean brake candidate.
        assert brake_dist <= meta["boolean_dist"] + 1e-9
        assert confidence in ("high", "medium")

    def test_no_duplicate_distance_pathology(self):
        """NEAR-DUPLICATE distances — the merged-frame pathology measured in
        diagnostics/granularity REPORT.md Phase 4 — must not produce unbounded
        derivative spikes. Since WU-4 the near-zero Δd guard emits NaN for the
        degenerate interval (|Δd| < MIN_VALID_DELTA_DISTANCE_M) instead of
        clamping the denominator: undefined, not fabricated. (Review L5-7:
        actually exercise the pathology, don't assert a by-construction-clean
        fixture. Pre-WU-4 this test asserted all-finite output, pinning the
        old 0.001 m substitution — which fabricated a ~10^4 m/s² value here.)"""
        distance, speed, _ = _native_corner_fixture()
        # inject near-duplicate distance points (sub-cm spacing) with a speed step
        distance = np.insert(distance, 10, distance[10] + 0.001)
        speed = np.insert(speed, 10, speed[10] - 5.0)
        decel = compute_deceleration(distance, speed, 5)
        finite = np.isfinite(decel)
        # exactly the injected degenerate interval is undefined ...
        assert int(np.count_nonzero(~finite)) == 1
        # ... and no unbounded spike leaks into the finite values
        assert np.all(np.abs(decel[finite]) < 200.0)


# =============================================================================
# Gap-flag overlap logic
# =============================================================================

class TestGapFlags:
    def test_overlap_camel_and_snake_keys(self):
        zone = (380.0, 600.0)
        assert _gap_overlaps_zone({"dStart": 500.0, "dEnd": 520.0}, *zone)
        assert _gap_overlaps_zone({"d_start": 500.0, "d_end": 520.0}, *zone)
        assert not _gap_overlaps_zone({"dStart": 601.0, "dEnd": 650.0}, *zone)
        assert not _gap_overlaps_zone({"dStart": 300.0, "dEnd": 379.0}, *zone)
        # boundary touch counts as overlap (inclusive interval intersection)
        assert _gap_overlaps_zone({"dStart": 600.0, "dEnd": 650.0}, *zone)
        # symmetric edge: gap END touching zone START (review L5-14)
        assert _gap_overlaps_zone({"dStart": 300.0, "dEnd": 380.0}, *zone)
        # malformed gap -> no flag
        assert not _gap_overlaps_zone({}, *zone)

    def test_apply_gap_flags_sets_only_overlapping(self):
        corners = [
            _make_corner_result(1, 100.0, 250.0),
            _make_corner_result(2, 380.0, 600.0),
            _make_corner_result(3, 900.0, 1050.0),
        ]
        result = _make_analysis_result(corners)
        ref_gaps = [{"dStart": 500.0, "dEnd": 540.0, "dt": 1.0, "ratio": 4.0}]
        comp_gaps = [{"dStart": 1000.0, "dEnd": 1020.0, "dt": 0.9, "ratio": 3.6}]

        flagged = apply_gap_flags(result, ref_gaps, comp_gaps)

        assert flagged == 2
        assert corners[0].gap_flag is False
        assert corners[1].gap_flag is True   # ref gap overlaps
        assert corners[2].gap_flag is True   # comp gap overlaps
        # analytical values untouched
        assert corners[1].delta_change == 0.01
        assert corners[1].confidence == "medium"

    def test_no_gaps_no_flags(self):
        corners = [_make_corner_result(1, 100.0, 250.0)]
        result = _make_analysis_result(corners)
        assert apply_gap_flags(result, [], []) == 0
        assert corners[0].gap_flag is False

    def test_gap_flag_defaults_false_for_backward_compat(self):
        # Existing construction sites do not pass gap_flag.
        cr = CornerResult(
            corner_number=1, name=None, apex_distance=500.0,
            brake_distance=400.0, zone_start=380.0, zone_end=600.0,
            delta_change=0.0, cause="unknown", confidence="low")
        assert cr.gap_flag is False


# =============================================================================
# Response-schema freeze
# =============================================================================

class TestSchemaFreeze:
    def test_gap_flag_not_serialized(self):
        """gap_flag is internal at G0 — the corner dict that feeds the frozen
        API response must not contain it (golden contract)."""
        cr = _make_corner_result(2, 380.0, 600.0)
        cr.gap_flag = True
        d = _corner_result_to_dict(cr)
        assert "gap_flag" not in d
        assert set(d.keys()) == {
            "corner_number", "name", "apex_distance", "brake_distance",
            "zone_start", "zone_end", "delta_change", "cause", "confidence",
        }


# =============================================================================
# DeltaResult grid metadata
# =============================================================================

class TestDeltaGridMetadata:
    def _tier1_inputs(self, n_ref=332, n_comp=340):
        track_len = 5400.0
        ref_d = np.linspace(0, track_len, n_ref)
        comp_d = np.linspace(0, track_len, n_comp)
        return (
            {
                "distance": ref_d.tolist(),
                "speed": np.full(n_ref, 200.0).tolist(),
                "relative_distance": (ref_d / track_len).tolist(),
                "time": np.linspace(0, 90.0, n_ref).tolist(),
            },
            {
                "distance": comp_d.tolist(),
                "speed": np.full(n_comp, 199.0).tolist(),
                "relative_distance": (comp_d / track_len).tolist(),
                "time": np.linspace(0, 90.3, n_comp).tolist(),
            },
        )

    def test_grid_metadata_populated_tier1(self):
        ref, comp = self._tier1_inputs()
        result = calculate_scaled_delta(
            ref_telemetry=ref, comp_telemetry=comp,
            ref_official_time=90.0, comp_official_time=90.3,
            ref_driver="PIA", comp_driver="RUS")

        assert result.ref_sample_count == 332
        assert result.comp_sample_count == 340
        # uniform spacing fixtures -> median spacing = track_len / (n - 1)
        assert result.ref_median_spacing_m == pytest.approx(5400.0 / 331, rel=1e-3)
        assert result.comp_median_spacing_m == pytest.approx(5400.0 / 339, rel=1e-3)
        # Tier-1 closure unchanged: delta[-1] == official gap
        assert result.delta[-1] == pytest.approx(0.3, abs=1e-6)
        assert result.scaling_factor == 1.0

    def test_grid_metadata_populated_tier3(self):
        ref, comp = self._tier1_inputs()
        # strip tier-1/2 fields -> falls to tier 3 (speed integration)
        for d in (ref, comp):
            d.pop("relative_distance")
            d.pop("time")
        result = calculate_scaled_delta(
            ref_telemetry=ref, comp_telemetry=comp,
            ref_official_time=90.0, comp_official_time=90.3,
            ref_driver="PIA", comp_driver="RUS")
        assert result.ref_sample_count == 332
        assert result.comp_sample_count == 340
        assert result.confidence <= 0.6  # tier-3 cap, unchanged

    def test_metadata_defaults_none(self):
        from services.delta_analysis import DeltaResult
        # Existing keyword construction sites remain valid without metadata.
        r = DeltaResult(
            reference_driver="A", compare_driver="B", distance=[0.0],
            delta=[0.0], raw_delta=[0.0], official_gap=0.0,
            scaling_factor=1.0, telemetry_gap=0.0, confidence=0.5)
        assert r.ref_sample_count is None
        assert r.comp_median_spacing_m is None

    def test_grid_metadata_never_in_response_schemas(self):
        """Review L5-12: pin the schema freeze — DeltaResult's internal grid
        metadata must never appear in any serialized response model. An
        asdict()-style refactor of the response assembly would otherwise leak
        them with green suites."""
        from models.schemas import (
            DriverPerformanceResult,
            ScaledDeltaDriverResult,
            ScaledDeltaResponse,
        )
        internal = {"ref_sample_count", "comp_sample_count",
                    "ref_median_spacing_m", "comp_median_spacing_m"}
        for model in (ScaledDeltaResponse, ScaledDeltaDriverResult, DriverPerformanceResult):
            assert internal.isdisjoint(set(model.model_fields)), model.__name__


# =============================================================================
# fetch_all_native_meta graceful degradation (review L5-5)
# =============================================================================

class TestNativeMetaDegradation:
    """The gap-metadata fetch must NEVER take down the insights pipeline:
    every failure mode degrades to {} (gap_flag stays False) with a warning.
    The telemetry arrays themselves are never fallback-fetched."""

    def _run(self, mock_client):
        import asyncio
        from services.performance_orchestrator import fetch_all_native_meta
        return asyncio.run(fetch_all_native_meta(
            mock_client, "2025_2_Qualifying", ["PIA", "RUS"], "Q3"))

    def _client(self, status=200, payload=None, exc=None):
        from unittest.mock import AsyncMock, MagicMock
        client = AsyncMock()
        if exc is not None:
            client.get.side_effect = exc
        else:
            resp = MagicMock()
            resp.status_code = status
            resp.json.return_value = payload
            client.get.return_value = resp
        return client

    def test_non_200_degrades_to_empty(self):
        assert self._run(self._client(status=501, payload={})) == {}

    def test_non_list_payload_degrades(self):
        assert self._run(self._client(payload={"driver": "PIA"})) == {}

    def test_item_missing_gaps_key_degrades(self):
        # the canned-telemetry-for-every-URL mock shape used by the existing
        # orchestrator tests: list items WITHOUT a 'gaps' key
        telemetry_shaped = [{"driver": "PIA", "distance": [1, 2], "speed": [100, 101]}]
        assert self._run(self._client(payload=telemetry_shaped)) == {}

    def test_exception_degrades(self):
        assert self._run(self._client(exc=RuntimeError("network down"))) == {}

    def test_valid_payload_parsed(self):
        payload = [
            {"driver": "PIA", "lapNumber": 19,
             "gaps": [{"tStart": 1.0, "tEnd": 2.0, "dStart": 100.0, "dEnd": 150.0,
                       "dt": 1.0, "ratio": 4.0}],
             "meta": {"schemaVersion": "native_v1"}},
            {"driver": "RUS", "lapNumber": 21, "gaps": [], "meta": {}},
        ]
        result = self._run(self._client(payload=payload))
        assert set(result) == {"PIA", "RUS"}
        assert result["PIA"][0]["dStart"] == 100.0
        assert result["RUS"] == []
