"""
WU-4: near-zero delta-d guard in compute_deceleration.

a = (v2^2 - v1^2) / (2 * delta_d) is numerically undefined as delta_d -> 0.
The pre-WU-4 code clamped exact zeros to 0.001 m and left near-zero intervals
entirely unguarded, so a genuine speed change across a degenerate interval
produced an unbounded fabricated deceleration spike. WU-4 emits NaN
("undefined over a zero-length interval") for |delta_d| below
MIN_VALID_DELTA_DISTANCE_M, masks the guarded samples out of the smoothing
input, and restores NaN at exactly the guarded positions — absent, not
misleading.

Seven tests in two classes, with two different fail-then-pass baselines:

- TestNearZeroDeltaDistanceGuard (3 tests): the guard itself. Recorded
  FAILING against the pre-WU-4 implementation (the exact-zero clamp to
  0.001 m) and passing on WU-4.
- TestSmoothingRenormalisation (4 tests): the masked-smoothing correction.
  Recorded against WU-4's first implementation ("variant B", zero-fill
  smoothing), NOT against pre-WU-4: the neighbour-bias test FAILED on B
  (neighbour value -2.4000 != -3.0, i.e. c*(w-1)/w for w=5) and passes on
  the final deficit-renormalised implementation; the two bit-identity tests
  and the NaN-count test are protective and passed on B as well.
"""
import numpy as np
import pytest

from services.corner_analysis import compute_deceleration

# Anything beyond this magnitude is a numerical artefact, not physics: peak
# F1 braking is ~6g (~60 m/s^2). The bound is deliberately generous so the
# test pins "no unbounded spike", not a physics envelope (which belongs to
# the detector gate).
ARTEFACT_BOUND_MS2 = 200.0


def _arrays_with_injected_interval(injected_dd: float):
    """
    Native-like 15 m spacing with a braking ramp, plus one injected interval
    of width `injected_dd` carrying a real 2 km/h speed drop. Returns
    (distance, speed, index of the degenerate interval in the diff/decel
    axis) — the index is derived from the data, not hardcoded.
    """
    n = 24
    distance = np.arange(n, dtype=float) * 15.0
    speed = np.linspace(260.0, 145.0, n)  # ~ -4.5 to -6.5 m/s^2 baseline
    insert_at = 12
    distance = np.insert(distance, insert_at, distance[insert_at - 1] + injected_dd)
    speed = np.insert(speed, insert_at, speed[insert_at - 1] - 2.0)
    bad_interval = int(np.argmin(np.abs(np.diff(distance))))
    return distance, speed, bad_interval


class TestNearZeroDeltaDistanceGuard:
    def test_near_zero_interval_produces_no_unbounded_spike(self):
        """
        A real speed drop across a 0.01 m interval must not become a
        ~10^3 m/s^2 fabricated deceleration. Every finite output value must
        stay physically bounded; the degenerate interval itself is undefined.
        """
        distance, speed, _ = _arrays_with_injected_interval(0.01)
        decel = compute_deceleration(distance, speed, smoothing_window=5)
        finite = np.isfinite(decel)
        assert not np.any(np.abs(decel[finite]) > ARTEFACT_BOUND_MS2), (
            f"unbounded spike leaked into finite output: "
            f"max |decel| = {np.abs(decel[finite]).max():.0f} m/s^2"
        )

    def test_guarded_interval_yields_exactly_one_nan(self):
        """
        One guarded interval in, exactly one NaN out — the moving-average
        smoothing must not smear the undefined marker across the window.
        """
        distance, speed, bad_interval = _arrays_with_injected_interval(0.01)
        decel = compute_deceleration(distance, speed, smoothing_window=5)
        nan_positions = np.flatnonzero(np.isnan(decel)).tolist()
        assert nan_positions == [bad_interval], (
            f"expected exactly one NaN at diff index {bad_interval}, "
            f"got NaN at {nan_positions}"
        )

    def test_exact_zero_interval_is_nan_not_fabricated(self):
        """
        delta_d == 0 must be reported as undefined (NaN), not silently
        replaced by a 0.001 m denominator that fabricates a finite value.
        """
        distance, speed, bad_interval = _arrays_with_injected_interval(0.0)
        decel = compute_deceleration(distance, speed, smoothing_window=5)
        assert np.isnan(decel[bad_interval]), (
            f"exact-zero interval produced a fabricated finite value: "
            f"decel[{bad_interval}] = {decel[bad_interval]}"
        )


# =============================================================================
# WU-4 closure: masked-smoothing renormalisation
# =============================================================================

