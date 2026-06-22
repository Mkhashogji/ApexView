# G0 A/B Report — legacy vs native acquisition

**Hard failures: 0** | KNOWN-DEVIATIONS: 4 | OPEN FINDINGS: 2 | Flags: 23 | Checks passed: 89

## KNOWN-DEVIATIONS (registered acceptances — bounded, never silently green)
- KNOWN-DEVIATION [shanghai] STOP-3: lap_breakdown closure 0.0858s <= registered bound 0.100s (accepted 2026-06-12, owner: zone-logic)
- KNOWN-DEVIATION [monaco] STOP-4 T9: |shift| 82.0m <= bound 100m (gap-overlap)
- KNOWN-DEVIATION [monaco] STOP-4 T11: |shift| 19.2m <= bound 25m (gap-overlap)
- KNOWN-DEVIATION [monaco] STOP-4 T14: |shift| 16.5m <= bound 22m (gap-overlap)

## OPEN FINDINGS (recognised, NOT accepted — owner decision pending)
- OPEN-FINDING [monaco] T10: shift -19.2m vs local gap 13.9m — OPEN-1 pending owner sign-off
- OPEN-FINDING [monaco] T17: shift -13.3m vs local gap 8.4m — OPEN-2 pending owner sign-off

## Flags (review, not failures)
- FLAG [shanghai] T1 apex min-speed diff +0.543 km/h (fixed legacy window)
- FLAG [shanghai] T4 apex min-speed diff +2.075 km/h (fixed legacy window)
- FLAG [shanghai] T5 apex min-speed diff +9.000 km/h (fixed legacy window)
- FLAG [shanghai] T7 apex min-speed diff +7.000 km/h (fixed legacy window)
- FLAG [shanghai] T9 brake shift +157.4m vs local gap 21.0m
- FLAG [shanghai] T10 apex min-speed diff +2.311 km/h (fixed legacy window)
- FLAG [shanghai] T12 apex min-speed diff +6.000 km/h (fixed legacy window)
- FLAG [shanghai] T13 apex min-speed diff +0.288 km/h (fixed legacy window)
- FLAG [shanghai] T14 brake shift -26.5m vs local gap 14.3m
- FLAG [shanghai] T15 brake shift -26.5m vs local gap 14.3m
- FLAG [shanghai] T15 apex min-speed diff +0.172 km/h (fixed legacy window)
- FLAG [shanghai] T16 apex min-speed diff +6.000 km/h (fixed legacy window)
- FLAG [monaco] T2 apex min-speed diff +16.000 km/h (fixed legacy window)
- FLAG [monaco] T4 apex min-speed diff +0.609 km/h (fixed legacy window)
- FLAG [monaco] T8 apex min-speed diff +4.000 km/h (fixed legacy window)
- FLAG [monaco] T10 brake shift -19.2m vs local gap 13.9m
- FLAG [monaco] T10 apex min-speed diff +0.366 km/h (fixed legacy window)
- FLAG [monaco] T12 apex min-speed diff +5.000 km/h (fixed legacy window)
- FLAG [monaco] T14 apex min-speed diff +2.984 km/h (fixed legacy window)
- FLAG [monaco] T17 brake shift -13.3m vs local gap 8.4m
- FLAG [monaco] T17 apex min-speed diff +16.000 km/h (fixed legacy window)
- FLAG [monaco] T18 apex min-speed diff +15.000 km/h (fixed legacy window)
- FLAG [monaco] T19 apex min-speed diff +9.000 km/h (fixed legacy window)

## Fixture: shanghai
| metric | legacy | native |
|---|---|---|
| official gap | +0.082s | +0.082s |
| delta-grid closure err | 0.00e+00 | 0.00e+00 |
| lap_breakdown err | 0.000s | 0.086s |
| total corner delta | +0.013s | +0.242s |
| samples | PIA:686, RUS:694 | PIA:332, RUS:343 |

### Per-corner diff
| T | brake leg (m) | brake nat (m) | shift (m) | local gap (m) | ok | minV diff (km/h) | dΔ leg (s) | dΔ nat (s) | conf |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 24.9 | 24.6 | -0.3 | 17.8 | ✓ | +0.543 | +0.055 | -0.036 | M→M |
| 2 | 468.4 | 467.8 | -0.6 | 17.6 | ✓ | +0.000 | +0.337 | +0.069 | M→M |
| 3 | 595.1 | 594.5 | -0.6 | 16.6 | ✓ | +0.000 | -0.142 | -0.174 | H→H |
| 4 | 830.7 | 830.1 | -0.6 | 6.9 | ✓ | +2.075 | -0.078 | +0.090 | M→M |
| 5 | 1015.3 | 1026.7 | +11.4 | 15.0 | ✓ | +9.000 | +0.007 | +0.015 | M→M |
| 6 | 1431.0 | 1414.3 | -16.6 | 21.9 | ✓ | +0.000 | +0.047 | -0.101 | M→M |
| 7 | 1654.7 | 1666.5 | +11.8 | 12.5 | ✓ | +7.000 | -0.011 | +0.048 | M→M |
| 8 | 2198.9 | 2186.1 | -12.8 | 23.5 | ✓ | +0.000 | +0.155 | +0.003 | M→M |
| 9 | 2254.6 | 2412.0 | +157.4 | 21.0 | ✗ | +0.000 | +0.217 | +0.056 | M→M |
| 10 | 2566.7 | 2568.9 | +2.2 | 11.3 | ✓ | +2.311 | -0.182 | +0.035 | M→M |
| 11 | 3062.6 | 3069.5 | +6.9 | 9.1 | ✓ | +0.000 | -0.221 | +0.148 | M→M |
| 12 | 3331.7 | 3332.5 | +0.9 | 15.2 | ✓ | +6.000 | -0.056 | +0.020 | M→M |
| 13 | 3557.2 | 3574.9 | +17.7 | 20.1 | ✓ | +0.288 | -0.015 | -0.005 | M→M |
| 14 | 5044.0 | 5017.5 | -26.5 | 14.3 | ✗ | +0.000 | +0.143 | +0.052 | H→H |
| 15 | 5044.0 | 5017.5 | -26.5 | 14.3 | ✗ | +0.172 | -0.124 | +0.030 | M→L |
| 16 | 5044.0 | 5054.4 | +10.4 | 14.3 | ✓ | +6.000 | -0.120 | -0.009 | M→H |

