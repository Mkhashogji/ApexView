"""
Post-G0 hardening (Prompt B) — legacy cache-poisoning isolation regression test.

The legacy telemetry path (_get_telemetry_legacy) reads the Parquet cache only
for UNFILTERED requests (`if not session_part:`), but historically WROTE the
result under the same unfiltered key regardless of session_part. The cache key
carries no session_part component (data_type="telemetry", drivers, lap_type),
so a session_part-filtered (e.g. Q3) request stored a narrow slice under the
"whole session" key — and a later unfiltered request was served that poisoned
fragment. Legacy is harness-only and bypassed in normal operation, but the
emergency rollback path it exists to provide must not silently serve incomplete
data.

These tests drive the REAL dispatcher (get_telemetry(..., acquisition="legacy"))
and stub only the FastF1 boundary, mirroring the native-path test discipline.
The two poisoning tests FAIL on the pre-fix write gating and PASS after it is
gated to match the read boundary; the inverse-sanity test passes either way
(normal unfiltered caching must keep working).

Runs inside the f1-api container: python -m pytest tests/test_legacy_cache_isolation.py -v
"""
import asyncio
import json

import numpy as np
import pandas as pd

from app.services.cache.parquet_cache import ParquetCache
from app.services.telemetry.fastf1_client import FastF1Client

# _parse_session_id-parseable; the lap is injected via monkeypatch.
TEST_SESSION = "2025_8_Qualifying"
LEGACY_DATA_TYPE = "telemetry"  # legacy (pre-G0) cache key namespace


def _merged_frame(n=10):
    """A FastF1 get_telemetry()-shaped merged frame (plain DataFrame is enough —
    the legacy path only indexes columns and .values)."""
    return pd.DataFrame({
        "Distance": np.linspace(0.0, 1000.0, n),
        "Speed": np.linspace(100.0, 300.0, n),
        "Throttle": np.full(n, 50.0),
        "Brake": np.array([i % 2 == 0 for i in range(n)], dtype=bool),
        "nGear": np.full(n, 5, dtype=np.int64),
        "RPM": np.full(n, 11000, dtype=np.int64),
        "DRS": np.zeros(n, dtype=np.int64),
        "RelativeDistance": np.linspace(0.0, 1.0, n),
        "Time": pd.to_timedelta(np.arange(n) * 0.25, unit="s"),
    })


class _FakeMergedLap:
    empty = False

    def __init__(self, lap_number):
        self._ln = lap_number

    def __getitem__(self, key):
        return {"LapTime": pd.Timedelta(seconds=90.6),
                "LapNumber": self._ln}[key]

    def get_telemetry(self):
        return _merged_frame()


class _FakeLaps:
    def __init__(self, lap_number=1):
        self._ln = lap_number

    def __len__(self):
        return 1

    def pick_driver(self, driver):
        return self

    def pick_fastest(self):
        return _FakeMergedLap(self._ln)


class _FakeSession:
    session_status = None

    def __init__(self):
        self.laps = _FakeLaps()

    def load(self):
        return None


def _stub_legacy(client, tmp_path, monkeypatch):
    """Stub the FastF1 boundary so the legacy path runs offline. The lap_number
    differs by session_part (99 when filtered, 1 when unfiltered) so a poisoned
    unfiltered read is distinguishable from a correct one."""
    client.cache = ParquetCache(cache_dir=tmp_path)
    monkeypatch.setattr(
        "app.services.telemetry.fastf1_client.fastf1.get_session",
        lambda *a, **k: _FakeSession())
    monkeypatch.setattr(
        client, "_filter_laps_by_session_part",
        lambda laps, session_part, session_status: _FakeLaps(99 if session_part else 1))
    monkeypatch.setattr(client, "_filter_valid_laps", lambda laps: laps)


def _legacy(client, session_part):
    result = asyncio.run(client.get_telemetry(
        TEST_SESSION, ["PIA"], session_part=session_part, acquisition="legacy"))
    # legacy swallows exceptions into [] — a broken stub must not pass silently
    assert len(result) == 1 and result[0].driver == "PIA", \
        f"legacy path returned {result!r} (stub or path error)"
    return result


class TestLegacyCacheIsolation:
    def test_q3_request_does_not_poison_unfiltered_key(self, tmp_path, monkeypatch):
        """PRIMARY discriminator: a session_part-filtered request must not write
        under the unfiltered cache key."""
        client = FastF1Client()
        _stub_legacy(client, tmp_path, monkeypatch)

        _legacy(client, session_part="Q3")

        poisoned = client.cache.read(
            TEST_SESSION, LEGACY_DATA_TYPE, drivers="PIA", lap_type="fastest")
        assert poisoned is None, (
            "Q3-filtered telemetry was written under the unfiltered key — "
            "a later unfiltered request would be served this poisoned fragment")

    def test_unfiltered_request_not_served_q3_fragment(self, tmp_path, monkeypatch):
        """End-to-end consequence: after a Q3 request, an unfiltered request must
        return the full lap (lap 1), not the cached Q3 fragment (lap 99)."""
        client = FastF1Client()
        _stub_legacy(client, tmp_path, monkeypatch)

        _legacy(client, session_part="Q3")          # would poison the key pre-fix
        result = _legacy(client, session_part=None)  # unfiltered read

        assert result[0].lap_number == 1, (
            f"unfiltered request served lap {result[0].lap_number} — expected the "
            f"full lap (1), got the Q3 fragment (99) from a poisoned cache")

    def test_unfiltered_request_still_caches(self, tmp_path, monkeypatch):
        """Inverse sanity (passes pre- and post-fix): normal unfiltered caching
        must keep round-tripping — the gating fix must not disable it."""
        client = FastF1Client()
        _stub_legacy(client, tmp_path, monkeypatch)

        first = _legacy(client, session_part=None)
        cached = client.cache.read(
            TEST_SESSION, LEGACY_DATA_TYPE, drivers="PIA", lap_type="fastest")
        assert cached is not None, "unfiltered request must populate the cache"

        second = _legacy(client, session_part=None)  # served from cache
        assert first[0].lap_number == second[0].lap_number == 1
