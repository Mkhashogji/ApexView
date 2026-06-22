"""
Phase 4: Derivative-noise demonstration.

Computes dv/dt (and the v^2-kinematic deceleration the pipeline uses) across a
braking zone on the RAW signal, quantifies noise (point-to-point variation,
sign flips), then shows the SAME derivative on a cubic-spline-upsampled and a
Savitzky-Golay-smoothed version for comparison only (NOT a fix).
Usage: python 03_derivative_noise.py <YEAR> <GP> <CIRCUIT_ID> [DRIVER]
"""
import sys
import numpy as np
import _common as C


def kinematic_decel(distance, speed_kmh):
    """Replicates corner_analysis.compute_deceleration: a=(v2^2-v1^2)/(2 dd)."""
    v = speed_kmh / 3.6
    dd = np.diff(distance)
    dd = np.maximum(dd, 0.1)
    a = (v[1:] ** 2 - v[:-1] ** 2) / (2 * dd)
    return a


def noise_metrics(a):
    a = np.asarray(a, float)
    diffs = np.abs(np.diff(a))
    signs = np.sign(a)
    sign_flips = int(np.sum(np.diff(signs) != 0))
    return {
        "n": int(a.size),
        "min": float(a.min()), "max": float(a.max()),
        "std": float(np.std(a, ddof=1)) if a.size > 1 else 0.0,
        "mean_abs_point_to_point": float(np.mean(diffs)) if diffs.size else 0.0,
        "max_abs_point_to_point": float(np.max(diffs)) if diffs.size else 0.0,
        "sign_flips": sign_flips,
    }


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]; circuit = sys.argv[3]
    s = C.load_session(year, gp)
    if len(sys.argv) > 4:
        drivers = [sys.argv[4]]; laps = [C.fastest_lap(s, sys.argv[4])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 4  DERIVATIVE-NOISE DEMONSTRATION", year, gp, "Q3", drivers, laps)

    drv = drivers[0]; lap = laps[0]
    # Use NATIVE car_data (the true ~4 Hz measured signal) for the raw derivative.
    # The merged get_telemetry() array has near-duplicate distance points (union
    # timebase) that corrupt finite-difference derivatives, so it is the wrong
    # substrate for a noise demonstration. add_distance() gives metres per sample.
    car = lap.get_car_data().add_distance()
    dist = car["Distance"].to_numpy(dtype=float)
    spd = car["Speed"].to_numpy(dtype=float)
    print(f"\n  raw substrate: native car_data, {len(dist)} samples (~4 Hz)")

    corners, length = C.load_corners(circuit)
    # pick the heaviest braking corner = largest pre-apex speed drop
    def speed_drop(apex):
        i = np.argmin(np.abs(dist - apex))
        pre = dist >= apex - 250
        win = (dist >= apex - 250) & (dist <= apex)
        if win.sum() < 3:
            return 0
        return spd[win].max() - spd[i]
    heavy = max(corners, key=lambda c: speed_drop(c["apex_distance"]))
    apex = heavy["apex_distance"]
    print(f"\n  heaviest-braking corner: T{heavy['corner_number']} "
          f"({heavy['name']}) apex={apex:.0f}m")

    zmask = (dist >= apex - 250) & (dist <= apex + 30)
    zd = dist[zmask]; zs = spd[zmask]
    print(f"  braking-zone window [{apex-250:.0f},{apex+30:.0f}]m: "
          f"{zmask.sum()} real samples, speed {zs.max():.0f}->{zs.min():.0f} km/h")

    # RAW kinematic deceleration (pipeline method)
    a_raw = kinematic_decel(zd, zs)
    raw_m = noise_metrics(a_raw)
    print("\n  RAW v^2-kinematic deceleration (m/s^2):")
    for k, v in raw_m.items():
        print(f"      {k:28s}: {v}")
    print("  raw decel values:", np.round(a_raw, 1).tolist())

    out = {"session": f"{year}_{gp}_Q3", "driver": drv, "circuit": circuit,
           "corner": f"T{heavy['corner_number']}", "apex": apex,
           "zone_samples": int(zmask.sum()), "raw": raw_m}

    # --- comparison only (NOT a fix): smoothing on a UNIFORM distance grid ---
    # Savitzky-Golay assumes uniform spacing, so we first resample speed onto an
    # evenly-spaced distance grid via cubic spline, THEN derive. This is the
    # apples-to-apples comparison the raw finite-difference cannot do directly.
    try:
        from scipy.interpolate import CubicSpline
        from scipy.signal import savgol_filter
        order = np.argsort(zd)
        zd_s, zs_s = zd[order], zs[order]
        zd_u, idx = np.unique(zd_s, return_index=True)
        zs_u = zs_s[idx]
        # uniform fine grid (~2 m spacing -> ~10x upsample of a ~20 m raw step)
        fine = np.linspace(zd_u.min(), zd_u.max(), zd_u.size * 10)
        cs = CubicSpline(zd_u, zs_u)
        spd_fine = cs(fine)
        a_spline = kinematic_decel(fine, spd_fine)
        sp_m = noise_metrics(a_spline)
        print("\n  CUBIC-SPLINE-UPSAMPLED on uniform grid (x10) decel (comparison only):")
        for k, v in sp_m.items():
            print(f"      {k:28s}: {v}")

        # Savitzky-Golay on the UNIFORM fine speed, then derivative
        wl = 11 if spd_fine.size >= 11 else (spd_fine.size // 2) * 2 + 1
        zs_sg = savgol_filter(spd_fine, window_length=wl, polyorder=3)
        a_sg = kinematic_decel(fine, zs_sg)
        sg_m = noise_metrics(a_sg)
        print(f"\n  SAVITZKY-GOLAY on uniform grid (win={wl}) decel (comparison only):")
        for k, v in sg_m.items():
            print(f"      {k:28s}: {v}")
        out["spline"] = sp_m; out["savgol"] = sg_m

        print("\n  COMPARISON (raw native -> spline-uniform -> savgol-uniform):")
        print(f"    mean |point-to-point|: {raw_m['mean_abs_point_to_point']:.2f} -> "
              f"{sp_m['mean_abs_point_to_point']:.2f} -> {sg_m['mean_abs_point_to_point']:.2f} m/s^2")
        print(f"    sign_flips           : {raw_m['sign_flips']} -> "
              f"{sp_m['sign_flips']} -> {sg_m['sign_flips']}")
        print(f"    std                  : {raw_m['std']:.2f} -> "
              f"{sp_m['std']:.2f} -> {sg_m['std']:.2f} m/s^2")
        if raw_m['mean_abs_point_to_point'] > 0:
            red = 100*(1 - sg_m['mean_abs_point_to_point']/raw_m['mean_abs_point_to_point'])
            print(f"    -> savgol cuts point-to-point noise by ~{red:.0f}% (illustrative)")
    except Exception as e:
        print(f"  [warn] scipy comparison skipped: {e}")

    C.save_json(f"03_derivative_noise_{drv}.json", out)


if __name__ == "__main__":
    main()