def _constant_decel_arrays(c_ms2: float, spacing_m: float, n: int,
                           inject_at: int | None = None, inject_dd: float = 0.01):
    """
    Distance/speed arrays whose kinematic deceleration is EXACTLY the constant
    ``c_ms2`` on every interval, via v^2 = v0^2 + 2*c*d. Optionally injects one
    degenerate interval of width ``inject_dd`` at diff index ``inject_at`` (the
    injected point also obeys the v^2 law, so every non-degenerate interval
    still carries exactly ``c_ms2``). Returns (distance, speed, bad_interval).
    """
    v0 = 80.0  # m/s (~288 km/h)
    distance = np.arange(n, dtype=float) * spacing_m
    if inject_at is not None:
        distance = np.insert(distance, inject_at + 1, distance[inject_at] + inject_dd)
    v_ms = np.sqrt(v0 ** 2 + 2.0 * c_ms2 * distance)
    speed_kmh = v_ms * 3.6
    bad = None if inject_at is None else int(np.argmin(np.abs(np.diff(distance))))
    return distance, speed_kmh, bad


class TestSmoothingRenormalisation:
    def test_bit_identical_to_plain_convolution_on_nan_free_input(self):
        """
        Protects the native head: with nothing guarded, the smoothing path
        must be BIT-identical (np.array_equal, not allclose) to the plain
        moving average — including the first and last ``w`` samples, where
        np.convolve's edge zero-padding lives. An approximate comparison
        would let an edge change slip through onto the harness.
        """
        rng = np.random.default_rng(1234)
        for w in (3, 5, 7):
            n = 60
            distance = np.cumsum(rng.uniform(2.5, 25.0, n))  # native-like, all >= 2.5 m
            speed = rng.uniform(80.0, 320.0, n)
            # reference: raw kinematic ratio -> plain moving average
            v = speed / 3.6
            raw = (v[1:] ** 2 - v[:-1] ** 2) / (2 * np.diff(distance))
            reference = np.convolve(raw, np.ones(w) / w, mode="same")
            out = compute_deceleration(distance, speed, smoothing_window=w)
            assert np.array_equal(out, reference), (
                f"w={w}: smoothing path is not bit-identical to plain convolution "
                f"(max |diff| = {np.max(np.abs(out - reference))})"
            )

    def test_guarded_windows_far_from_guard_are_bit_identical(self):
        """
        Stronger form of the previous test, on the GUARDED code path: output
        samples whose window contains no guarded sample must still be
        bit-identical to the plain convolution of the zero-filled array —
        the renormalisation factor there is exactly 1.0, not approximately.
        """
        w = 5
        distance, speed, bad = _arrays_with_injected_interval(0.01)
        v = speed / 3.6
        raw = (v[1:] ** 2 - v[:-1] ** 2) / (2 * np.diff(distance))
        filled = raw.copy(); filled[bad] = 0.0
        plain = np.convolve(filled, np.ones(w) / w, mode="same")
        out = compute_deceleration(distance, speed, smoothing_window=w)
        far = np.ones(len(out), dtype=bool)
        far[max(0, bad - (w // 2)): bad + (w // 2) + 1] = False
        assert np.array_equal(out[far], plain[far])

    def test_neighbours_of_guarded_interval_are_not_biased_toward_zero(self):
        """
        One guarded interval inside a region of EXACTLY constant deceleration
        c: the neighbours' smoothed values must equal c (mean of their w-1
        valid samples), not c*(w-1)/w. Fails under zero-fill smoothing
        (neighbours come out at 0.8*c for w=5); passes under deficit
        renormalisation.
        """
        c, w = -3.0, 5
        distance, speed, bad = _constant_decel_arrays(c, spacing_m=10.0, n=40,
                                                      inject_at=20, inject_dd=0.01)
        out = compute_deceleration(distance, speed, smoothing_window=w)
        assert np.isnan(out[bad])
        # neighbours within the smoothing half-window on each side, interior
        # of the array (well away from the edge zero-padding)
        neighbours = [bad - 2, bad - 1, bad + 1, bad + 2]
        for i in neighbours:
            assert out[i] == pytest.approx(c, rel=1e-9), (
                f"neighbour {i} of guarded interval {bad} biased: "
                f"{out[i]} != {c} (zero-fill would give {c * (w - 1) / w})"
            )

    def test_nan_count_preserved_for_multiple_guarded_intervals(self):
        """Exactly n guarded intervals in -> exactly n NaN out, at exactly the
        guarded positions (including two ADJACENT guarded intervals, which
        share smoothing windows)."""
        n = 40
        distance = np.arange(n, dtype=float) * 12.0
        speed = np.linspace(280.0, 120.0, n)
        # three degenerate intervals: one isolated, two adjacent
        for insert_at, dd in ((30, 0.02), (16, 0.01), (15, 0.03)):
            distance = np.insert(distance, insert_at, distance[insert_at - 1] + dd)
            speed = np.insert(speed, insert_at, speed[insert_at - 1] - 1.0)
        expected = set(np.flatnonzero(np.abs(np.diff(distance)) < 0.5).tolist())
        assert len(expected) == 3
        out = compute_deceleration(distance, speed, smoothing_window=5)
        got = set(np.flatnonzero(np.isnan(out)).tolist())
        assert got == expected, f"NaN positions {sorted(got)} != guarded {sorted(expected)}"
