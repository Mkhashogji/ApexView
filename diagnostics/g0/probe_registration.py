"""Pre-implementation probe 2: per-corner distance-registration shift, native vs merged.

The 20.2m total-length difference could be (a) accumulated integration drift —
which shifts corner windows and can trigger the Phase 3 STOP (>=5m/corner) — or
(b) endpoint effects (merged frame spanning more time than the car frame).
Disambiguate by diffing Distance at IDENTICAL car SessionTime stamps, then
evaluating the drift at each track-JSON corner apex.

Read-only. Run inside f1-api: python probe_registration.py <year> <round> <drv> <track.json>
"""
import sys
import json
import fastf1
import numpy as np

year, rnd, drv, trackjson = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
fastf1.Cache.enable_cache("/app/data/cache")
s = fastf1.get_session(year, rnd, "Q")
s.load()
q1, q2, q3 = s.laps.split_qualifying_sessions()
lap = q3.pick_drivers(drv).pick_fastest()
print(f"driver={drv} lap={int(lap['LapNumber'])} time={lap['LapTime']}")

car = lap.get_car_data().add_distance()
tel = lap.get_telemetry()

ct = np.round(car["SessionTime"].dt.total_seconds().to_numpy(), 6)
cd = car["Distance"].to_numpy()
mt = np.round(tel["SessionTime"].dt.total_seconds().to_numpy(), 6)
md = tel["Distance"].to_numpy()

m_lookup = {}
for t, d in zip(mt, md):
    m_lookup[t] = d

drift_t, drift_v, matched = [], [], 0
for t, d in zip(ct, cd):
    if t in m_lookup:
        matched += 1
        drift_t.append(t)
        drift_v.append(d - m_lookup[t])
drift_v = np.array(drift_v)
drift_t = np.array(drift_t)
print(f"matched car timestamps in merged frame: {matched}/{len(ct)}")
print(f"drift native-merged: mean={drift_v.mean():+.3f}m  min={drift_v.min():+.3f}m  "
      f"max={drift_v.max():+.3f}m  at_lap_end={drift_v[-1]:+.3f}m")

# endpoint effects
print(f"car frame span    : t=[{ct[0]:.3f},{ct[-1]:.3f}]  d=[{cd[0]:.2f},{cd[-1]:.2f}]")
print(f"merged frame span : t=[{mt[0]:.3f},{mt[-1]:.3f}]  d=[{md[0]:.2f},{md[-1]:.2f}]")
print(f"merged rows after last car stamp: {(mt > ct[-1]).sum()}  "
      f"distance integrated there: {md[-1] - m_lookup.get(ct[-1], float('nan')):.2f}m")
print(f"merged rows before first car stamp: {(mt < ct[0]).sum()}")

# drift evaluated at each corner apex (merged-distance frame = the historical reference)
with open(trackjson, encoding="utf-8") as f:
    track = json.load(f)
print("\nper-corner registration shift (native Distance - merged Distance at the")
print("merged sample nearest each nominal apex; positive = native reads further):")
viol = 0
for c in track["corners"]:
    apex = float(c["distance"])
    # merged sample nearest the apex (in merged-distance space)
    mi = int(np.argmin(np.abs(md - apex)))
    t_apex = mt[mi]
    # native distance at that same instant (interp on car timebase)
    nd = float(np.interp(t_apex, ct, cd))
    shift = nd - md[mi]
    flag = "  <-- exceeds 5m" if abs(shift) >= 5.0 else ""
    if abs(shift) >= 5.0:
        viol += 1
    print(f"  T{c['cornerNumber']:<3d} apex={apex:6.0f}m  shift={shift:+7.3f}m{flag}")
print(f"\ncorners with |shift| >= 5m: {viol}/{len(track['corners'])}")
