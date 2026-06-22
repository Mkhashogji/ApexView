"""
G0 — Honest Acquisition: unit tests for the native acquisition layer.

Covers (per the G0 Phase 6 spec):
- gap-law boundary behaviour on synthetic dt arrays (uniform, jittered,
  injected 1.0 s hole, exact-3x boundary — exclusive)
- provenance completeness (every row tagged; only REAL_CAR/REAL_POS in G0)
- distance-integration parity against FastF1's own add_distance (1e-6 tier
  on identical input)
- Brake dtype preservation (boolean in -> boolean through the bundle;
  0.0/1.0 floats on the wire, matching the legacy golden serialisation)
- structured failure (NativeAcquisitionError; no silent fallback)

Runs inside the f1-api container (fastf1 + numpy available):
    cd apps/api && python -m pytest tests/test_native_acquisition.py -v
"""
import numpy as np
import pandas as pd
import pytest

import fastf1.core as fastf1_core

from app.services.telemetry.native_acquisition import (
    GAP_DT_MULTIPLIER,
    G0_ALLOWED_PROVENANCE,
    NativeAcquisitionError,
    PROVENANCE_COLUMN,
    Provenance,
    TelemetryBundle,
    acquire_native_bundle,
    detect_gaps,
)


# =============================================================================
# Helpers
# =============================================================================

def _make_car_frame(dts=None, n=40, v0=100.0, v1=300.0):
    """Synthetic car-data Telemetry frame with controllable dt sequence."""
    if dts is None:
        dts = np.full(n - 1, 0.25)
    t = np.concatenate([[0.0], np.cumsum(dts)])
    n = len(t)
    time = pd.to_timedelta(t, unit="s")
    return fastf1_core.Telemetry(pd.DataFrame({
        "Time": time,
        "SessionTime": time + pd.Timedelta(seconds=1000),
        "Speed": np.linspace(v0, v1, n),
        "Throttle": np.full(n, 50.0),
        "Brake": np.zeros(n, dtype=bool),
        "nGear": np.full(n, 5, dtype=np.int64),
        "RPM": np.full(n, 11000.0),
        "DRS": np.zeros(n, dtype=np.int64),
    }))


def _make_pos_frame(n=44):
    t = pd.to_timedelta(np.arange(n) * 0.24 + 0.05, unit="s")
    return fastf1_core.Telemetry(pd.DataFrame({
        "Time": t,
        "SessionTime": t + pd.Timedelta(seconds=1000),
        "X": np.linspace(0, 1000, n),
        "Y": np.linspace(0, 500, n),
        "Z": np.full(n, 10.0),
    }))


class FakeLap:
    """Minimal stand-in for a fastf1 Lap: stream accessors + item access."""

    def __init__(self, car=None, pos=None, lap_number=19,
                 lap_time=pd.Timedelta(seconds=90.641)):
        self._car = car if car is not None else _make_car_frame()
        self._pos = pos if pos is not None else _make_pos_frame()
        self._items = {"LapNumber": lap_number, "LapTime": lap_time}

    def get_car_data(self):
        if isinstance(self._car, Exception):
            raise self._car
        return self._car

    def get_pos_data(self):
        if isinstance(self._pos, Exception):
            raise self._pos
        return self._pos

    def __getitem__(self, key):
        return self._items[key]


# =============================================================================
# Gap law (detect_gaps)
# =============================================================================

