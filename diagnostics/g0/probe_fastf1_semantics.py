"""Pre-implementation probe: verify FastF1 method semantics the native layer relies on.
Read-only. Run inside f1-api: python probe_fastf1_semantics.py"""
import fastf1
import numpy as np

fastf1.Cache.enable_cache("/app/data/cache")
s = fastf1.get_session(2025, 2, "Q")
s.load()
q1, q2, q3 = s.laps.split_qualifying_sessions()
lap = q3.pick_drivers("PIA").pick_fastest()
print("lap:", int(lap["LapNumber"]), lap["LapTime"])

car = lap.get_car_data()
print("car columns:", list(car.columns))
print("car rows:", len(car), "Brake dtype:", car["Brake"].dtype, "nGear dtype:", car["nGear"].dtype)

# 1. add_distance on car frame
car_d = car.add_distance()
d = car_d["Distance"].to_numpy()
print("add_distance: first=%.6f last=%.3f monotonic=%s" % (d[0], d[-1], bool(np.all(np.diff(d) >= 0))))

# explicit integration parity check (what the unit test will assert)
t = car["Time"].dt.total_seconds().to_numpy()
v = car["Speed"].to_numpy() / 3.6
dt = np.diff(t, prepend=t[0])
explicit = np.cumsum(v * dt)
print("explicit vs add_distance: max abs diff = %.9f m" % np.max(np.abs(explicit - d)))

# alternative: dt from SessionTime
t2 = car["SessionTime"].dt.total_seconds().to_numpy()
dt2 = np.diff(t2, prepend=t2[0]); dt2[0] = 0
explicit2 = np.cumsum(v * dt2)
print("explicit(SessionTime,dt0=0) vs add_distance: max abs diff = %.9f m" % np.max(np.abs(explicit2 - d)))

# 2. add_relative_distance on car frame
try:
    car_rd = car_d.add_relative_distance()
    rd = car_rd["RelativeDistance"].to_numpy()
    print("add_relative_distance: first=%.8f last=%.8f" % (rd[0], rd[-1]))
except Exception as e:
    print("add_relative_distance FAILED:", e)

# 3. merged frame RelativeDistance for parity reference
tel = lap.get_telemetry()
mrd = tel["RelativeDistance"].to_numpy()
md = tel["Distance"].to_numpy()
print("merged RelativeDistance: first=%.8f last=%.8f  Distance first=%.4f last=%.3f"
      % (mrd[0], mrd[-1], md[0], md[-1]))
print("merged rows:", len(tel))

# 4. car Time column normalization reference (legacy used merged Time - Time[0])
print("car Time[0]=%.4fs SessionTime[0]=%.3fs" % (t[0], t2[0]))

# 5. pos frame
pos = lap.get_pos_data()
print("pos columns:", list(pos.columns), "rows:", len(pos))
