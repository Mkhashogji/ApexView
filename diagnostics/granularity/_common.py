"""
Shared helpers for the telemetry-granularity diagnostic suite.

Read-only. Loads FastF1 data from the SAME cache the production API uses
(/app/data/cache inside the f1-api container) so library + data versions match.

Nothing here touches application code; it re-derives the production entry path
(`lap.get_telemetry()`) directly so we can audit what the pipeline receives.
"""
import sys
import json
import numpy as np


CACHE_DIR = "/app/data/cache"


def banner(title, year, gp, session_part, drivers, laps):
    import fastf1
    import numpy
    import pandas
    try:
        import scipy
        scipy_v = scipy.__version__
    except Exception:
        scipy_v = "n/a"
    print("=" * 78)
    print(title)
    print("=" * 78)
    print(f"  fastf1={fastf1.__version__}  numpy={numpy.__version__}  "
          f"pandas={pandas.__version__}  scipy={scipy_v}")
    print(f"  session : {year} {gp}  part={session_part}")
    for d, lp in zip(drivers, laps):
        lt = lp['LapTime']
        print(f"  driver  : {d}  lap#{int(lp['LapNumber'])}  "
              f"LapTime={lt}  Compound={lp.get('Compound')}")
    print("-" * 78)


def enable_cache():
    import fastf1
    fastf1.Cache.enable_cache(CACHE_DIR)


def load_session(year, gp):
    import fastf1
    enable_cache()
    s = fastf1.get_session(year, gp, "Q")
    s.load()  # hits cache; offline-safe once populated
    return s


def q3_laps(session):
    """Return the Q3 segment laps (production filters by session_part='Q3')."""
    try:
        q1, q2, q3 = session.laps.split_qualifying_sessions()
        if q3 is not None and len(q3) > 0:
            return q3
    except Exception as e:
        print(f"  [warn] split_qualifying_sessions failed: {e}; using full laps")
    return session.laps


def top_two_drivers(session):
    """Pick the two fastest drivers in Q3 by their fastest valid lap."""
    laps = q3_laps(session)
    best = {}
    for drv in laps['Driver'].unique():
        dl = laps.pick_drivers(drv)
        try:
            f = dl.pick_fastest()
        except Exception:
            f = None
        if f is not None and f['LapTime'] is not None and not _isnat(f['LapTime']):
            best[drv] = f
    ordered = sorted(best.items(), key=lambda kv: kv[1]['LapTime'])
    return [d for d, _ in ordered[:2]], [lp for _, lp in ordered[:2]]


def _isnat(td):
    try:
        return td != td  # NaT != NaT
    except Exception:
        return False


def fastest_lap(session, driver):
    laps = q3_laps(session)
    return laps.pick_drivers(driver).pick_fastest()


def dt_seconds(time_series):
    """Consecutive diffs of a timedelta series, in seconds."""
    t = time_series.dt.total_seconds().to_numpy()
    return np.diff(t)


def describe(arr, unit=""):
    arr = np.asarray(arr, dtype=float)
    pct = np.percentile(arr, [5, 25, 50, 75, 95])
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "p5": float(pct[0]), "p25": float(pct[1]), "p50": float(pct[2]),
        "p75": float(pct[3]), "p95": float(pct[4]),
        "unit": unit,
    }


def print_stats(label, d):
    print(f"  {label}: n={d['n']}  mean={d['mean']:.4f}  median={d['median']:.4f}  "
          f"std={d['std']:.4f}  min={d['min']:.4f}  max={d['max']:.4f} {d['unit']}")
    print(f"      pct  p5={d['p5']:.4f}  p25={d['p25']:.4f}  p50={d['p50']:.4f}  "
          f"p75={d['p75']:.4f}  p95={d['p95']:.4f} {d['unit']}")


def text_hist(arr, bins=12, width=50, unit=""):
    arr = np.asarray(arr, dtype=float)
    counts, edges = np.histogram(arr, bins=bins)
    mx = counts.max() if counts.max() > 0 else 1
    lines = []
    for i in range(len(counts)):
        bar = "#" * int(round(width * counts[i] / mx))
        lines.append(f"    [{edges[i]:8.3f},{edges[i+1]:8.3f}) {unit:<4} {counts[i]:6d} |{bar}")
    return "\n".join(lines)


def save_json(name, obj):
    path = f"/tmp/diag/results/{name}"
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    print(f"  [saved] {path}")


def load_corners(circuit_id):
    """Load corner apex distances from the production track JSON (copied into the container)."""
    path = f"/tmp/diag/tracks/{circuit_id}.json"
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    corners = [
        {"corner_number": c["cornerNumber"],
         "apex_distance": float(c["distance"]),
         "type": c.get("type"),
         "name": c.get("name")}
        for c in d.get("corners", [])
    ]
    return corners, float(d.get("length", 0.0))
