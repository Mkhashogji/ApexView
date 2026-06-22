"""Quantify detector substrate noise in the Shanghai T9 search zone (2300-2570m)."""
import json, urllib.request, numpy as np

def get(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        return json.loads(r.read())

def kinematic_decel(d, v_kmh, window=5):
    v = np.asarray(v_kmh) / 3.6
    dd = np.maximum(np.diff(np.asarray(d)), 0.1)
    a = (v[1:]**2 - v[:-1]**2) / (2 * dd)
    if window > 1 and len(a) > window:  # same moving-average as compute_deceleration
        kernel = np.ones(window) / window
        a = np.convolve(a, kernel, mode="same")
    return a

for head in ("legacy", "native"):
    tel = get(f"http://localhost:8000/telemetry?session=2025_2_Qualifying&drivers=PIA&session_part=Q3&acquisition={head}")[0]
    d = np.array(tel["distance"]); v = np.array(tel["speed"])
    a = kinematic_decel(d, v)
    zone = (d[1:] >= 2300) & (d[1:] <= 2570)
    az = a[zone]
    crossings = int(np.sum((az[:-1] > -5.5) & (az[1:] <= -5.5)))
    print(f"{head:7s}: samples_in_zone={zone.sum():3d}  decel min={az.min():6.1f} "
          f"max={az.max():5.1f}  threshold(-5.5) crossings={crossings}  "
          f"mean|p2p|={np.mean(np.abs(np.diff(az))):.2f}")
