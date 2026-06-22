# OPEN-1 / OPEN-2 Forensics — Monaco T10 / T17 brake-point shifts

**Purpose:** give the owner the evidence to rule on the two findings that block the G0
gate. Read-only investigation; no application code changed.
**Method:** the production detection path reconstructed by importing the *real*
analysis-service functions (`compute_deceleration`, `detect_apex_from_speed_v2`,
`detect_braking_zone_v2`) and feeding them the exact arrays each acquisition head serves
for the reference driver (NOR). Reproduction is exact: legacy 1966.08 / 2807.91 m and
native 1946.93 / 2794.61 m match the production A/B report to ±0.02 m.
**Scripts / raw output:** [`open_findings_forensics.py`](open_findings_forensics.py) →
[`open_findings_forensics_output.txt`](open_findings_forensics_output.txt);
[`open_findings_supplement.py`](open_findings_supplement.py) →
[`open_findings_supplement_output.txt`](open_findings_supplement_output.txt).

> **Critical production fact (verified):** the orchestrator calls `analyze_corners_v2`
> **without** `circuit_id` (`performance_orchestrator.py:630-651`), so detection runs on
> the **default** `CornerAnalysisConfig` — `braking_decel_threshold=-5.0`,
> **`decel_smoothing_window=5`**, `apex_search_margin=50`. Monaco's per-circuit overrides
> are dead code on this path. All reconstruction uses the default config; it reproduces
> the production brake points exactly, which independently confirms the config in use.

---

## VERDICTS (decisive evidence first)

### OPEN-1 — Monaco T10 (shift −19.2 m): **H-defect, located in EXCLUDED detector code — NOT a G0 rewire defect.**

**Single decisive piece of evidence:** on the *same native arrays*, varying only
`compute_deceleration`'s smoothing window, the shift **collapses from −19.2 m to −0.1 m**:

| smoothing window | legacy bp | native bp | shift |
|---|---|---|---|
| 1 (none) | 1966.1 m | 1966.0 m | **−0.1 m** |
| 3 | 1966.1 m | 1966.0 m | −0.1 m |
| 5 (production) | 1966.1 m | 1946.9 m | **−19.2 m** |

A G0 acquisition / registration / indexing defect could not switch off when the smoothing
window changes (the native arrays are identical across the three rows). The shift is
therefore produced by the smoothing kernel, not by G0's code. Corroborating: the native−merged
**distance registration delta is −0.088 m** at this corner; the **detected apex is identical**
(legacy 2077.3 m, native 2077.2 m); the **boolean brake-on sample is found at the same
physical point** on both substrates (1966.0 / 1966.1 m); the legacy brake point sits on a
**real FastF1 `Source='car'` row** (so this is not a phantom-row story).

**Mechanism (exact line):** `compute_deceleration` smooths the kinematic deceleration with a
**sample-count** kernel — `kernel = np.ones(smoothing_window)/smoothing_window;
decel = np.convolve(decel, kernel, mode="same")` (`corner_analysis.py:864-866`). Five samples
span ~2× the physical distance on the honest (sparser) native frame, so the kernel bleeds the
downstream heavy braking (speed 286→240→185 km/h at 1992–2006 m) backward onto the
boolean-brake-on sample at 1966 m, where the *smoothed* decel reads **−13.8 m/s²** even though
the raw decel there is ~+0.8 (speed is still flat, 285→286). The two-stage backward walk
(`detect_braking_zone_v2:1024-1034`), seeing "heavy braking already underway," steps back one
real sample to 1946.9 m. On the denser merged frame the kernel reaches half as far, reads
+0.5 m/s² at 1966 m, and the walk stops there.

**Blast radius:** global. The same sample-count smoothing affects every corner on every
circuit; it also produces the identical −19.2 m shift at Monaco T11 (shared detected apex)
and several moderate Shanghai shifts. **G0 scope:** OUT — the fix (a distance-based smoothing
window, or window scaled to spacing) edits excluded detector code (`compute_deceleration`).
**Recommended disposition:** register under root cause *"detector decel-smoothing window
(sample-count) × native spacing"*, bound 25 m, owner = zone-logic/detector gate — i.e. the
same gate that already owns STOP-3 and the gap-overlapped corners.

### OPEN-2 — Monaco T17 (shift −13.3 m): **same H-defect mechanism, with an additional H-quantisation signature on the legacy side.**

**Single decisive piece of evidence:** the shift collapses to **−0.1 m at smoothing window=1**
(2807.9 vs 2808.0 m) and only appears at window=5 (2794.6 m) — identical signature to T10, so
the net shift is smoothing-driven.

