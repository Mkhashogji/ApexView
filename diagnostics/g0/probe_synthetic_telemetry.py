import pandas as pd
import numpy as np
import fastf1.core as fc
n = 20
t = pd.to_timedelta(np.arange(n) * 0.25, unit="s")
df = pd.DataFrame({
    "Time": t, "SessionTime": t + pd.Timedelta(seconds=1000),
    "Speed": np.linspace(100, 300, n), "Throttle": np.full(n, 50.0),
    "Brake": np.zeros(n, dtype=bool), "nGear": np.full(n, 5, dtype=int),
    "RPM": np.full(n, 11000.0), "DRS": np.zeros(n, dtype=int),
})
tel = fc.Telemetry(df)
tel2 = tel.add_distance()
tel3 = tel2.add_relative_distance()
print("Distance ok:", round(float(tel3["Distance"].iloc[-1]), 3))
print("RelDist last:", float(tel3["RelativeDistance"].iloc[-1]))
print("Brake dtype after ops:", tel3["Brake"].dtype)
