"""
Phase 6: Corner-scale impact (headline evidence).

For representative corners, counts how many REAL samples fall inside the v2
braking search zone (apex-300..apex-30, per detect_braking_zone_v2) and between
the detected brake point and the apex. Also contrasts merged get_telemetry()
samples vs native car_data samples in the same window (phantom vs real), and
reports how many samples the kinematic backward-walk actually traverses.
Usage: python 05_corner_scale.py <YEAR> <GP> <CIRCUIT_ID> [DRIVER]
"""
import sys
import numpy as np
import _common as C

BRAKING_DECEL_THRESHOLD = -5.5  # shanghai config value (monaco=-4.0); reported per-run


def kinematic_decel(distance, speed_kmh):
    v = speed_kmh / 3.6
    dd = np.maximum(np.diff(distance), 0.1)
    return (v[1:] ** 2 - v[:-1] ** 2) / (2 * dd)


def analyze_corner(tel, car, apex, decel_threshold):
    dist = tel["Distance"].to_numpy(float)
    spd = tel["Speed"].to_numpy(float)
    brake = tel["Brake"].to_numpy()
    # v2 search zone
    ss, se = apex - 300, apex - 30
    zmask = (dist >= ss) & (dist <= se)
    zidx = np.where(zmask)[0]
    res = {"apex": apex, "search_zone": [ss, se],
           "merged_samples_in_zone": int(zmask.sum())}

    # native car_data samples in the same metric window (add_distance for parity)
    cardist = None
    try:
        cardist = car.add_distance()["Distance"].to_numpy(float)
        res["car_samples_in_zone"] = int(((cardist >= ss) & (cardist <= se)).sum())
    except Exception:
        res["car_samples_in_zone"] = None

    if len(zidx) < 2:
        res["note"] = "too few samples to detect"
        return res

    # Stage 1: boolean brake >= 0.5
    bn = brake.astype(float)
    bn = bn / 100.0 if bn.max() > 1.0 else bn
    cand = zidx[bn[zidx] >= 0.5]
    decel = kinematic_decel(dist, spd)
    if len(cand) == 0:
        res["brake_point"] = None
        res["samples_brake_to_apex"] = None
        return res
    b_idx = int(cand[0])
    res["brake_point_m"] = float(dist[b_idx])
    # Stage 2 backward walk (replicates :1027-1032), count steps
    steps = 0
    r = b_idx
    while r > zidx[0]:
        di = min(r - 1, len(decel) - 1)
        if di >= 0 and decel[di] > decel_threshold:
            break
        r -= 1; steps += 1
    res["refined_point_m"] = float(dist[max(0, r)])
    res["backward_walk_steps"] = steps
    # samples from brake point to apex
    bp = res["refined_point_m"]
    res["samples_brake_to_apex"] = int(((dist >= bp) & (dist <= apex)).sum())
    if cardist is not None:
        res["native_samples_brake_to_apex"] = int(((cardist >= bp) & (cardist <= apex)).sum())
    return res


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]; circuit = sys.argv[3]
    s = C.load_session(year, gp)
    if len(sys.argv) > 4:
        drivers = [sys.argv[4]]; laps = [C.fastest_lap(s, sys.argv[4])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 6  CORNER-SCALE IMPACT", year, gp, "Q3", drivers, laps)

    # circuit-specific decel threshold (mirror corner_config where it matters)
    decel_threshold = {"shanghai": -5.5, "monaco": -4.0, "monza": -6.0,
                       "baku": -6.5}.get(circuit, -5.0)
    print(f"  using braking_decel_threshold={decel_threshold} m/s^2 (circuit={circuit})")

    drv = drivers[0]; lap = laps[0]
    tel = lap.get_telemetry()
    car = lap.get_car_data()
    corners, length = C.load_corners(circuit)
    dist = tel["Distance"].to_numpy(float)
    spd = tel["Speed"].to_numpy(float)

    # rank corners by pre-apex speed drop, pick a heavy one + a fast one + median
    def drop(c):
        a = c["apex_distance"]; i = np.argmin(np.abs(dist - a))
        win = (dist >= a - 250) & (dist <= a)
        return (spd[win].max() - spd[i]) if win.sum() >= 3 else 0
    ranked = sorted(corners, key=drop, reverse=True)
    picks = [ranked[0], ranked[len(ranked)//2], ranked[-1]]

    out = {"session": f"{year}_{gp}_Q3", "driver": drv, "circuit": circuit,
           "decel_threshold": decel_threshold, "corners": []}
    for c in picks:
        print(f"\n  --- T{c['corner_number']} ({c['name']}) apex={c['apex_distance']:.0f}m, "
              f"pre-apex speed drop ~{drop(c):.0f} km/h ---")
        r = analyze_corner(tel, car, c["apex_distance"], decel_threshold)
        r["corner_number"] = c["corner_number"]; r["name"] = c["name"]
        for k in ["merged_samples_in_zone", "car_samples_in_zone", "brake_point_m",
                  "refined_point_m", "backward_walk_steps", "samples_brake_to_apex",
                  "native_samples_brake_to_apex"]:
            if k in r:
                print(f"      {k:28s}: {r[k]}")
        if r.get("native_samples_brake_to_apex") is not None:
            print(f"      => the brake event for T{c['corner_number']} is characterised from "
                  f"~{r['native_samples_brake_to_apex']} NATIVE (~{r['samples_brake_to_apex']} merged) "
                  f"samples brake->apex.")
        out["corners"].append(r)

    # full per-corner table (zone sample counts for every corner)
    print(f"\n  FULL CORNER TABLE (search zone apex-300..apex-30):")
    print(f"    {'corner':8s}{'apex_m':>8s}{'merged':>8s}{'native':>8s}")
    table = []
    for c in sorted(corners, key=lambda x: x["corner_number"]):
        rr = analyze_corner(tel, car, c["apex_distance"], decel_threshold)
        print(f"    T{c['corner_number']:<7d}{c['apex_distance']:>8.0f}"
              f"{rr['merged_samples_in_zone']:>8d}{(rr['car_samples_in_zone'] or -1):>8d}")
        table.append({"corner": c["corner_number"], "apex": c["apex_distance"],
                      "merged": rr["merged_samples_in_zone"],
                      "native": rr["car_samples_in_zone"]})
    out["full_table"] = table
    C.save_json(f"05_corner_scale_{drv}.json", out)


if __name__ == "__main__":
    main()
