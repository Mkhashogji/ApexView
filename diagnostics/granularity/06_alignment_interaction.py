"""
Phase 7: Interaction with the existing distance alignment.

Quantifies what interpolation the Phase-2 alignment already performs:
- real samples (get_telemetry) vs the 1000-pt grid the delta is resampled onto;
- the phantom-density ratio (grid points / real samples);
- demonstrates that get_delta_change_in_range (corner attribution) reads off the
  interpolated grid, so per-corner deltas are sampled at synthetic, not measured,
  positions.
Usage: python 06_alignment_interaction.py <YEAR> <GP> [DRIVER]
"""
import sys
import numpy as np
import _common as C

NUM_POINTS = 1000  # delta_analysis.py DEFAULT_NUM_POINTS / orchestrator


def main():
    year = int(sys.argv[1]); gp = sys.argv[2]
    s = C.load_session(year, gp)
    if len(sys.argv) > 3:
        drivers = [sys.argv[3]]; laps = [C.fastest_lap(s, sys.argv[3])]
    else:
        drivers, laps = C.top_two_drivers(s)
    C.banner("PHASE 7  ALIGNMENT vs RESOLUTION", year, gp, "Q3", drivers, laps)

    drv = drivers[0]; lap = laps[0]
    tel = lap.get_telemetry()
    n_real = len(tel)
    print(f"\n  real samples on lap (get_telemetry)   : {n_real}")
    print(f"  Phase-2 delta grid (np.linspace 0..1) : {NUM_POINTS}")
    ratio = NUM_POINTS / n_real
    print(f"  phantom-density ratio (grid/real)     : {ratio:.2f}x")
    print(f"     -> {NUM_POINTS - n_real} of {NUM_POINTS} grid points "
          f"({100*(1-n_real/NUM_POINTS):.0f}%) are interpolated, not measured.")

    # mean grid spacing vs mean real spacing (metres)
    track_len = float(tel["Distance"].to_numpy()[-1])
    grid_spacing = track_len / (NUM_POINTS - 1)
    real_spacing = track_len / (n_real - 1)
    print(f"\n  track length (telemetry)              : {track_len:.0f} m")
    print(f"  mean REAL sample spacing              : {real_spacing:.1f} m")
    print(f"  mean GRID spacing (what code iterates): {grid_spacing:.1f} m")
    print("     -> alignment provides spatial CO-LOCATION at 1000 pts but cannot")
    print("        add temporal resolution; ~%.0f%% of grid points lie between" %
          (100*(1-n_real/NUM_POINTS)))
    print("        real measurements and carry no independent information.")

    # demonstrate corner-attribution reads off the interpolated grid
    rel = np.linspace(0, 1, NUM_POINTS)
    # how many grid points fall in a typical 80m corner phase window
    phase_m = 80.0
    pts_per_phase_grid = phase_m / grid_spacing
    pts_per_phase_real = phase_m / real_spacing
    print(f"\n  in an 80 m corner-phase window (cause attribution splits a zone in 3):")
    print(f"      grid points : ~{pts_per_phase_grid:.1f}")
    print(f"      REAL samples: ~{pts_per_phase_real:.1f}")
    print("     -> get_delta_change_in_range() interpolates endpoints on the grid;")
    print("        the underlying measured support per phase is only ~%.0f samples." %
          pts_per_phase_real)

    out = {"session": f"{year}_{gp}_Q3", "driver": drv,
           "real_samples": n_real, "grid_points": NUM_POINTS,
           "phantom_density_ratio": ratio,
           "pct_interpolated": 100*(1-n_real/NUM_POINTS),
           "track_len_m": track_len, "real_spacing_m": real_spacing,
           "grid_spacing_m": grid_spacing,
           "real_samples_per_80m_phase": pts_per_phase_real}
    C.save_json(f"06_alignment_interaction_{drv}.json", out)


if __name__ == "__main__":
    main()
