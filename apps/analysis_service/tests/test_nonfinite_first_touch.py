"""
WU-2: end-to-end injection — a non-finite telemetry payload must produce an
honest degrade, not a fabricated result.

The WU-2 diagnostic measured the pre-WU-2 defect on the real production
path: a wire payload with JSON nulls in speed ([300, null, 298, null, null,
250] — what the API serialises a NaN into) was parsed to None, re-emerged as
NaN inside np.array(..., dtype=float), and _safe_array silently interpolated
it into fabricated values ([300, 299, 298, 282, 266, 250]) — yielding a
normal-looking corner result at medium confidence. These tests pin the
post-WU-2 contract at the first-touch layer and would have caught the
original defect.

They are deliberately pitched BELOW the orchestrator's ingress validation
(fetch_driver_telemetry), so they stay meaningful after WU-2b lands: they
prove that even if a non-finite array reaches corner analysis by any route
(a standalone endpoint, a future G1 producer injected at the telemetry-dict
seam), it is rejected, not laundered.
"""
import numpy as np
import pytest

from core.errors import NonFiniteTelemetryError
from services.corner_analysis import CornerInput, analyze_corners_v2
from services.delta_analysis import DeltaResult
from services.performance_orchestrator import run_phase3_corner


def _wire_parsed_telemetry(n=24, poison_speed=True):
    """
    Telemetry dicts in the exact shape fetch_driver_telemetry hands to
    Phase 3: plain Python lists, with the reference driver's speed carrying
    JSON-null-parsed None values (the wire form of an API-side NaN).
    """
    distance = [float(i) * 15.0 for i in range(n)]
    speed = [250.0 - i * 2.0 for i in range(n)]
    if poison_speed:
        speed[3] = None
        speed[7] = None
    brake = [0.0] * n
    ref = {"distance": distance, "speed": speed, "brake": brake}
    comp = {"distance": list(distance), "speed": [240.0 - i * 2.0 for i in range(n)],
            "brake": list(brake)}
    return ref, comp


def _delta_result(ref, comp):
    return DeltaResult(
        reference_driver="PIA",
        compare_driver="RUS",
        distance=list(ref["distance"]),
        delta=[0.0] * len(ref["distance"]),
        raw_delta=[0.0] * len(ref["distance"]),
        official_gap=0.082,
        scaling_factor=1.0,
        telemetry_gap=0.082,
        confidence=0.85,
    )


CORNERS = [CornerInput(corner_number=1, apex_distance=180.0, name="T1",
                       corner_type="slow")]


class TestNonFiniteFirstTouch:
    def test_analyze_corners_v2_rejects_null_bearing_speed(self):
        """First touch (analyze_corners_v2's _safe_array calls) must raise,
        naming the offending channel — not return a fabricated result."""
        ref, comp = _wire_parsed_telemetry()
        with pytest.raises(NonFiniteTelemetryError) as exc_info:
            analyze_corners_v2(
                delta_result=_delta_result(ref, comp),
                ref_distance=ref["distance"],
                ref_brake=ref["brake"],
                ref_speed=ref["speed"],
                comp_distance=comp["distance"],
                comp_brake=comp["brake"],
                comp_speed=comp["speed"],
                corners=CORNERS,
                track_length=float(ref["distance"][-1]),
            )
        assert "ref_speed" in str(exc_info.value)

    def test_run_phase3_corner_degrades_honestly(self):
        """Through the orchestrator's Phase-3 wrapper the rejection becomes
        an honest degrade: (None, error) with the reason named — never a
        fabricated CornerAnalysisResult."""
        ref, comp = _wire_parsed_telemetry()
        result, error = run_phase3_corner(
            _delta_result(ref, comp), ref, comp, CORNERS,
            track_length=float(ref["distance"][-1]),
        )
        assert result is None
        assert error is not None
        assert "non-finite telemetry" in error
        assert "ref_speed" in error

    def test_clean_telemetry_still_analyses(self):
        """Control: finite input produces a real result — the rejection is
        surgical, not a blanket failure."""
        ref, comp = _wire_parsed_telemetry(poison_speed=False)
        result, error = run_phase3_corner(
            _delta_result(ref, comp), ref, comp, CORNERS,
            track_length=float(ref["distance"][-1]),
        )
        assert error is None
        assert result is not None
        assert len(result.corner_results) == 1
