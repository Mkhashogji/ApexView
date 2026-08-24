"""
WU-2b: ingress finiteness validation at fetch_driver_telemetry, plus the
WU-2a degrade surfacing (errors[] mirrored into warnings[]).

fetch_driver_telemetry is the seam every telemetry array crosses on the
orchestrated path — and the seam G1's harvested arrays will cross. Before
WU-2b its only validation was presence/non-emptiness of distance and speed;
a non-empty list passed regardless of content, so JSON nulls (the wire form
of an API-side NaN), real NaN (the legacy-cache round-trip form), and ±inf
all sailed through. The channels time and relative_distance additionally
never pass through _safe_array at all — they feed the Tier-1/2 delta path
directly, where a non-finite value propagates unrepaired and can break the
closure invariant silently. This file pins the ingress contract per channel.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from core.errors import NonFiniteTelemetryError
from services.performance_orchestrator import (
    CornerInput,
    PerformanceInsightsConfig,
    fetch_driver_telemetry,
    orchestrate_performance_insights,
)

N = 24


def _clean_payload():
    """A wire-shaped /telemetry response item (camelCase optional keys)."""
    return {
        "driver": "PIA",
        "lapNumber": 19,
        "lapTime": 90.641,
        "distance": [float(i) * 15.0 for i in range(N)],
        "speed": [250.0 - i for i in range(N)],
        "brake": [0.0] * N,
        "throttle": [100.0] * N,
        "relativeDistance": [i / (N - 1) for i in range(N)],
        "time": [i * 0.25 for i in range(N)],
    }


def _client_returning(payload_item):
    client = AsyncMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = [payload_item]
    client.get.return_value = resp
    return client


def _fetch(client):
    return asyncio.run(fetch_driver_telemetry(
        client, "2025_2_Qualifying", "PIA", "Q3", None))


class TestIngressFinitenessValidation:
    """Per-channel: a non-finite value produces (None, error) naming the
    channel — the function's established failure contract."""

    @pytest.mark.parametrize("wire_key,channel", [
        ("distance", "distance"),
        ("speed", "speed"),
        ("brake", "brake"),
        ("relativeDistance", "relative_distance"),
        ("time", "time"),
    ])
    def test_json_null_rejected_per_channel(self, wire_key, channel):
        payload = _clean_payload()
        payload[wire_key] = list(payload[wire_key])
        payload[wire_key][5] = None  # what the wire delivers for an API-side NaN
        telemetry, error = _fetch(_client_returning(payload))
        assert telemetry is None
        assert error is not None and channel in error

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_real_nonfinite_rejected(self, bad):
        # the legacy Parquet cache round-trips a literal NaN token back to a
        # real float('nan'); inf is accepted by pydantic and was previously
        # uncaught everywhere
        payload = _clean_payload()
        payload["time"] = list(payload["time"])
        payload["time"][2] = bad
        telemetry, error = _fetch(_client_returning(payload))
        assert telemetry is None
        assert error is not None and "time" in error

    def test_clean_payload_passes_through_unchanged(self):
        payload = _clean_payload()
        telemetry, error = _fetch(_client_returning(payload))
        assert error is None
        assert telemetry is not None
        assert telemetry["distance"] == payload["distance"]
        assert telemetry["speed"] == payload["speed"]
        assert telemetry["brake"] == payload["brake"]
        assert telemetry["relative_distance"] == payload["relativeDistance"]
        assert telemetry["time"] == payload["time"]
        assert telemetry["lap_time"] == payload["lapTime"]

    def test_absent_optionals_still_pass(self):
        """The mock head omits relativeDistance/time entirely — absence keeps
        its existing meaning (Tier-3 routing), only present values are
        validated."""
        payload = _clean_payload()
        del payload["relativeDistance"]
        del payload["time"]
        telemetry, error = _fetch(_client_returning(payload))
        assert error is None
        assert telemetry is not None
        assert telemetry["relative_distance"] is None
        assert telemetry["time"] is None


class TestDegradeSurfacedInWarnings:
    """WU-2a degrade path: a NonFiniteTelemetryError inside Phase 3 must
    surface in result.warnings — the only field the frontend renders — not
    only in result.errors."""

    def test_phase3_rejection_reaches_warnings(self):
        config = PerformanceInsightsConfig(
            session_id="2025_2_Qualifying",
            reference_driver="PIA",
            compare_drivers=["RUS"],
            corners=[CornerInput(corner_number=1, apex_distance=180.0,
                                 name="T1", corner_type="slow")],
            mode="engineer",
            session_part="Q3",
            track_length=345.0,
        )
        client = _client_returning(_clean_payload())
        boom = NonFiniteTelemetryError("ref_speed", 2, N, [3, 7])
        with patch("services.performance_orchestrator.analyze_corners_v2",
                   side_effect=boom):
            result = asyncio.run(orchestrate_performance_insights(config, client))

        prefix = "corner analysis rejected non-finite telemetry"
        matching_errors = [e for e in result.errors if prefix in e]
        assert matching_errors, f"expected a '{prefix}' error, got {result.errors}"
        assert "ref_speed" in matching_errors[0]
        # the same reason must be user-visible
        assert any(prefix in w for w in result.warnings), (
            f"rejection not mirrored into warnings[]: {result.warnings}"
        )
