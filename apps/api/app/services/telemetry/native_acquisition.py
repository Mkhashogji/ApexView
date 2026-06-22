"""
Native dual-stream telemetry acquisition (G0 — Honest Acquisition).

Replaces FastF1's high-level ``lap.get_telemetry()`` on the qualifying analysis
path. ``get_telemetry()`` merges two interleaved ~4 Hz streams — car data
(Speed/RPM/Throttle/Brake/nGear/DRS) and position data (X/Y/Z) — onto the
union of their timestamps. The two streams share zero timestamps, so roughly
half of every car channel in the merged frame is linear interpolation
presented as measurement (measured: diagnostics/granularity/REPORT.md).
This module acquires the two streams separately, tags every row with
provenance, detects acquisition gaps, and never interpolates.

G0 design decisions
-------------------
- ``Distance`` on the car frame comes from FastF1's ``add_distance()``
  (cumulative ``Speed/3.6 * dt`` over the car frame's own native dt, with
  ``dt[0] = Time[0]``). The library function is used rather than a local
  re-implementation so integration semantics stay identical to FastF1's
  elsewhere; the unit suite asserts 1e-6 parity against an explicit
  integration on identical input (test_native_acquisition.py).
- ``RelativeDistance`` comes from FastF1's ``add_relative_distance()``
  (Distance / Distance.iloc[-1]; measured to end at exactly 1.0 on the car
  frame, vs 0.9996 on the legacy merged frame — np.interp clamping makes the
  delta-grid endpoint behaviour identical).
- ``pos_native`` is acquired, tagged, cached and exposed in the bundle but is
  consumed by NOTHING downstream at G0 — it is the substrate for later gates.
- Gaps (consecutive car-sample dt STRICTLY greater than
  ``GAP_DT_MULTIPLIER x median dt``) are detected and recorded as metadata
  only. The Phase-2 delta grid still interpolates end-to-end across gaps:
  severing the grid would break the closure invariant
  (``delta[-1] == official gap``); modelling uncertainty growth through gaps
  is the fusion track's job at a later gate.
- No silent fallback: any acquisition failure raises
  ``NativeAcquisitionError``. Callers must surface it, never swallow it.

Provenance vocabulary
---------------------
``REAL_CAR`` and ``REAL_POS`` are the only values that may appear in G0
output. ``DERIVED_RPM``, ``FUSED`` and ``GAP`` are reserved for later gates
(RPM-ratio harvesting, stream fusion, gap-marker rows) and are defined now so
the enum is stable across gates; tests assert they remain unused at G0.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "native_v1"

# Gap law: an inter-sample interval is a gap when dt is STRICTLY greater than
# this multiple of the lap's median car dt. 3x median (~0.72 s on reference
# data) catches the measured 0.76-0.82 s dropouts while passing normal
# 0.16-0.44 s jitter. Boundary is exclusive: dt == 3 x median is NOT a gap.
GAP_DT_MULTIPLIER = 3.0


class Provenance(str, Enum):
    """Row-level provenance tags for native telemetry frames."""

    REAL_CAR = "REAL_CAR"      # native car-data measurement
    REAL_POS = "REAL_POS"      # native position-data measurement
    # --- reserved for later gates; MUST NOT appear in G0 output ---
    DERIVED_RPM = "DERIVED_RPM"  # speed derived from RPM/gear ratios
    FUSED = "FUSED"              # multi-stream fusion estimate
    GAP = "GAP"                  # synthetic gap-marker row


#: Provenance values permitted in G0 bundles (asserted by tests).
G0_ALLOWED_PROVENANCE = {Provenance.REAL_CAR.value, Provenance.REAL_POS.value}

PROVENANCE_COLUMN = "Provenance"

# Channels required on the car frame for the analysis path to function.
REQUIRED_CAR_CHANNELS = ["Speed", "Throttle", "Brake", "nGear", "Time", "SessionTime"]
REQUIRED_POS_CHANNELS = ["X", "Y", "Z", "Time", "SessionTime"]


class NativeAcquisitionError(Exception):
    """
    Structured acquisition failure. Raised — never swallowed — when the native
    path cannot produce a valid bundle (ground rule: no silent fallback to
    ``get_telemetry()``).
    """

    def __init__(self, stage: str, reason: str, driver: Optional[str] = None,
                 session: Optional[str] = None):
        self.stage = stage
        self.reason = reason
        self.driver = driver
        self.session = session
        super().__init__(f"native acquisition failed at {stage}: {reason}"
                         + (f" (driver={driver})" if driver else "")
                         + (f" (session={session})" if session else ""))

    def to_detail(self) -> Dict[str, Any]:
        """HTTP-friendly structured detail."""
        return {
            "error": "native_acquisition_failed",
            "stage": self.stage,
            "reason": self.reason,
            "driver": self.driver,
            "session": self.session,
        }


@dataclass
class TelemetryBundle:
    """
    Per-lap native acquisition product.

    Attributes:
        car_native: car-data frame (Speed, RPM, Throttle, Brake [bool dtype
            preserved], nGear, DRS, Time, SessionTime) plus ``Distance``,
            ``RelativeDistance`` and ``Provenance`` (= REAL_CAR on every row).
        pos_native: position frame (X, Y, Z, Time, SessionTime) plus
            ``Provenance`` (= REAL_POS). Unused downstream at G0.
        gaps: acquisition gaps on the car stream (see ``detect_gaps``).
        meta: stream statistics, schema version, library versions.
    """

    car_native: pd.DataFrame
    pos_native: pd.DataFrame
    gaps: List[Dict[str, float]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


def _median_dt(time_s: np.ndarray) -> float:
    """Median of positive consecutive dt values, in seconds."""
    dt = np.diff(time_s)
    dt = dt[dt > 0]
    return float(np.median(dt)) if dt.size else 0.0


def detect_gaps(
    time_s: np.ndarray,
    distance_m: np.ndarray,
    multiplier: float = GAP_DT_MULTIPLIER,
) -> List[Dict[str, float]]:
    """
    Detect acquisition gaps: intervals where consecutive dt is STRICTLY
    greater than ``multiplier x median(dt)``.

    Args:
        time_s: lap-relative sample times (seconds), monotonically increasing.
        distance_m: per-sample distance (metres), same length as ``time_s``.
        multiplier: gap threshold multiplier (default ``GAP_DT_MULTIPLIER``).

    Returns:
        List of gap dicts with both time and distance bounds:
        ``{t_start, t_end, d_start, d_end, dt, ratio}``. Distance bounds are
        what corner-zone overlap checks consume; time bounds are the primary
        definition. Boundary is exclusive: ``dt == multiplier * median`` is
        NOT a gap (unit-tested).
    """
    time_s = np.asarray(time_s, dtype=float)
    distance_m = np.asarray(distance_m, dtype=float)
    if time_s.size < 2:
        return []

    median = _median_dt(time_s)
    if median <= 0:
        return []
    threshold = multiplier * median

    gaps: List[Dict[str, float]] = []
    dts = np.diff(time_s)
    for i, dt in enumerate(dts):
        if dt > threshold:  # strict: dt == threshold passes
            gaps.append({
                "t_start": float(time_s[i]),
                "t_end": float(time_s[i + 1]),
                "d_start": float(distance_m[i]),
                "d_end": float(distance_m[i + 1]),
                "dt": float(dt),
                "ratio": float(dt / median),
            })
    return gaps


def _lib_versions() -> Dict[str, str]:
    import fastf1
    return {
        "fastf1": fastf1.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }


def acquire_native_bundle(lap, driver: Optional[str] = None,
                          session: Optional[str] = None) -> TelemetryBundle:
    """
    Acquire the native dual-stream bundle for one lap.

    Args:
        lap: a FastF1 ``Lap`` object (e.g. from ``laps.pick_fastest()``).
        driver/session: identifiers for structured error reporting only.

    Returns:
        TelemetryBundle with provenance-tagged car and pos frames, gap list,
        and meta.

    Raises:
        NativeAcquisitionError: on any failure — empty streams, missing
        channels, or FastF1 errors. Never falls back to ``get_telemetry()``.
    """
    # --- car stream ---------------------------------------------------------
    try:
        car = lap.get_car_data()
    except Exception as exc:
        raise NativeAcquisitionError("get_car_data", str(exc), driver, session) from exc
    if car is None or len(car) == 0:
        raise NativeAcquisitionError("get_car_data", "empty car-data frame", driver, session)
    missing = [c for c in REQUIRED_CAR_CHANNELS if c not in car.columns]
    if missing:
        raise NativeAcquisitionError(
            "get_car_data", f"missing channels: {missing}", driver, session)

    # --- input validation (G0 continuation review: findings R1/L1-2/L3-2..5) --
    # Honest acquisition forbids fabricated values: a NaN/NaT sample would cast
    # to an arbitrary integer downstream (e.g. nGear.astype(int)) while wearing
    # the REAL_CAR tag, and a NaN dt is INVISIBLE to the gap law (NaN > x is
    # False), hiding a dropout co-located with the corrupt sample. Non-monotonic
    # time corrupts distance integration and gap bounds; excessive duplicate
    # timestamps bias the gap-law median upward, hiding genuine dropouts.
    _time_raw = car["Time"].dt.total_seconds().to_numpy()
    if not np.all(np.isfinite(_time_raw)):
        raise NativeAcquisitionError(
            "validate_car", "non-finite Time samples (NaT) in car stream", driver, session)
    _dts = np.diff(_time_raw)
    if np.any(_dts < 0):
        raise NativeAcquisitionError(
            "validate_car", "non-monotonic Time in car stream", driver, session)
    _n_zero = int(np.sum(_dts == 0))
    if _dts.size > 0 and _n_zero > 0.10 * _dts.size:
        raise NativeAcquisitionError(
            "validate_car",
            f"excessive duplicate timestamps ({_n_zero}/{_dts.size}) — "
            f"gap-law median would be biased upward", driver, session)
    for _ch in ("Speed", "Throttle", "RPM", "DRS", "nGear"):
        if _ch in car.columns:
            _vals = np.asarray(car[_ch], dtype=float)
            if not np.all(np.isfinite(_vals)):
                raise NativeAcquisitionError(
                    "validate_car", f"non-finite values in {_ch}", driver, session)
    if car["Brake"].isna().any():
        raise NativeAcquisitionError(
            "validate_car", "null values in Brake", driver, session)

    try:
        # FastF1's own integration (see module docstring for why) + 0-1 axis.
        car = car.add_distance()
        car = car.add_relative_distance()
    except Exception as exc:
        raise NativeAcquisitionError("add_distance", str(exc), driver, session) from exc

    car = car.copy()
    car[PROVENANCE_COLUMN] = Provenance.REAL_CAR.value

    # --- pos stream (acquired + tagged; consumed by nothing at G0) ----------
    try:
        pos = lap.get_pos_data()
    except Exception as exc:
        raise NativeAcquisitionError("get_pos_data", str(exc), driver, session) from exc
    if pos is None or len(pos) == 0:
        raise NativeAcquisitionError("get_pos_data", "empty pos-data frame", driver, session)
    missing = [c for c in REQUIRED_POS_CHANNELS if c not in pos.columns]
    if missing:
        raise NativeAcquisitionError(
            "get_pos_data", f"missing channels: {missing}", driver, session)
    pos = pos.copy()
    pos[PROVENANCE_COLUMN] = Provenance.REAL_POS.value

    # --- gap detection (car stream is the analysis substrate) ---------------
    car_time = car["Time"].dt.total_seconds().to_numpy()
    car_dist = car["Distance"].to_numpy(dtype=float)
    gaps = detect_gaps(car_time, car_dist)

    pos_time = pos["Time"].dt.total_seconds().to_numpy()
    median_dt_car = _median_dt(car_time)

    meta: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "acquisition_mode": "native",
        "n_car": int(len(car)),
        "n_pos": int(len(pos)),
        "median_dt_car": median_dt_car,
        "median_dt_pos": _median_dt(pos_time),
        "gap_dt_multiplier": GAP_DT_MULTIPLIER,
        "gap_threshold_s": GAP_DT_MULTIPLIER * median_dt_car,
        "n_gaps": len(gaps),
        "lib_versions": _lib_versions(),
    }

    if gaps:
        logger.info(
            "native acquisition: %d gap(s) on car stream (driver=%s, session=%s): %s",
            len(gaps), driver, session,
            [f"{g['dt']:.2f}s@{g['d_start']:.0f}m" for g in gaps],
        )

    return TelemetryBundle(car_native=car, pos_native=pos, gaps=gaps, meta=meta)