class TestGapLaw:
    def test_uniform_dt_no_gaps(self):
        t = np.arange(0, 90, 0.25)
        d = np.linspace(0, 5000, len(t))
        assert detect_gaps(t, d) == []

    def test_jittered_dt_no_gaps(self):
        # Realistic jitter band 0.16-0.44 s (measured): all below 3x median.
        rng_dts = np.tile([0.16, 0.20, 0.24, 0.32, 0.36, 0.44], 20)
        t = np.concatenate([[0.0], np.cumsum(rng_dts)])
        d = np.linspace(0, 5000, len(t))
        assert detect_gaps(t, d) == []

    def test_injected_one_second_hole_detected(self):
        dts = np.full(60, 0.25)
        dts[30] = 1.0  # median stays 0.25 -> threshold 0.75 -> 1.0s is a gap
        t = np.concatenate([[0.0], np.cumsum(dts)])
        d = np.linspace(0, 5000, len(t))
        gaps = detect_gaps(t, d)
        assert len(gaps) == 1
        g = gaps[0]
        assert g["dt"] == pytest.approx(1.0, abs=1e-9)
        assert g["ratio"] == pytest.approx(4.0, abs=1e-9)
        assert g["t_start"] == pytest.approx(t[30], abs=1e-9)
        assert g["t_end"] == pytest.approx(t[31], abs=1e-9)
        # distance bounds bracket the hole
        assert g["d_start"] < g["d_end"]

    def test_exact_3x_boundary_is_exclusive(self):
        # dt == 3 x median must NOT be a gap (strict >).
        dts = np.full(60, 0.25)
        dts[30] = 0.75  # exactly 3x median
        t = np.concatenate([[0.0], np.cumsum(dts)])
        d = np.linspace(0, 5000, len(t))
        assert detect_gaps(t, d) == []
        # epsilon above the boundary IS a gap
        dts[30] = 0.75 + 1e-9
        t = np.concatenate([[0.0], np.cumsum(dts)])
        assert len(detect_gaps(t, d)) == 1

    def test_multiplier_constant_is_three(self):
        # The gap law is part of the G0 contract.
        assert GAP_DT_MULTIPLIER == 3.0

    def test_too_short_series(self):
        assert detect_gaps(np.array([0.0]), np.array([0.0])) == []
        assert detect_gaps(np.array([]), np.array([])) == []

    def test_combined_jitter_and_hole(self):
        # Median robustness under mixed regimes (review L5-10): realistic
        # jitter band PLUS one genuine 1.0 s dropout -> exactly one gap.
        jitter = np.tile([0.16, 0.20, 0.24, 0.32, 0.36, 0.44], 10)
        dts = np.concatenate([jitter[:30], [1.0], jitter[30:]])
        t = np.concatenate([[0.0], np.cumsum(dts)])
        d = np.linspace(0, 5000, len(t))
        gaps = detect_gaps(t, d)
        assert len(gaps) == 1
        assert gaps[0]["dt"] == pytest.approx(1.0, abs=1e-9)

    def test_two_holes_detected_in_order(self):
        dts = np.full(80, 0.25)
        dts[20] = 0.9
        dts[60] = 1.1
        t = np.concatenate([[0.0], np.cumsum(dts)])
        d = np.linspace(0, 5000, len(t))
        gaps = detect_gaps(t, d)
        assert len(gaps) == 2
        assert gaps[0]["t_start"] < gaps[1]["t_start"]
        assert gaps[0]["dt"] == pytest.approx(0.9, abs=1e-9)
        assert gaps[1]["dt"] == pytest.approx(1.1, abs=1e-9)


# =============================================================================
# Input validation (continuation review R1: NaN/NaT, monotonicity, dup stamps)
# =============================================================================

class TestInputValidation:
    def test_nan_speed_raises(self):
        car = _make_car_frame(n=30)
        car.loc[car.index[10], "Speed"] = np.nan
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert exc.value.stage == "validate_car"
        assert "Speed" in exc.value.reason

    def test_nat_time_raises(self):
        car = _make_car_frame(n=30)
        car.loc[car.index[5], "Time"] = pd.NaT
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert exc.value.stage == "validate_car"
        assert "Time" in exc.value.reason

    def test_non_monotonic_time_raises(self):
        dts = np.full(29, 0.25)
        dts[10] = -0.10  # out-of-order sample
        car = _make_car_frame(dts=dts)
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert "non-monotonic" in exc.value.reason

    def test_excessive_duplicate_timestamps_raise(self):
        # alternating 0 / 0.24 dts: median over positive dts would be biased
        # to 0.24 while the true cadence is 0.12 — gap law would be blinded.
        dts = np.tile([0.0, 0.24], 20)
        car = _make_car_frame(dts=dts)
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert "duplicate timestamps" in exc.value.reason

    def test_few_duplicates_tolerated(self):
        # one duplicate stamp out of 39 intervals (~2.6%) passes the 10% law
        dts = np.full(39, 0.25)
        dts[7] = 0.0
        bundle = acquire_native_bundle(FakeLap(car=_make_car_frame(dts=dts)), driver="PIA")
        assert bundle.meta["n_car"] == 40

    def test_nan_rpm_raises(self):
        car = _make_car_frame(n=30)
        car.loc[car.index[3], "RPM"] = np.nan
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert "RPM" in exc.value.reason


# =============================================================================
# Bundle acquisition: provenance, channels, structure
# =============================================================================