### Gap inventory (native)
- PIA: dt=0.76s (ratio 3.2) at 485–542m
- RUS: dt=0.76s (ratio 3.2) at 3249–3287m
- RUS: dt=0.84s (ratio 3.5) at 4414–4492m

Runtimes (s): telemetry 6.71→4.84, insights 10.86→13.52

## Fixture: monaco
| metric | legacy | native |
|---|---|---|
| official gap | +0.109s | +0.109s |
| delta-grid closure err | 0.00e+00 | 0.00e+00 |
| lap_breakdown err | 0.492s | 0.257s |
| total corner delta | +0.906s | +0.157s |
| samples | NOR:521, LEC:531 | NOR:257, LEC:258 |

### Per-corner diff
| T | brake leg (m) | brake nat (m) | shift (m) | local gap (m) | ok | minV diff (km/h) | dΔ leg (s) | dΔ nat (s) | conf |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 65.0 | 57.1 | -7.9 | 21.6 | ✓ | +0.000 | +0.060 | +0.059 | H→M |
| 2 | 111.9 | 124.7 | +12.8 | 17.2 | ✓ | +16.000 | +0.039 | -0.011 | M→H |
| 3 | 613.7 | 606.2 | -7.4 | 20.6 | ✓ | +0.000 | +0.012 | -0.018 | H→H |
| 4 | 613.7 | 606.2 | -7.4 | 20.6 | ✓ | +0.609 | -0.041 | -0.066 | H→H |
| 5 | 613.7 | 606.2 | -7.4 | 20.6 | ✓ | +0.000 | -0.097 | -0.066 | L→M |
| 6 | 820.1 | 820.1 | -0.1 | 13.7 | ✓ | +0.000 | +0.107 | +0.022 | H→H |
| 7 | 1007.5 | 991.0 | -16.5 | 19.6 | ✓ | +0.000 | -0.050 | -0.161 | H→H |
| 8 | 1007.5 | 1013.6 | +6.1 | 19.6 | ✓ | +4.000 | -0.064 | -0.041 | M→M |
| 9 | 1350.2 | 1432.1 | +82.0 | 6.6 | ✗ | +0.000 | +0.017 | -0.032 | M→M |
| 10 | 1966.1 | 1946.9 | -19.2 | 13.9 | ✗ | +0.366 | +0.522 | +0.257 | H→M |
| 11 | 1966.1 | 1946.9 | -19.2 | 13.9 | ✗ | +0.000 | +0.449 | +0.137 | L→L |
| 12 | 1997.6 | 2006.4 | +8.8 | 10.4 | ✓ | +5.000 | -0.263 | -0.036 | M→M |
| 13 | 2278.2 | 2279.4 | +1.3 | 15.4 | ✓ | +0.000 | -0.004 | +0.008 | M→M |
| 14 | 2295.9 | 2279.4 | -16.5 | 15.9 | ✗ | +2.984 | +0.062 | +0.005 | M→M |
| 15 | 2575.0 | 2560.9 | -14.1 | 18.2 | ✓ | +0.000 | +0.088 | -0.015 | H→H |
| 16 | 2575.0 | 2560.9 | -14.1 | 18.2 | ✓ | +0.000 | +0.349 | +0.246 | M→M |
| 17 | 2807.9 | 2794.6 | -13.3 | 8.4 | ✗ | +16.000 | -0.004 | -0.020 | M→M |
| 18 | 2816.5 | 2816.4 | -0.1 | 8.1 | ✓ | +15.000 | -0.260 | -0.100 | M→M |
| 19 | 2963.3 | 2964.9 | +1.5 | 8.0 | ✓ | +9.000 | -0.014 | -0.010 | M→M |

### Gap inventory (native)
- NOR: dt=0.76s (ratio 3.2) at 851–884m
- NOR: dt=1.08s (ratio 4.5) at 1642–1721m
- NOR: dt=0.88s (ratio 3.7) at 2408–2466m
- LEC: dt=1.16s (ratio 4.8) at 883–943m
- LEC: dt=0.76s (ratio 3.2) at 2091–2116m
- LEC: dt=1.08s (ratio 4.5) at 3076–3147m

Runtimes (s): telemetry 5.68→4.51, insights 11.04→15.68
