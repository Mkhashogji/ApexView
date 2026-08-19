# WU-4 Findings — Near-zero Δd guard in `compute_deceleration`, and what it measured

**Purpose:** record what the pre-G1 hardening unit WU-4 changed and — more importantly —
what installing the guard revealed about the legacy merged frame. The guard was installed
**ahead of** G1 becoming the first producer capable of driving Δd toward zero, not in
response to an observed failure; on the native head it fires zero times. Its incidental
effect on the legacy head is the first numerical measurement of what the phantom-row
merge actually cost.
**Method:** all figures measured on the cached fixtures (Shanghai 2025 R2 Q PIA/RUS,
Monaco 2025 R8 Q NOR/LEC) via the live `/telemetry` endpoint under each acquisition
head, and via the A/B harness (`tools/ab_harness/run_ab.py`) run from the host against
three code variants — **A** pre-WU-4 (`git show 19e06da:…/corner_analysis.py`, docstring-
only different from `511f0fb`), **B** WU-4 with zero-fill smoothing, **C** WU-4 final
(deficit-renormalised smoothing). Native metrics are byte-identical across A/B/C on both
fixtures; every movement below is legacy-head movement.
**Registered debts untouched:** OPEN-1/OPEN-2 (the smoothing *window* — size and
sample-count semantics — is unchanged; this unit changes only the masking around it),
STOP-3, `circuit_id` forwarding.

---

## 1. The measured cost of the phantom-row merge

The pre-WU-4 guard was `np.where(delta_distance == 0, 0.001, delta_distance)` — an
exact-zero clamp. Measured on the legacy merged frame (`/telemetry?acquisition=legacy`):

| lap | samples | intervals with \|Δd\| < 0.5 m | min \|Δd\| | exact zeros |
|---|---|---|---|---|
| Shanghai PIA | 686 | **27** | 0.0950 m | 0 |
| Shanghai RUS | 694 | **34** | 0.0819 m | 0 |
| Monaco NOR | 521 | **28** | 0.0192 m | 0 |
| Monaco LEC | 531 | **29** | 0.0174 m | 0 |

Native, same laps: 0 / 0 / 0 / 0 sub-0.5 m intervals (min |Δd| 3.74 / 3.20 / 2.15 / 2.22 m).

Because the merged frame has **no exact zeros**, the old clamp **never fired** on it. Every
one of those 27–34 near-zero divisions per lap flowed through unmodified, producing
fabricated decelerations of order 10³–10⁴ m/s² (a 2 km/h step over 0.02 m ≈ 6,300 m/s²,
reproduced by the WU-4 test `test_exact_zero_interval_is_nan_not_fabricated`) that fed
`detect_braking_zone_v2` and `detect_exit_zone_v2`. G0 argued the merge was dishonest in
principle; this is the first quantification of what it did to the detector.

The mechanism is not statistical — it is locatable. Under variant A the legacy detector's
zone boundaries sit **exactly on** guarded-interval positions:

| fixture | A zone boundary / brake point | nearest guarded interval (legacy ref driver) |
|---|---|---|
| Shanghai T8/T9 zone boundary | 2371.6 m | 2371.5 m |
| Shanghai T14 brake point | 5044.0 m | 5044.0 m |
| Monaco T6/T7 zone boundary | 1117.0 m | 1117.0 m |
| Monaco T7/T8 zone boundary | 1230.6 m | 1230.6 m |
| Monaco T8 exit | 1308.8 m | 1308.8 m |

i.e. fabricated spikes *were* the "detections". With the guard (variant C) those events
are undefined (NaN → comparisons False) and the boundaries move: Shanghai T3/T4, T8/T9,
T14/T15; Monaco T6, T7, T8, T16, T17. Legacy `total_corner_delta` moves
Shanghai +0.0128 → +0.0714 s and Monaco +0.9061 → +0.8512 s. Legacy lap-breakdown
closure is unchanged (0.0000 / 0.4924 s), and Shanghai T14/T15 legacy brake points move
**toward native** (5044.0 → 5025.2 m; native 5017.5 m): the two A-era brake-shift FLAGs
(−26.5 m vs 14.3 m local gap) fall within the local gap under C.

## 2. Two incidental detector corrections (behavioural improvements, not regressions)

Line citations are anchored to a commit because bare numbers in a permanent record go
stale silently: "pre-WU-4" = `corner_analysis.py` at commit `19e06da`; "WU-4 tree" = the
file as committed by WU-4 (the guard added ~66 lines above these expressions).