class TestBundleAcquisition:
    def test_provenance_complete_and_g0_restricted(self):
        bundle = acquire_native_bundle(FakeLap(), driver="PIA", session="t")
        car_prov = set(bundle.car_native[PROVENANCE_COLUMN].unique())
        pos_prov = set(bundle.pos_native[PROVENANCE_COLUMN].unique())
        assert car_prov == {Provenance.REAL_CAR.value}
        assert pos_prov == {Provenance.REAL_POS.value}
        # 100% of rows tagged
        assert bundle.car_native[PROVENANCE_COLUMN].notna().all()
        assert bundle.pos_native[PROVENANCE_COLUMN].notna().all()
        # only G0-allowed values appear anywhere
        assert (car_prov | pos_prov) <= G0_ALLOWED_PROVENANCE

    def test_reserved_provenance_values_exist_but_unused(self):
        # Defined now for enum stability across gates; must not appear in G0.
        assert Provenance.DERIVED_RPM.value == "DERIVED_RPM"
        assert Provenance.FUSED.value == "FUSED"
        assert Provenance.GAP.value == "GAP"
        assert Provenance.DERIVED_RPM.value not in G0_ALLOWED_PROVENANCE
        assert Provenance.FUSED.value not in G0_ALLOWED_PROVENANCE
        assert Provenance.GAP.value not in G0_ALLOWED_PROVENANCE

    def test_brake_bool_dtype_preserved_in_bundle(self):
        bundle = acquire_native_bundle(FakeLap(), driver="PIA", session="t")
        assert bundle.car_native["Brake"].dtype == np.dtype(bool)

    def test_distance_and_relative_distance_added(self):
        bundle = acquire_native_bundle(FakeLap(), driver="PIA", session="t")
        car = bundle.car_native
        assert "Distance" in car.columns
        assert "RelativeDistance" in car.columns
        d = car["Distance"].to_numpy()
        assert np.all(np.diff(d) >= 0)  # monotonic
        # FastF1's add_relative_distance ends at exactly 1.0 (measured)
        assert car["RelativeDistance"].iloc[-1] == pytest.approx(1.0, abs=1e-9)

    def test_meta_contents(self):
        bundle = acquire_native_bundle(FakeLap(), driver="PIA", session="t")
        m = bundle.meta
        assert m["schema_version"] == "native_v1"
        assert m["acquisition_mode"] == "native"
        assert m["n_car"] == len(bundle.car_native)
        assert m["n_pos"] == len(bundle.pos_native)
        assert m["median_dt_car"] == pytest.approx(0.25, abs=1e-6)
        assert m["gap_dt_multiplier"] == 3.0
        assert m["n_gaps"] == len(bundle.gaps) == 0
        assert set(m["lib_versions"]) == {"fastf1", "numpy", "pandas"}

    def test_gap_recorded_in_bundle(self):
        dts = np.full(40, 0.25)
        dts[20] = 1.0
        bundle = acquire_native_bundle(
            FakeLap(car=_make_car_frame(dts=dts)), driver="PIA", session="t")
        assert bundle.meta["n_gaps"] == 1
        assert bundle.gaps[0]["ratio"] == pytest.approx(4.0, abs=1e-9)

    def test_pos_native_exposed_but_independent(self):
        # pos_native is part of the bundle (substrate for later gates) and
        # carries its own row count, untouched by car-frame processing.
        bundle = acquire_native_bundle(FakeLap(), driver="PIA", session="t")
        assert isinstance(bundle, TelemetryBundle)
        assert len(bundle.pos_native) == 44
        assert "Distance" not in bundle.pos_native.columns  # nothing derived onto pos at G0


# =============================================================================
# Distance-integration parity (1e-6 tier)
# =============================================================================

class TestDistanceIntegrationParity:
    def test_bundle_distance_matches_explicit_integration(self):
        """
        FastF1's add_distance integrates cumulative Speed/3.6 * dt with
        dt[0] = Time[0] (verified empirically in diagnostics/g0). Asserted
        against the BUNDLE's Distance channel (review L5-8: testing the code
        under review, not the library in isolation) at the 1e-6 tier.
        """
        car = _make_car_frame(n=60, v0=80.0, v1=320.0)
        bundle = acquire_native_bundle(FakeLap(car=car), driver="PIA")
        d_bundle = bundle.car_native["Distance"].to_numpy()

        t = car["Time"].dt.total_seconds().to_numpy()
        v_ms = car["Speed"].to_numpy() / 3.6
        dt = np.diff(t, prepend=0.0)  # dt[0] = Time[0]
        d_explicit = np.cumsum(v_ms * dt)

        assert np.max(np.abs(d_bundle - d_explicit)) == pytest.approx(0.0, abs=1e-6)


