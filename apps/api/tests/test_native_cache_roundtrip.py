"""
G0 continuation §2 / Post-G0 hardening (Prompt A) — native Parquet cache
round-trip (permanent integration test).

GOVERNING REQUIREMENT: the round-trip is exercised through the REAL service
write method a live request invokes — route GET /telemetry ->
FastF1Client.get_telemetry (dispatcher) -> _get_telemetry_native ->
_get_telemetry_native_impl (the cache write). The earlier version called the
serializer helper (_native_cache_row) directly, so it passed even while the
production write path stored Brake as a float and omitted the provenance
columns — false confidence over dead code. These tests drive the production
path on a synthetic FakeLap (no FastF1 session, no network) and assert the
cache file is byte-for-byte as honest as data served live.

A bundle written to the versioned Parquet key, read back COLD (a fresh python
subprocess — zero shared in-memory state), must preserve:
- every channel's values (1e-6 tier),
- Brake as JSON booleans (bundle bool dtype fidelity, not 0.0/1.0 wire floats),
- provenance columns intact (REAL_CAR / REAL_POS),
- gap intervals intact (exact),
- meta intact (median dts, sample counts, schema version).

Negative cases: a legacy-schema frame and a wrong-schema_version frame placed
under the native key are each REFUSED by the read guard (read -> None ->
re-materialisation), never silently parsed as native.

Runs inside the f1-api container: python -m pytest tests/test_native_cache_roundtrip.py -v
"""
import asyncio
import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

import fastf1.core as fastf1_core

from app.services.cache.parquet_cache import ParquetCache
from app.services.telemetry.fastf1_client import (
    FastF1Client,
    NATIVE_TELEMETRY_DATA_TYPE,
)
from app.services.telemetry.native_acquisition import acquire_native_bundle

# reuse the synthetic-lap helpers from the acquisition suite
from tests.test_native_acquisition import FakeLap, _make_car_frame


COLD_READER = r"""
import json, sys
import pyarrow.parquet as pq
df = pq.read_table(sys.argv[1]).to_pandas()
print(df.to_json(orient="records"))
"""

# Session string that _parse_session_id accepts (season_round_name); the lap is
# injected via monkeypatch, so the values only need to parse.
TEST_SESSION = "2025_8_Qualifying"


def _make_bundle_with_gap():
    """Deterministic synthetic lap: mixed boolean Brake + exactly one gap."""
    dts = np.full(39, 0.25)
    dts[20] = 1.0  # one genuine gap
    car = _make_car_frame(dts=dts)
    car["Brake"] = np.array([i % 3 == 0 for i in range(len(car))], dtype=bool)
    lap = FakeLap(car=car)
    return lap, acquire_native_bundle(lap, driver="PIA", session="rt_test")


class _FakeSession:
    """Stands in for a loaded FastF1 session; lap is injected separately."""

    def load(self):  # no network
        return None


def _materialize_via_production(client, tmp_path, fake_lap, monkeypatch):
    """
    Drive the REAL production write: get_telemetry -> _get_telemetry_native ->
    _get_telemetry_native_impl (which builds the bundle from `fake_lap` and
    writes the Parquet cache row). Returns the single written *.parquet path.

    Only the FastF1 boundary is stubbed: fastf1.get_session (no network) and
    _select_fastest_valid_lap (returns the synthetic lap). Everything from
    acquire_native_bundle through the cache write is the unmodified service code.
    """
    client.cache = ParquetCache(cache_dir=tmp_path)
    monkeypatch.setattr(
        "app.services.telemetry.fastf1_client.fastf1.get_session",
        lambda *a, **k: _FakeSession())
    monkeypatch.setattr(
        client, "_select_fastest_valid_lap", lambda *a, **k: fake_lap)

    # session_part=None so the cache write actually fires (Q3 would bypass it);
    # acquisition="native" pins the native dispatcher regardless of env default.
    result = asyncio.run(client.get_telemetry(
        TEST_SESSION, ["PIA"], session_part=None, acquisition="native"))
    assert len(result) == 1 and result[0].driver == "PIA"

    files = list(tmp_path.glob("*.parquet"))
    assert len(files) == 1, f"expected one parquet file, found {files}"
    assert NATIVE_TELEMETRY_DATA_TYPE in files[0].name  # versioned keyspace
    return files[0]