**The quantisation corroborator:** the legacy brake point (2807.9 m) sits on a FastF1
**`Source='pos'` row — interpolated car channels**, i.e. phantom precision absent from the
native frame. And the shift equals **1.00× the actual native sample gap straddling the brake
point** (13.3 m), versus the misleading "1.58× the *median* local gap" the harness reported
(the median local gap there is 8.4 m because the spacing is jittered — the gap actually
straddling the brake point is 13.3 m). So at window=1 the native detector lands on the nearest
real sample to legacy's phantom point (pure quantisation, ~0 m net), and the production
window=5 smoothing then walks it back exactly one real sample.

**Mechanism / blast radius / scope:** identical to OPEN-1 (`compute_deceleration:864-866`,
global, out of G0 scope). Registration deltas −0.090 m (at 2808 m) / +0.162 m (at 3000 m).
**Recommended disposition:** register alongside T10 under the same root cause, bound 22 m,
owner = zone-logic/detector gate.

### Adversarial verification of this verdict
Two independent skeptics were tasked to **refute** "the shifts are excluded-detector smoothing,
not G0 code" by reading the actual code and constructing a G0-code-defect explanation
consistent with the evidence. Both returned **VERDICT-STANDS**. The decisive logical argument
(forced by the code): `compute_deceleration` computes the raw kinematic decel directly from the
served `Distance`/`Speed`; at window=1 the `np.convolve` branch is skipped, so the detector sees
the raw decel on the native arrays — and it already agrees with legacy to 0.1 m. *Any* G0
mis-integration/mis-registration of those arrays would be baked into that raw decel and would
make window=1 diverge too. It does not. The two requirements — "G0 corrupts the served arrays"
and "window=1 brake point matches legacy to 0.1 m" — are mutually exclusive because the raw decel
is a pure function of those same arrays. Skeptic 2 independently re-derived the T17 interval
decel: window=1 → −3.49 m/s² (> −5, walk stops at 2807.9 m); window=5 → −7.29 m/s² (heavy, walk
back to 2794.6 m). (Both skeptics also surfaced an unrelated cache-write fidelity gap — recorded
in [G0_DETAILED_REPORT.md](G0_DETAILED_REPORT.md) §4 #13 — and the `circuit_id`-not-forwarded
systemic point, already noted there.)

### Bottom line for the gate
Neither OPEN finding is a defect in G0's authored acquisition, registration, or indexing code
— proven by the controlled window-sweep on identical native arrays. Both are the pre-existing
sample-count smoothing window in excluded detector code, *exposed* (not caused) by the honest
substrate. The recommendation is to **convert OPEN-1/OPEN-2 to registered known-deviations**
under a single new root cause and assign them to the zone-logic/detector gate — the gate that
already owns every other G0 brake-zone debt. With that, the gate's only remaining blocker is
the owner's approval of this disposition.

---

## Evidence detail

### 1. The two hypotheses, tested directly

