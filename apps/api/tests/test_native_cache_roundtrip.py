"""
G0 continuation §2 — native Parquet cache round-trip (permanent integration test).

Writes a TelemetryBundle-derived cache row to a versioned Parquet file, reads
it back COLD (a fresh python subprocess — zero shared in-memory state) and
asserts equality with the original on:
- every channel's values (1e-6 tier),
- Brake survives as JSON booleans (bundle bool dtype fidelity, not the
  0.0/1.0 wire floats),
- provenance columns intact (REAL_CAR / REAL_POS),
- gap intervals intact (exact),
- meta intact (median dts, sample counts, schema version).

Negative case: a legacy-schema frame placed under the native key is REFUSED
by the schema guard (read returns None -> re-materialisation), never silently
parsed as native.

Runs inside the f1-api container: python -m pytest tests/test_native_cache_roundtrip.py -v
"""
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


def _make_bundle_with_gap():
    dts = np.full(39, 0.25)
    dts[20] = 1.0  # one genuine gap
    car = _make_car_frame(dts=dts)
    car["Brake"] = np.array([i % 3 == 0 for i in range(len(car))], dtype=bool)
    lap = FakeLap(car=car)
    return lap, acquire_native_bundle(lap, driver="PIA", session="rt_test")


class TestNativeCacheRoundTrip:
    def test_cold_subprocess_round_trip(self, tmp_path):
        lap, bundle = _make_bundle_with_gap()
        client = FastF1Client()
        response = client._native_bundle_to_response("PIA", lap, bundle)
        row = client._native_cache_row("PIA", response, bundle)

        cache = ParquetCache(cache_dir=tmp_path)
        assert cache.write(pd.DataFrame([row]), "rt_test", NATIVE_TELEMETRY_DATA_TYPE,
                           drivers="PIA", lap_type="fastest")
        files = list(tmp_path.glob("*.parquet"))
        assert len(files) == 1
        assert NATIVE_TELEMETRY_DATA_TYPE in files[0].name  # versioned keyspace

        # --- COLD read: fresh process, no in-memory state ------------------
        out = subprocess.run(
            [sys.executable, "-c", COLD_READER, str(files[0])],
            capture_output=True, text=True, check=True)
        records = json.loads(out.stdout)
        assert len(records) == 1
        cold = records[0]

        # channel values, 1e-6 tier
        for field, original in (
            ("distance", bundle.car_native["Distance"].tolist()),
            ("speed", bundle.car_native["Speed"].tolist()),
            ("throttle", bundle.car_native["Throttle"].tolist()),
        ):
            assert json.loads(cold[field]) == pytest.approx(original, abs=1e-6)
        assert json.loads(cold["gear"]) == [int(g) for g in bundle.car_native["nGear"]]

        # Brake: JSON booleans, not floats — bundle dtype fidelity
        brake_cold = json.loads(cold["brake"])
        assert all(isinstance(b, bool) for b in brake_cold)
        assert brake_cold == bundle.car_native["Brake"].tolist()

        # provenance intact
        assert json.loads(cold["provenance_car"]) == ["REAL_CAR"]
        assert json.loads(cold["provenance_pos"]) == ["REAL_POS"]

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
