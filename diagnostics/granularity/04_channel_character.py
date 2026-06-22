"""
Phase 5: Per-channel signal character.

Empirically classifies each channel as continuous / bounded / binary / discrete
by inspecting unique values + dtype. De-risks the eventual interpolation strategy
(e.g. Brake binary -> no cubic spline; Gear discrete -> step, not interpolate).
Usage: python 04_channel_character.py <YEAR> <GP> [DRIVER]
"""
import sys
import numpy as np
import _common as C


def classify(name, arr):
    a = np.asarray(arr)
    try:
        af = a.astype(float)
    except Exception:
        af = None
    uniq = np.unique(a)
    info = {"dtype": str(a.dtype), "n_unique": int(uniq.size)}
    if af is not None:
        info.update(min=float(np.nanmin(af)), max=float(np.nanmax(af)))
    sample = uniq[:10].tolist()
    # heuristic classification
    if uniq.size <= 2:
        kind = "binary"
    elif a.dtype == bool:
        kind = "binary"
    elif np.issubdtype(a.dtype, np.integer) and uniq.size <= 10:
        kind = "discrete (step)"
    elif uniq.size <= 12:
        kind = "discrete/bounded"
    else:
        kind = "continuous"
    info["kind"] = kind
    print(f"  {name:12s} dtype={info['dtype']:8s} unique={info['n_unique']:5d}  "
          f"kind={kind}")
    print(f"      sample unique values: {sample}")
    if af is not None:
        print(f"      range: [{info.get('min')}, {info.get('max')}]")
    return info


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]
    s = C.load_session(year, gp)
    if len(sys.argv) > 3:
        drivers = [sys.argv[3]]; laps = [C.fastest_lap(s, sys.argv[3])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 5  PER-CHANNEL SIGNAL CHARACTER", year, gp, "Q3", drivers, laps)

    drv = drivers[0]; lap = laps[0]
    tel = lap.get_telemetry()
    out = {"session": f"{year}_{gp}_Q3", "driver": drv, "channels": {}}
    print(f"\n  driver {drv}, merged get_telemetry ({len(tel)} rows)\n")
    for ch in ["Speed", "RPM", "Throttle", "Brake", "nGear", "DRS"]:
        if ch in tel.columns:
            out["channels"][ch] = classify(ch, tel[ch].to_numpy())
    C.save_json(f"04_channel_character_{drv}.json", out)


if __name__ == "__main__":
    main()