class TestNativeCacheRoundTrip:
    def test_production_write_cold_round_trip(self, tmp_path, monkeypatch):
        """Materialise via the real write path, cold-read from disk, and prove
        the cached row is as honest as data served live."""
        lap, bundle = _make_bundle_with_gap()
        client = FastF1Client()
        parquet = _materialize_via_production(client, tmp_path, lap, monkeypatch)

        out = subprocess.run(
            [sys.executable, "-c", COLD_READER, str(parquet)],
            capture_output=True, text=True, check=True)
        records = json.loads(out.stdout)
        assert len(records) == 1
        cold = records[0]

        # --- PRIMARY discriminator: Brake survives as JSON booleans -----------
        # (pre-fix the production write stored telemetry_response.brake — wire
        # floats — so this fails cleanly; post-fix it is the bundle's booleans.)
        brake_cold = json.loads(cold["brake"])
        assert all(isinstance(b, bool) for b in brake_cold), (
            f"Brake must round-trip as booleans, got {set(type(b).__name__ for b in brake_cold)}")
        assert brake_cold == bundle.car_native["Brake"].tolist()

        # provenance columns present, complete, only REAL_CAR / REAL_POS
        assert json.loads(cold["provenance_car"]) == ["REAL_CAR"]
        assert json.loads(cold["provenance_pos"]) == ["REAL_POS"]

        # channel values, 1e-6 tier
        for field, original in (
            ("distance", bundle.car_native["Distance"].tolist()),
            ("speed", bundle.car_native["Speed"].tolist()),
            ("throttle", bundle.car_native["Throttle"].tolist()),
        ):
            assert json.loads(cold[field]) == pytest.approx(original, abs=1e-6)
        assert json.loads(cold["gear"]) == [int(g) for g in bundle.car_native["nGear"]]

        # gaps intact (exact)
        gaps_cold = json.loads(cold["gaps"])
        assert len(gaps_cold) == 1
        for k in ("t_start", "t_end", "d_start", "d_end", "dt", "ratio"):
            assert gaps_cold[0][k] == pytest.approx(bundle.gaps[0][k], abs=1e-9)

        # meta intact
        meta_cold = json.loads(cold["meta"])
        assert meta_cold["schema_version"] == "native_v1"
        assert meta_cold["n_car"] == bundle.meta["n_car"]
        assert meta_cold["n_pos"] == bundle.meta["n_pos"]
        assert meta_cold["median_dt_car"] == pytest.approx(bundle.meta["median_dt_car"], abs=1e-9)
        assert meta_cold["median_dt_pos"] == pytest.approx(bundle.meta["median_dt_pos"], abs=1e-9)
        assert meta_cold["n_gaps"] == 1

    def test_production_write_matches_helper(self, tmp_path, monkeypatch):
        """Re-divergence guard: the row the production path writes must equal
        the row _native_cache_row produces for the same lap (so the write can
        never silently drift away from the single serialization source again)."""
        lap, bundle = _make_bundle_with_gap()
        client = FastF1Client()
        _materialize_via_production(client, tmp_path, lap, monkeypatch)

        # what production actually wrote (read back from disk)
        prod_df = client.cache.read(
            TEST_SESSION, NATIVE_TELEMETRY_DATA_TYPE, drivers="PIA", lap_type="fastest")
        assert prod_df is not None
        prod_row = prod_df.iloc[0].to_dict()

        # what the single serialization source produces for the same lap
        expected = client._native_cache_row(
            "PIA", client._native_bundle_to_response("PIA", lap, bundle), bundle)

        assert set(prod_row.keys()) == set(expected.keys())
        for k, v in expected.items():
            if k == "lap_time":
                assert prod_row[k] == pytest.approx(v, abs=1e-9)
            else:
                assert prod_row[k] == v, f"column {k} diverged: {prod_row[k]!r} != {v!r}"

    def test_warm_read_reconstructs_identical_response(self, tmp_path):
        """The service-side read path must reproduce the exact wire response
        (pydantic re-coerces the cached booleans to 0.0/1.0 floats)."""
        lap, bundle = _make_bundle_with_gap()
        client = FastF1Client()
        fresh = client._native_bundle_to_response("PIA", lap, bundle)
        row = client._native_cache_row("PIA", fresh, bundle)

        cache = ParquetCache(cache_dir=tmp_path)
        cache.write(pd.DataFrame([row]), "rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                    drivers="PIA", lap_type="fastest")
        df = cache.read("rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                        drivers="PIA", lap_type="fastest")
        assert df is not None
        rebuilt = client._native_row_to_response("PIA", df.iloc[0])
        assert rebuilt is not None
        assert rebuilt.model_dump() == fresh.model_dump()  # wire-identical

    def test_legacy_schema_frame_refused(self, tmp_path):
        """Negative case: a legacy-shaped frame under the native key must be
        refused (None -> re-materialise), never silently parsed as native."""
        legacy_row = {
            "driver": "PIA", "lap_number": 19, "lap_time": 90.641,
            "distance": json.dumps([0.0, 10.0]), "speed": json.dumps([100.0, 110.0]),
            "throttle": json.dumps([50.0, 60.0]), "brake": json.dumps([0.0, 1.0]),
            "gear": json.dumps([5, 5]),
            "relative_distance": None, "time": None, "rpm": None, "drs": None,
            # no meta / provenance / gaps columns — legacy shape
        }
        cache = ParquetCache(cache_dir=tmp_path)
        cache.write(pd.DataFrame([legacy_row]), "rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                    drivers="PIA", lap_type="fastest")
        df = cache.read("rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                        drivers="PIA", lap_type="fastest")
        client = FastF1Client()
        assert client._native_row_to_response("PIA", df.iloc[0]) is None

    def test_wrong_schema_version_refused(self, tmp_path):
        lap, bundle = _make_bundle_with_gap()
        client = FastF1Client()
        response = client._native_bundle_to_response("PIA", lap, bundle)
        row = client._native_cache_row("PIA", response, bundle)
        meta = json.loads(row["meta"])
        meta["schema_version"] = "native_v999"  # future incompatible schema
        row["meta"] = json.dumps(meta)

        cache = ParquetCache(cache_dir=tmp_path)
        cache.write(pd.DataFrame([row]), "rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                    drivers="PIA", lap_type="fastest")
        df = cache.read("rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                        drivers="PIA", lap_type="fastest")
        assert client._native_row_to_response("PIA", df.iloc[0]) is None