- `detect_exit_zone_v2`, the `decel[exit_idx] >= acceleration_threshold` test
  (`corner_analysis.py:1121` at `19e06da`; `:1187` in the WU-4 tree): under A a fabricated
  *positive* spike counted toward "sustained acceleration" and could trigger exit detection
  at a degenerate interval (Monaco T8 exit at 1308.8 m is one). Under C the interval is
  NaN → False → the streak resets and exit falls to the speed-recovery / max-search paths.
- `detect_braking_zone_v2` stage-2 backward walk, `decel[decel_idx] > braking_decel_threshold`
  (`corner_analysis.py:1037-1038` at `19e06da`; `:1104` in the WU-4 tree): under A a
  fabricated positive spike broke the walk early (brake point too late; Shanghai T14 at
  5044.0 m). Under C the walk continues through the undefined sample to the next defined
  one.

## 3. Zero-fill smoothing bias (found in review, corrected before the golden was captured)

The first WU-4 implementation (variant B) zero-filled guarded positions before the moving
average, biasing each neighbour toward zero by up to 1/w. On the native head this never
fires; on legacy it fires 27–34×/lap. The three-way comparison isolates it:

| fixture | A→B moved corners | A→C moved corners | B vs C differ | B−C on legacy total_corner_delta |
|---|---|---|---|---|
| Shanghai | T8, T9 | T3, T4, T8, T9, T14, T15 | **T3, T4, T14, T15** | **−58.6 ms** (0.0128 vs 0.0714) |
| Monaco | T6, T7, T8, T16, T17 | same | none | 0.0 ms |

Material on Shanghai: zero-fill pulled the true heavy-braking values next to guarded
intervals above the −5 m/s² threshold, so the stage-2 walk stopped at the same (wrong)
5044.0 m as A — B looked deceptively baseline-identical in aggregate while suppressing a
real detection change. Negligible on Monaco (B ≡ C). Fix: renormalise by the *guarded*
deficit only (`convolve(filled, ones/w) · w/(w − deficit)`), leaving `np.convolve`'s edge
zero-padding untouched so array edges and every guard-free window are **bit-identical** to
the plain convolution (`np.array_equal`, verified — the literal `convolve(x, ones(w))/(w−deficit)`
form is *not* bit-identical: 600/600 trials differ at ~1e-16). Golden captured against C.

## 4. Negative Δd (measured, not fixed)

Distance running backwards is a distinct pathology from distance standing still; the guard
catches it only when |Δd| < 0.5 m (a large negative Δd would produce a sign-flipped
deceleration and pass). Measured on both heads, both fixtures, all four laps: **zero
negative Δd intervals** (native and legacy). No exposure today; recorded so G1's position
harvest — which introduces independently-derived distance observations — is measured
against it.

## 5. Open structural question — what the legacy-insights golden actually measures

The legacy head is verbatim in *acquisition* only. Both heads flow through the same analysis
service, including `compute_deceleration`, so `legacy insights value-identical to golden`
measures **shared downstream code**, not the rollback contract. The goldens that do express
that contract — track, telemetry, delta — remained byte-identical throughout WU-4 (harness
gate #4). Every subsequent analysis-service honesty fix (WU-2 next) will move this check
again. Two facts constrain the remedy: `run_ab.py:319-320` (at `19e06da`; the file is
unchanged since `d2f0dfa`) applies `check.hard()` to this identity unconditionally —
`check.hard(golden_ins == live_ins, …)` — and no registry scope reaches it, so a `known_deviations.json` entry
would be inert; and the pre-WU-4 golden is preserved permanently at `511f0fb`, so a
re-snapshot destroys no evidence. Whether the check should be re-scoped or retired is a
decision for its own unit.

Also observed: `diagnostics/g0/capture_golden.ps1` sends no `acquisition` override and
predates the native default — run today it captures the **native** head (probe run:
`telemetry_shanghai.json` = 48,010 bytes vs the 102,758-byte legacy golden). The WU-4 legacy
insights were therefore captured through the harness's own `fetch_head(fixture, "legacy")`,
i.e. exactly the request the oracle compares against; the script needs an acquisition
parameter before it is used again for `golden/legacy/`.

## 6. Bearing on G1

- G1's position harvest produces denser, irregularly spaced distance observations; the guard
  now makes a degenerate interval *absent* (NaN, comparisons False) rather than a fabricated
  spike, and the WARNING carries the guarded-interval count for a future provenance channel.
- The Shanghai T14 result is the template for what G1 must not repeat: a plausible-looking
  aggregate (B ≈ A) hiding a suppressed detection change. Bit-identity tests on the untouched
  arm, and per-corner attribution on the moved arm, are the pattern.