# =============================================================================
# Wire-format parity (Brake bool -> 0.0/1.0 floats, as in legacy goldens)
# =============================================================================

class TestWireFormat:
    def test_brake_serialises_as_floats_like_legacy(self):
        from app.services.telemetry.fastf1_client import FastF1Client

        car = _make_car_frame(n=30)
        car["Brake"] = np.array([i % 2 == 0 for i in range(30)], dtype=bool)
        lap = FakeLap(car=car)
        bundle = acquire_native_bundle(lap, driver="PIA", session="t")

        client = FastF1Client()
        response = client._native_bundle_to_response("PIA", lap, bundle)

        # pydantic coerces bool -> float on the List[float] field, exactly as
        # the legacy merged path serialised (golden: 0.0/1.0 floats).
        assert all(isinstance(v, float) for v in response.brake)
        assert set(response.brake) <= {0.0, 1.0}
        assert response.brake[0] == 1.0 and response.brake[1] == 0.0
        # schema-frozen fields present
        assert response.lap_number == 19
        assert response.lap_time == pytest.approx(90.641, abs=1e-6)
        assert len(response.distance) == len(response.speed) == 30
        assert response.relative_distance[-1] == pytest.approx(1.0, abs=1e-9)
        assert response.time[0] == pytest.approx(0.0, abs=1e-9)


# =============================================================================
# Structured failure (no silent fallback)
# =============================================================================

class TestDownsampleBranch:
    def test_downsample_slices_all_arrays_consistently(self):
        """Review L5-9: the (dormant) downsample branch must slice every
        served array with the same indices — a missed array ships misaligned
        data. Exercised by lowering the threshold below the sample count."""
        from app.services.telemetry.fastf1_client import FastF1Client

        car = _make_car_frame(n=40)
        lap = FakeLap(car=car)
        bundle = acquire_native_bundle(lap, driver="PIA")

        client = FastF1Client()
        client.downsample_threshold = 10
        response = client._native_bundle_to_response("PIA", lap, bundle)

        lengths = {len(response.distance), len(response.speed), len(response.throttle),
                   len(response.brake), len(response.gear), len(response.rpm),
                   len(response.drs), len(response.relative_distance), len(response.time)}
        assert lengths == {10}
        # endpoints preserved by index-based selection
        full_d = bundle.car_native["Distance"].to_numpy()
        assert response.distance[0] == pytest.approx(float(full_d[0]), abs=1e-9)
        assert response.distance[-1] == pytest.approx(float(full_d[-1]), abs=1e-9)


class TestGapIntervalWireFormat:
    def test_gap_interval_serializes_camelcase_dstart(self):
        """Review L5-4: pin the wire keys the orchestrator's
        _gap_overlaps_zone consumes (dStart/dEnd) — a rename on either side
        would silently zero all gap flags with both suites green."""
        from app.models.dto import GapInterval

        gap = GapInterval(t_start=1.0, t_end=2.0, d_start=100.0, d_end=150.0,
                          dt=1.0, ratio=4.0)
        wire = gap.model_dump(by_alias=True)
        assert set(wire.keys()) == {"tStart", "tEnd", "dStart", "dEnd", "dt", "ratio"}
        assert wire["dStart"] == 100.0
        assert wire["dEnd"] == 150.0


class TestNativeAcquisitionError:
    def test_empty_car_frame_raises(self):
        empty = fastf1_core.Telemetry(pd.DataFrame())
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=empty), driver="PIA", session="s1")
        assert exc.value.stage == "get_car_data"
        detail = exc.value.to_detail()
        assert detail["error"] == "native_acquisition_failed"
        assert detail["driver"] == "PIA"
        assert detail["session"] == "s1"

    def test_missing_channel_raises(self):
        car = _make_car_frame(n=20)
        car = car.drop(columns=["Speed"])
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(car=car), driver="PIA")
        assert "Speed" in exc.value.reason

    def test_stream_exception_wrapped(self):
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(
                FakeLap(car=RuntimeError("telemetry source offline")), driver="RUS")
        assert exc.value.stage == "get_car_data"
        assert "offline" in exc.value.reason

    def test_empty_pos_frame_raises(self):
        empty = fastf1_core.Telemetry(pd.DataFrame())
        with pytest.raises(NativeAcquisitionError) as exc:
            acquire_native_bundle(FakeLap(pos=empty), driver="PIA")
        assert exc.value.stage == "get_pos_data"
