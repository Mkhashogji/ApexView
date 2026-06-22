"""
Phase 1-2: Raw sample-interval audit + channel-rate divergence.

Measures dt between consecutive samples on car-data and pos-data separately,
states effective Hz, and reports whether the two sources are co-sampled.
Usage: python 01_sample_intervals.py <YEAR> <GP> [DRIVER]
"""
import sys
import numpy as np
import _common as C


def audit_channel(name, df, time_col="SessionTime"):
    print(f"\n  [{name}]  rows={len(df)}  columns={list(df.columns)[:12]}")
    dt = C.dt_seconds(df[time_col])
    dt = dt[dt > 0]  # drop any zero/dup timestamps for the interval profile
    d = C.describe(dt, unit="s")
    C.print_stats(f"{name} dt", d)
    eff_hz = 1.0 / d["median"] if d["median"] > 0 else float("nan")
    print(f"      effective rate = 1/median(dt) = {eff_hz:.2f} Hz")
    print(f"      dt histogram (s):")
    print(C.text_hist(dt, bins=12, unit="s"))
    d["effective_hz"] = eff_hz
    d["n_rows"] = len(df)
    return d


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]
    s = C.load_session(year, gp)
    if len(sys.argv) > 3:
        drivers = [sys.argv[3]]; laps = [C.fastest_lap(s, sys.argv[3])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 1-2  RAW SAMPLE-INTERVAL AUDIT", year, gp, "Q3", drivers, laps)

    out = {"session": f"{year}_{gp}_Q3", "drivers": {}}
    drv = drivers[0]; lap = laps[0]
    print(f"\n### Reference driver for raw audit: {drv} ###")

    car = lap.get_car_data()
    pos = lap.get_pos_data()
    tel = lap.get_telemetry()

    car_stats = audit_channel("car_data (Speed/RPM/Throttle/Brake/Gear)", car)
    pos_stats = audit_channel("pos_data (X/Y/Z)", pos)

    # get_telemetry = merged product the pipeline actually consumes
    print(f"\n  [get_telemetry MERGED]  rows={len(tel)}")
    dt_tel = C.dt_seconds(tel["SessionTime"])
    dt_tel = dt_tel[dt_tel > 0]
    tel_stats = C.describe(dt_tel, unit="s")
    C.print_stats("get_telemetry dt", tel_stats)
    print(f"      effective rate = {1.0/tel_stats['median']:.2f} Hz")

    # Phase 2: channel-rate divergence
    print("\n### PHASE 2  CHANNEL-RATE DIVERGENCE ###")
    print(f"  car_data rows   : {len(car)}")
    print(f"  pos_data rows   : {len(pos)}")
    print(f"  merged rows     : {len(tel)}  (get_telemetry union timebase)")
    # coincidence of timestamps
    ct = set(np.round(car['SessionTime'].dt.total_seconds().to_numpy(), 4))
    pt = set(np.round(pos['SessionTime'].dt.total_seconds().to_numpy(), 4))
    inter = ct & pt
    print(f"  car timestamps  : {len(ct)} unique")
    print(f"  pos timestamps  : {len(pt)} unique")
    print(f"  shared (exact)  : {len(inter)}  "
          f"({100.0*len(inter)/max(1,min(len(ct),len(pt))):.1f}% of smaller source)")
    print(f"  union           : {len(ct | pt)}  (== merged rows ~ {len(tel)})")
    if 'Source' in tel.columns:
        vc = tel['Source'].value_counts().to_dict()
        print(f"  merged 'Source' tag counts: {vc}")
        print("     -> 'interpolation'/'pos'/'car' shows how many merged rows are")
        print("        filled rather than native car samples.")

    out["drivers"][drv] = {
        "car": car_stats, "pos": pos_stats, "merged": tel_stats,
        "car_rows": len(car), "pos_rows": len(pos), "merged_rows": len(tel),
        "shared_timestamps": len(inter), "union_timestamps": len(ct | pt),
        "merged_source_counts": (tel['Source'].value_counts().to_dict()
                                  if 'Source' in tel.columns else None),
    }
    C.save_json("01_sample_intervals.json", out)


if __name__ == "__main__":
    main()
