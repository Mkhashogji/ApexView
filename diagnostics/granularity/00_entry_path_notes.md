# Phase 0 — Entry-Path Map (code tracing)

Goal: document a telemetry sample's journey from FastF1 into Phase 2, including
every existing resampling step, so later phases don't double-count interpolation.

## A. How telemetry is obtained (the FastF1 call)

Active path (qualifying analysis):

1. Analysis service `performance_orchestrator.fetch_driver_telemetry()`
   → HTTP `GET http://api:8000/telemetry`
   (`apps/analysis_service/services/performance_orchestrator.py:407`).
2. API route `apps/api/app/routes/telemetry.py:24` → `service.get_telemetry(...)`.
3. `service` is resolved by `get_data_service()` (LIVE_DATA env) to
   **`app.services.telemetry.fastf1_client.FastF1Client`**.
   - The qualifying proxy route also instantiates this same class directly
     (`apps/api/app/routes/analysis.py:6`).
4. **The actual FastF1 call**: `fastest_lap.get_telemetry()`
   - `apps/api/app/services/telemetry/fastf1_client.py:665` (telemetry endpoint)
   - `:807`, `:828` (delta endpoint)

`get_telemetry()` is FastF1's HIGH-LEVEL accessor. It is NOT raw car data.
Internally (FastF1 3.8.x) it:
  - calls `get_car_data()` (Speed, RPM, Throttle, Brake, nGear, DRS) and
    `get_pos_data()` (X, Y, Z, Status),
  - merges them with `merge_channels()` onto the **union** of both channels'
    timestamps,
  - calls `add_distance()` (cumulative ∫speed·dt) and `add_relative_distance()`
    (Distance / Distance[-1] → 0..1),
  - `interpolate_edges`-style fill at lap boundaries.
  → So a merge + interpolation step is already baked in BEFORE our code sees it.
  Channels are extracted at `:669-690`:
  Distance, Speed, Throttle, Brake, nGear, RPM, DRS, RelativeDistance, Time.

No explicit `frequency=` / `.resample_channels()` is passed anywhere in our code
(grep clean). The only FastF1 resampling is the implicit merge inside
`get_telemetry()`.

## B. Our own resampling / downsampling steps

1. **Index downsample (API, conditional)** —
   `apps/api/app/services/telemetry/fastf1_client.py:696-714`:
   `if len(distance) > self.downsample_threshold:` → `np.linspace(0, n-1, threshold)`
   index selection on every channel.
   - `downsample_threshold = settings.DOWNSAMPLE_THRESHOLD` (`:38`)
   - `DOWNSAMPLE_THRESHOLD = 5000` (`apps/api/app/core/config.py:19`).
   - A qualifying lap is ~200-400 samples → **branch never triggers**.
     Raw FastF1 samples pass through to the analysis service unchanged.

2. **Phase 2 delta alignment (analysis service)** —
   `apps/analysis_service/services/delta_analysis.py`:
   - Tier 1 (used in practice): `common_rel_dist = np.linspace(0, 1, num_points)`
     (`:292`), then `np.interp(common_rel_dist, rel_distance, time_scaled)`
     (`:295-296`).
   - Tier 2/3 use `np.linspace(min,max,num_points)` on metres (`:375`, `:192`) + `np.interp`.
   - `num_points` default **1000** (`:146,240,334,398`); orchestrator passes
     `DEFAULT_NUM_POINTS = 1000` (`performance_orchestrator.py:71,584`).
   - `align_telemetry_to_distance()` (`:110-134`) == thin wrapper over `np.interp`.
   ⇒ Delta trace is resampled to **1000 points**, typically 3-5× denser than the
     ~200-400 real samples. **Phantom resolution introduced here.**

3. **Phase 3 corner analysis (analysis service)** —
   `apps/analysis_service/services/corner_analysis.py`:
   - Brake/apex/exit detection runs on the **raw ref/comp arrays** that came from
     `get_telemetry()` (NOT the 1000-pt grid): `analyze_corners_v2(... ref_distance,
     ref_brake, ref_speed, comp_* ...)` (`performance_orchestrator.py:630-640`).
   - `compute_deceleration()` (`:809`) finite-difference v²-kinematics on raw samples.
   - `detect_braking_zone_v2()` (`:944`) two-stage: boolean brake≥0.5, then a
     backward index walk over `decel` (`:1027-1032`) — iterates **raw samples**.
   - BUT the *time gained/lost* per corner is read from the delta via
     `get_delta_change_in_range()` → `get_delta_at_distance()` → `np.interp` on the
     **1000-pt grid** (`delta_analysis.py:631-702`).
   - `_interpolate_to_distance()` (`:235`) == `np.interp` (used by zone helpers).

4. **Similarity / clustering** (`services/similarity.py:35`) also resample to 1000
   (`np.linspace`+`np.interp`) — not on the qualifying insights path but same pattern.

## C. NaN handling (minor interpolation)

`_safe_array()` (delta_analysis.py:75, corner_analysis.py:200, orchestrator:181)
linearly interpolates interior NaNs via `np.interp`. Applies only to NaN cells.

## D. Config comments that pre-admit the granularity assumption

`apps/analysis_service/core/corner_config.py`:
  - line 9:  "Default values based on typical F1 telemetry (~5 Hz sampling, ~17m between samples)"
  - line 52: "Distance tolerances (meters) - accounts for ~5 Hz telemetry resolution"
  - line 53: "braking_point_tolerance: float = 20.0  # ±20m at ~5 Hz"
These tolerances feed the High/Medium/Low confidence assignment in
`detect_braking_zone_v2` (`:1040-1045`). i.e. the confidence ladder is explicitly
sized to absorb sampling resolution.

## E. Sample's journey (summary)

FastF1 raw car_data (~Y Hz) + pos_data (~Z Hz)
  → get_telemetry(): merge onto union timebase + add_distance/relative_distance  [interp #1, FastF1]
  → API get_telemetry(): downsample only if >5000 pts (NEVER for a quali lap)     [no-op]
  → JSON over HTTP to analysis service (raw arrays preserved)
  → Phase 2: resample to 1000-pt 0..1 grid via np.interp                          [interp #2, ours]
  → Phase 3 brake/apex/exit: detection on RAW arrays;
            per-corner delta read off the 1000-pt grid                            [interp #2 reused]

Gates measured empirically in scripts 01-06.
