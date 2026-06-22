"""
Phase 3: Spatial resolution at speed.

Converts temporal sparsity into metres between consecutive REAL samples:
gap_m = speed(m/s) * dt(s). Reports distribution + the high-speed worst case.
Uses raw car_data (closest to FastF1 source).
Usage: python 02_spatial_resolution.py <YEAR> <GP> [DRIVER]
"""
import sys
import numpy as np
import _common as C


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]
    s = C.load_session(year, gp)
    if len(sys.argv) > 3:
        drivers = [sys.argv[3]]; laps = [C.fastest_lap(s, sys.argv[3])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 3  SPATIAL RESOLUTION AT SPEED", year, gp, "Q3", drivers, laps)

    drv = drivers[0]; lap = laps[0]
    car = lap.get_car_data()
    t = car["SessionTime"].dt.total_seconds().to_numpy()
    v_kmh = car["Speed"].to_numpy(dtype=float)
    dt = np.diff(t)
    v_seg = (v_kmh[:-1] + v_kmh[1:]) / 2.0          # mean speed over each interval
    v_ms = v_seg / 3.6
    gap = v_ms * dt                                  # metres between real samples
    valid = dt > 0
    gap = gap[valid]; v_seg = v_seg[valid]; dt = dt[valid]

    print(f"\n  driver {drv}: {len(gap)} inter-sample intervals")
    d_all = C.describe(gap, unit="m")
    C.print_stats("metres-per-sample (all speeds)", d_all)
    print(f"  metres-per-sample histogram:")
    print(C.text_hist(gap, bins=12, unit="m"))

    out = {"session": f"{year}_{gp}_Q3", "driver": drv, "all": d_all, "bands": {}}
    for lo in (200, 250, 300):
        m = v_seg >= lo
        if m.sum() >= 3:
            db = C.describe(gap[m], unit="m")
            print(f"\n  >= {lo} km/h  ({m.sum()} intervals):")
            C.print_stats(f"metres-per-sample (>= {lo} km/h)", db)
            out["bands"][f">={lo}kmh"] = db

    vmax = v_kmh.max()
    imax = np.argmax(v_seg)
    print(f"\n  top speed on lap: {vmax:.1f} km/h")
    print(f"  WORST CASE: at {v_seg[imax]:.0f} km/h, consecutive samples are "
          f"{gap[imax]:.1f} m apart (dt={dt[imax]*1000:.0f} ms)")
    out["top_speed_kmh"] = float(vmax)
    out["worst_case"] = {"speed_kmh": float(v_seg[imax]),
                         "gap_m": float(gap[imax]), "dt_ms": float(dt[imax]*1000)}
    C.save_json(f"02_spatial_resolution_{drv}.json", out)


if __name__ == "__main__":
    main()