| Hypothesis (owner's definition) | T10 | T17 |
|---|---|---|
| **H-quantisation** — legacy bp on an interpolated phantom row; native snaps to nearest real sample | legacy bp on a **real `car` row** → does not apply as the *cause* | legacy bp on an **interpolated `pos` row** → applies, but only ~0 m of the net shift (window=1) |
| **H-defect** — bookkeeping / registration / indexing / *threshold-or-smoothing interacting with native spacing* puts the bp on the wrong real sample | **smoothing × spacing** (window-sweep decisive); registration −0.09 m rules out bookkeeping | **smoothing × spacing** (window-sweep decisive); registration ≤0.16 m rules out bookkeeping |

The owner's H-defect clause explicitly includes *"threshold interacting badly with native
spacing."* That is exactly what both corners exhibit — but the interacting code is the
pre-existing detector smoothing, on the G0 exclusion list, not the G0 rewire.

### 2. Threshold-crossing trace (production window=5)

**T10** — both find boolean brake-on at ~1966 m; the backward walk diverges:
- legacy: at 1966.1 m, `decel[i-1]=+0.5 > -5.0` → **STOP** → 1966.08 m
- native: at 1966.0 m, `decel[i-1]=-13.8 ≤ -5.0` → walk back → at 1946.9 m, `decel[i-1]=+0.6 > -5.0` → STOP → 1946.93 m

**T17** — both find boolean brake-on at ~2808 m:
- legacy: at 2808.0 m, `decel=-8.8` → walk back **0.1 m** to the adjacent `pos` row 2807.9 m (`decel=-2.3`) → STOP → 2807.91 m
- native: at 2807.9 m, `decel=-7.3` → walk back one real sample to 2794.6 m (`decel=+0.7`) → STOP → 2794.61 m

### 3. Native braking-zone sample table (T17, abridged — full in the raw output)

| idx | dist m | speed | brake | dt_prev m | smoothed decel | marker |
|---|---|---|---|---|---|---|
| 213 | 2781.1 | 197 | 0 | 8.8 | +6.0 | |
| **214** | **2794.6** | 202 | 0 | 13.5 | +0.7 | **NATIVE brake point** |
| **215** | **2807.9** | 199 | 1 | 13.3 | −7.3 | boolean brake-on; legacy bp between (native axis) |
| 216 | 2816.4 | 190 | 1 | 8.4 | −24.0 | |

The native frame has *no* sample between 2794.6 and 2807.9 m (gap 13.3 m); the merged frame
had an interpolated `pos` row at 2807.9 m on which legacy stopped.

### 4. Registration deltas (native − merged Distance at the same instant)

T10: −0.088 m at apex, −0.088 m at the brake point. T17: +0.162 m at apex, −0.090 m at the
brake point. All ≪ 5 m — the distance-integration rewire did not move the corner windows.

### 5. Local-gap nuance (median vs actual straddling gap)

| corner | shift | median local gap (±60 m) | actual straddling gap | ×median | ×actual |
|---|---|---|---|---|---|
| T10 | 19.2 m | 13.9 m | 12.7 m | 1.38 | **1.51** |
| T17 | 13.3 m | 8.4 m | 13.3 m | 1.58 | **1.00** |

For T17 the harness's "1.58× median" overstates the effect — measured against the gap that
actually straddles the brake point, the shift is **exactly one real sample**. For T10 the
shift is genuinely ~1.5 real samples (the smoothing walked it one full sample past the brake-on
point, which itself sits mid-gap).

---

## Generality check — are T10/T17 outliers or the tail of a distribution?

All corners, both circuits, reference driver, default config
([`open_findings_supplement_output.txt`](open_findings_supplement_output.txt)):

```
|shift| / actual-straddling-gap   (n=35 corner instances)
   0-.25 | ##########  10
  .25-.5 | #######      7
  .5-.75 | ######       6
   .75-1 | #####        5     <- 28 of 35 are <= one real sample
  1-1.25 | #            1     (Monaco T10/T17 region)
 1.25-1.5|              0
   1.5-2 | ##           2
     2-3 | ##           2     (Shanghai T14/T15 brake-on-fallback double)
      >3 | ##           2     (Shanghai T9 6.96x, Monaco T9 13.06x — Tunnel/no-braking)
  median=0.56  p90=2.07  max=13.06
```

**Reading:** 28 of 35 corner-instances shift by ≤ one real native sample — the substrate swap
moved most brake points imperceptibly. T10/T17 sit in the near tail (1.0–1.5× actual), produced
by the smoothing mechanism. The genuine outliers are the two **T9** corners (Shanghai 6.96×,
Monaco 13.06× — both no-braking-event "kink" corners, Monaco's also over the Tunnel acquisition
gap); their shifts **persist at smoothing window=1** (Monaco T9: +82.0 m at window 1/3/5), so
they are structural, not smoothing. **Conclusion:** T10/T17 are the visible tail of the
smoothing distribution, not isolated outliers and not defects — exactly the class that should be
owned by the detector gate.

### Causal decomposition of the five Monaco brake-shift violators
| corner | shift | window=1 shift | class | current STOP-4 disposition | forensic refinement |
|---|---|---|---|---|---|
| T9 | +82.0 m | +82.0 m (persists) | structural (no-braking + Tunnel gap) | registered (gap) | confirmed structural |
| T10 | −19.2 m | −0.1 m (collapses) | smoothing × spacing | **OPEN-1** | → register, detector gate |
| T11 | −19.2 m | −0.1 m (collapses) | smoothing × spacing | registered (gap) | gap overlap is *incidental*; shift is smoothing |
| T14 | −16.5 m | −16.5 m (persists) | mixed/structural | registered (gap) | partly structural — confirmed not pure smoothing |
| T17 | −13.3 m | −0.1 m (collapses) | smoothing × spacing (+ legacy phantom row) | **OPEN-2** | → register, detector gate |

This refines (does not overturn) the STOP-4 sign-off: T9 and T14 are genuinely structural;
T10/T11/T17 share the smoothing root cause. The owner accepted T11 as gap-overlapped — true of
the zone, though the *shift* is smoothing-driven; no action needed, but recorded here for the
detector gate.
