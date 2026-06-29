# CLAUDE.md

Guidance for working in this repository.

## What this is

An interactive, real-time browser instrument: one self-organising control loop,
four controls, that produces recognisable psychiatric regimes when a control is
driven out of range. It distinguishes **malfunctions** (loop machinery breaks)
from **miscalibrations** (machinery intact, dial wrong). See `README.md` for the
user-facing description.

## Where the code lives

- `docs/index.html` — **the entire app**: model, rendering, and UI in one
  self-contained file (inlined HTML + CSS + JS, zero dependencies). This is
  deliberate: it must run from `file://` and from GitHub Pages without a build
  step or a server.
- `index.html` (repo root) — a redirect into `docs/`.
- `.github/workflows/pages.yml` — publishes `docs/` to GitHub Pages.

There is no build, no bundler, no package.json. Edit `docs/index.html` directly.

## The model (single source of truth: the `CONFIG` block)

All parameters and classifier thresholds live in one `CONFIG` object at the top
of the script. Retune there; nothing is hard-coded elsewhere.

- **Division `p`** — replicator dynamics on a probability simplex over `n`
  coalitions on the unit circle. Payoff = coherence (`G`, pull toward the
  precision-weighted consensus `m`) + world-tracking (`lambda`, pull toward the
  discounted evidence `yhat`) − crowding (`c`). Order parameter: Herfindahl
  concentration `H`.
- **Fill `F`** — PI homeostat (`kP` proportional, `kI` integral) defending a
  setpoint. Feast/famine (`env`) shifts that setpoint; `sigmaF` is always-on
  noise.
- **Precision `rho`** — per-channel weight on the consensus `m` and the coherence
  term; relaxes toward an evidence-fit target at internal rate `phi`. NOT a board
  control, and NOT the autism mechanism: exposing its retuning rate (`flex`) was
  tested and rejected (precision is not separable from `G` — see findings).
- **Evidence** — a slow Lissajous wander at radius `yR`. The bar's averaging
  clock is `tau`, the per-level horizon: one constant doing the scoring/evidence
  horizon (`yhat` smoothing), the inter-level EMA read, AND the level's whole
  reconfiguration rate. In the BUILT model that clock is exposed as **`tauW`**
  (the shortening factor; short = ADHD); `delta`/`tauMin`/`tauMax` are the
  vestigial single-level form. `tauW` is the bar's clock; `kP` is its damping —
  bipolar (damping) and ADHD (clock) are the two faults of the one fill homeostat
  (siblings, not the same break).

### The board controls → regimes (the new regime: all four at the TOP)

**All four disorders are breaks of the world-facing top contest** — two axes,
each broken two ways. They are NOT depth-located (the earlier "trait disorders
live at n-1, contained" framing is RETIRED: emergence from the ground is ruled
out — see findings). The four are per-level controls set on the top. The
gross/subtle split lives WITHIN each axis: the violent break trips a gross label,
the milder break is trace-level (reads "healthy" on the headline, plain in the
lines).

| Axis | Control | High / hard break | Low / mild break |
|---|---|---|---|
| **Division** (binding) | `G` coherence gain | high → division collapses, frozen monopoly = **schizophrenia** (gross) | low → weak binding, H sags / churns = **autism**, weak central coherence (trace-level; sharpens under ambiguous input) |
| **Fill** (the one homeostat, two sibling faults) | `kP` damping / `tauW` clock | `kP` → floor → fill oscillates, limit cycle = **bipolar** (gross) | `tauW` short → fill hugs setpoint, fast decorrelated jitter = **ADHD** (trace-level: variance DOWN, ac1 DOWN — the B fingerprint, opposite of bipolar) |

Both trace-level fingerprints are readable AT the top when applied at the top:
ADHD's flat fill (variance ~35x down) unconditionally; autism's H-sag faintly
under clear input, pronounced under ambiguous (H 0.38→0.26). (`kP` floor is
small-positive: exactly 0 is undamped and blows up.)

Plus the environment: `chaos` scales the external noise (volatility); `env` is
the feast/famine tilt on it (`env` > 0 floods/manic, `env` < 0 starves/depressed).

The fill pair are siblings on one homeostat: `kP` is its **damping**, `tauW` its
**averaging clock**; they cross-dissociate (A-vs-B protocol below). The division
pair is `G` alone (high vs low) — there is no separate precision-flexibility
control (findings). `delta`, `tauMin`, `tauMax`, `phi` survive only in the
isolated single-level core (`P.levels <= 1`), never run; not board controls.

### Classifier

`classify(d, P)` is a priority cascade on windowed diagnostics: collapse (`H` >
`H_collapse`) → oscillation (`ampF` > `amp_osc`) → scatter (`H` < `H_scatter`) →
tracking lost (`err` > `errLost`) → flooded/starved (`|F − Fstar|` > `band`) →
healthy. Diagnostics are **windowed means/amplitudes**, not instantaneous values
— the instantaneous signals are noisy enough to make a label flicker.

Known and intended: the hard breaks (schizophrenia's collapse, bipolar's
oscillation) produce clean named labels; the mild breaks on the same two axes
(autism = low `G`, ADHD = short `tauW`) are trace-level and read as "healthy" on
the gross label by design — they live in the trace lines and the fingerprints
(autism: H sag/churn; ADHD: fill variance DOWN / decorrelated), not in a
collapsed state. Do not fake a label for them.

In the built multi-level model the classifier reads the parts that matter for
each regime: division (collapse/scatter/tracking) at the fast bottom nucleus
(division is a current-level quantity), fill (oscillation/flood/starve) at the
slow top, where a break only registers once it has propagated up.

## What today's implementation established (the autism / ADHD result)

Two attempts to add a fourth, separate control each ended in a **structural
result, not a bug** — the model twice refused to collapse two things into one,
which is exactly what makes it a real instrument (it can say no). Record these as
findings; do not "fix" them.

### 1. ADHD = short averaging clock `tauW` (BUILT, confirmed)
Exposed the per-level averaging clock as `tauW` (the shortening factor on a
level's one clock: the homeostat bar, the scoring/`yhat` horizon, and the
inter-level EMA read are all the same constant; `tauW=1` healthy, `<1` runs the
whole level faster). Short `tauW @ n-1` reproduces the **B fingerprint** by
prediction and dissociates cleanly from the `kP` damping break:
- n-1 fill variance: healthy 5.2e-3 -> ADHD 3.4e-4 (DOWN ~15x) vs bipolar 1.3e-1 (UP).
- n-1 lag-1 ac1: healthy 0.999 -> ADHD 0.973 (decorrelated) vs bipolar 0.998 (pinned).
- Contained: ADHD top variance ~ baseline (the fast jitter is low-passed); headline
  stays healthy (trait-level). Variance-DOWN direction is dt-robust (direction
  stable, magnitude not). `tauW` REPLACED the internal `clk` factor (it is its
  inverse: `clk>1=faster` became `tauW<1=faster=short clock`).

### 2. Precision flexibility is NOT a separable control (tested, rejected)
The "precision flexibility = autism" hypothesis (a per-channel `rho` with an
inverse-volatility target, relaxing at a rate `flex`; autism = `flex->0`) was
implemented faithfully and tested multi-run. Result: with the regimes intact,
freezing `flex` does **nothing** (precision is not on the critical path); making
it load-bearing (precision-weighting the world-fit term) makes `flex` bite but
**scatters every regime** (healthy tracking-lost, schizophrenia stops collapsing,
H ~0.25 everywhere). No setting is both load-bearing and non-destructive. **The
precision LEVEL is already `G`** (they multiply in the one coherence term); there
is no room for a separate precision-flexibility rate. The control was reverted.
This is the first "no": G and precision are not separable on the division side.

### 3. The G axis carries weak central coherence but NOT rigidity (tested)
Pre-registered G-axis test (G level x input clarity; Variant A static-G, Variant
B frozen-G-flexibility; rigidity judged by a **reweighting probe**, not by
H-pinned-high). Verdict = the test's outcome 3:
- **Weak-central-coherence face: YES.** Low / frozen-low `G` in an ambiguous
  field loses concentration (H 0.52 -> 0.34 when G is frozen and cannot rise). The
  freeze is non-inert.
- **Insistence-on-sameness / rigidity face: NO.** A high-G monopoly still
  *follows* a world shift (reweighting probe = 1) -> that is strong binding, not
  rigidity. Frozen-G is no slower to follow a shift than healthy. No G setting
  produces lock-AND-fail-to-follow.

**Why, and read this as a claim the model is MAKING, not a gap:** the world-fit
term (`lambda*||u - yhat||^2`) is **unconditional** -- it always pulls the winner
toward the current world -- so the contest follows world changes regardless of
any binding/precision lesion. Therefore, in this architecture, **insistence on
sameness cannot be a binding failure.** The model predicts autism's two faces
have **different mechanisms**: weak central coherence is a binding/integration
deficit (the contest, the `G` axis); insistence on sameness is a gating of
world-coupling the contest deliberately does not reduce to binding. They co-occur
in a person because both are hit, not because they are one thing. This is the
second "no": weak-coherence and rigidity are not one mechanism.

### The rigidity face: a characterized edge, NOT a TODO
Autism is **half-captured by design, for a principled reason**. The contest model
captures the **perceptual/integration** face (weak central coherence, real-time,
the `G` axis). The **behavioral/insistence** face is hypothesized to live at a
different level of description -- the **developmental-basin** machinery (sameness
= a deep canalized basin resisting remaking), slow and learned -- not the fast
contest. Forcing rigidity into the contest would be the same category error as
forcing masking's learned content into the fast dynamics.

**Scoped, NOT built (do not build at the end of a session):** a possible
contest-level mechanism for rigidity is a **gateable world-fit** -- route the
world-pull through a local precision/attention term a lesion can suppress
*locally* without globally zeroing it (naive global zeroing scattered every
regime). It modifies the one term every regime depends on, so the failure mode is
"broke schizophrenia and bipolar to add half of autism." Pursue ONLY if the
basin-level account does not cover rigidity, cold and fresh, with the FULL regime
suite as a gate, as the first thing in a session, never the last. Until then the
honest statement is: weak coherence = the contest; insistence on sameness = the
basin (or an unbuilt gateable-world-fit), two levels, not one control.

### Next-session queue (do cold and fresh, in this order)
1. **ADHD behavioral test (scatter vs hyperfocus) -- RUN, POSITIVE.** Short
   clock, winner strength varied by input clarity, at the world-facing level
   (4-seed). Under the short clock behavior depends ONLY on winner strength:
   weak/ambiguous winner -> scatter (switch rate ~0.0073, ~2x), strong winner ->
   held (~0.0045, ~= healthy 0.0043 = relative hyperfocus). Healthy clock is flat
   regardless (~0.0037-0.0043). So scatter and hyperfocus are ONE mechanism (the
   short clock), selected by input -- they come paired in a carrier, as
   predicted. Caveat: the split shows at the level that reads the world DIRECTLY;
   injected at n-1 it washes out (input arrives pre-stabilized from the top),
   consistent with ADHD being contained there. So ADHD now has BOTH a fill
   fingerprint (variance down / decorrelated, confirmed) and a behavioral face
   (scatter/hyperfocus), both from the one short clock.
2. **Autism unification test (the canalization chain) -- BLOCKED, needs a build
   first.** The four-link test (weak binding penalizes NOVELTY not just
   ambiguity -> the stamp fires less on novelty -> standing canalizes routine
   basins -> deep basins fail the reweighting probe) would decide whether autism
   is one root (weak binding) with two faces at two timescales: fast weak
   coherence + slow stamp-driven sameness. BUT it relies on standing/stamp/
   canalization dynamics (`Edot/E = r*q - mu`, the salience-stamp, emergent
   basins) that are **NOT in this build** -- grep finds none; the replaced
   `allocator_toy.py` never had them; they are the paper's "part two coalition
   layer," conceptual not coded. So this is NOT a no-risk measurement: it first
   needs the canalization layer ported into the instrument. Guards when built:
   keep NOVELTY distinct from AMBIGUITY (Link 1, the fragile one); confirm the
   fast wall still stands (with standing frozen, a binding lesion must STILL fail
   to produce rigidity -- if the fast contest fakes rigidity, the reward coupling
   leaked across the level separation); rigidity = lock-AND-fail-the-reweighting-
   probe, never H-pinned-high alone; basin depth must EMERGE from the stamp, not
   be hand-set.

## The recursive stack (multi-level): architecture + containment

> **REFRAME (the new regime).** The disorders are no longer located by depth.
> All four are breaks of the **top** contest (the two-axis table above):
> emergence-from-the-ground is ruled out, so nothing "lives in the basement."
> What the stack still earns: (1) it is the genuine **architecture** (one contest
> at each scale, evidence down / supply up, clocks lengthening upward — get the
> coupling exact, below); and (2) **containment** — a lesion injected *below* the
> world-facing top is absorbed (autism and ADHD applied at n-1 wash out by the
> top; their fingerprints appear only where the level reads the world directly).
> So a lower lesion is a *contained* version of a top lesion, not a different or
> deeper disorder. The old "bipolar as propagating severity / depth = severity"
> reading and "ADHD vs depth" wording below are **SUPERSEDED** by this; keep the
> coupling spec, read the severity/depth claims as containment only.

This wraps the single-level core above; it replaces none of it. The same contest
runs at several levels (`n`, `n-1`, `n-2`, bottom). The damping break (`kP -> 0`)
injected *below* the top either stays contained or, only if the intervening
levels are also weak, reaches the top — read this as **containment**, not a
severity axis that relocates the disorder. The disorders themselves are set at
the top.

### Coupling the levels (this is the architecture; get it exact)
Run the identical `step()` core at each level `N`. Not independent stacked
copies; each is coupled to its neighbours — supply from the level below,
evidence from the level above:
- **Supply from below.** `F_N` is the throughput of `N-1`, not a free scalar.
  Drive it from `N-1`'s output rate (its `pibar` / winning coalition's sustained
  output). Supply rises UP the stack.
- **Bar from below.** `theta_N`'s resting value tracks `N-1`'s sustainable
  output. Do **not** expose independent free `kP_N`, `kI_N` per level; the
  damping regulating `F_N` is how fast `N-1` re-settles, let it emerge from the
  coupling. (If the build gives each level its own `kP`, refactor so it's
  inherited from below.)
- **Evidence from ABOVE (feedback flows down).** Only the **top** reads external
  `y` (the world). `y_N` for every lower level is the winning `m` of the level
  *above* it — the top's pick propagates down as the target each level below
  tracks. Evidence/feedback flows DOWN; this is the opposite direction from
  supply, which rises up. (This reverses the earlier "evidence from below" /
  bottom-reads-world wording — that is VOID.)
- **Clocks lengthen upward.** Each level's time constants a fixed factor slower
  than the one below. Top = mood/global/slowest **and world-facing**, bottom =
  fast/local end-effector.
- **Top is the world-reader; bottom is the fast nucleus.** The world enters at
  the slow top; the bottom is the fastest local contest, driven by feedback from
  above and feeding its supply up. Do not recurse past the bottom.

### The break, and containment (severity, bipolar only)
Inject loss of fill damping (`kP -> 0`) as a lesion at a chosen level `N`. Watch
whether the oscillation is contained or propagates up.
- Break **low with intact levels above**: a well-damped, slower upper level
  low-passes the oscillating throughput from below, absorbing it. Fast, bounded,
  local, never reaches the top. **Contained** (mild / sub-clinical bipolar).
- Break **at/near the top**, or low **with upper levels also weakened**: reaches
  the slow global level, full sustained swing. **Propagated** (full bipolar).
- **Same break, depth = severity.** Identical Hopf fingerprint, fast/small when
  contained, slow/large when propagated. This is one disorder (bipolar) at
  different severities, NOT bipolar-vs-ADHD.

In the build: `kP` is per level, set on the currently viewed level (drill the
layer picker, drop `kP` there). Inject at the bottom with healthy levels above ->
contained; inject at the top -> propagated. A **break depth** readout (how many
levels show the oscillation) is the quantitative form of severity. The kI/kP
"emerge from below" ideal is approximated: damping is per-level `kP` but the
upward fill coupling plus the slower upper clocks supply the low-pass, so a
fast break from below is absorbed by the slow levels above.

### What this asserts, and what it does not (hold this line)
- **`delta` IS the bar's averaging clock** — one `tau` for the scoring horizon
  and the inter-level averaging window. (The earlier guard "keep delta separate,
  do not merge into the homeostat timescale" is VOID; this merge is by design.)
- **ADHD = short `delta`** (bar's clock), the sibling of bipolar (`kP`, damping).
  Do NOT frame ADHD as a contained fill oscillation; the containment demo is
  bipolar-only severity.
- **Do not wire the division pair into propagation.** Schizophrenia/autism
  aren't claimed to reduce by containment; the division is a current-level
  quantity. Leave them on the single-level controls (`G`, `phi`).

## Design decisions baked in (do not regress without being asked)

- **No presets.** The user explicitly removed all preset buttons. Do not add
  them back.
- **Randomness is "feast vs famine"** with +/− valence (the reproductive
  environment: surplus vs deficit), not a generic "randomness"/"stressor" knob.
- **Layers are a nested stack of contests**, not view-framings. The two flows
  cross in OPPOSITE directions: **evidence/feedback flows DOWN** (only the *top*
  reads the world; each level below tracks the level *above*'s `m` as its
  target), while **supply/throughput rises UP** (a level's fill `F` is disturbed
  by the fill of the level below it, so a break propagates upward). Each level is
  a live allocator contest with its OWN fill and per-level `kP` (the lesion
  site). Clocks lengthen upward (top slowest, and world-facing; bottom fast and
  local). The picker (level n / n-1 / n-2 / cellular) drills the panels into a
  level; `kP` is set on the viewed level. Headline is read at the TOP — the slow,
  world-facing level that collates the stack (division AND fill both read there).
  Do not revert to one shared fill, to bottom-reads-world, or to evidence rising
  up from below.
- **No hysteresis graphs** or non-core printouts. The user removed them as an
  obvious idea not worth a full readout.

## Discriminating Mechanism A from B (the A-vs-B protocol)

> **NOTE (new regime).** This protocol was run with the lesions injected at **n-1**
> as the test site, and its prose below still uses the old "x depth" framing.
> Under the new regime the disorders are **top-level** (see the board table). The
> A/B fingerprint dissociation is a **mechanism signature, level-independent** —
> it holds wherever the lesion sits — so these results stand; read "at n-1" here
> as the historical test location, not as where the disorder lives. (The clock
> control is now `tauW` short, the inverse of the old `clk > 1`.)

The four disorders were originally framed as two malfunctions x depth: division
collapse (`G` high) and fill break (`kP` -> 0), at the top (schizophrenia/bipolar)
or at n-1 (autism/ADHD). A separate hypothesis is that ADHD is a **short clock**
(`tauW` short / `clk` > 1, the level runs faster) rather than a `kP` break. These
two mechanisms BOTH raise variance, so variance cannot tell them apart. The
discriminating protocol (run it via a headless Node+Puppeteer harness on the
real sim, not a port):

- **A (lower damping):** ramp `levels[1].kP` 1 -> 0, all else healthy. Predict a
  Hopf at `omega0 = sqrt(kI*Fstar)` (x the level's clock); confirm by (i) peak
  frequency matching `omega0` and (ii) the peak NOT drifting when `dt` is halved.
- **B (short clock):** ramp `levels[1].clk` 1 -> high (the level reconfigures
  faster). This is a real lever with teeth (scales the whole reconfiguration
  clock); the yhat-smoothing horizon alone is inert.
- **Discriminators** (variance is deliberately NOT one), at n-1 AND the top:
  power-spectrum peak + sharpness, lag-1 autocorrelation, return time.

**Measured result (on record):** A and B cross-dissociate AT THE LESION SITE
(n-1): A drives fill variance UP, low-frequency, correlated, into a limit cycle;
B drives fill variance DOWN, high-frequency, decorrelated (ac1 -> 0). Distinct
mechanisms -- the sibling framing survives at the lesion. Calibrated sweep
(dt=0.005, omega0-band power at f0~0.076, return-time in tau_relax(n-1)=1.04
units): A `kP@n-1` 1->0.1 gives n-1 var 6.7e-3->1.2e-1, ac1 pinned ~0.97,
omega0-band 5.8k->246k, return-time 1.08->6.15t; B `clk@n-1` 1->8 gives n-1 var
6.8e-3->2.3e-4, ac1 0.977->0.316, omega0-band 6.5k->1.4, return-time 1.08->0.15t.
They never share a non-trivial operating point: the supposed confound (variance)
moves in OPPOSITE directions, so there is no "matched point" to disentangle --
the dissociation is total on every indicator from baseline outward.

**Containment is now a one-pole EMA, not a gate (this replaced the gate).** A
level reads the level below's fill through `read += (below.F - read)*dt/tau`,
with `tau` the reading level's OWN emergent horizon, and is disturbed by
`couple*(read - below.Fset)`. Containment is the EMA's frequency-dependent gain
`1/sqrt(1+(omega*tau)^2)` -- graded, never zero. The homeostat's own z-integral
stays exact (NOT leaky); only the inter-level read is an EMA. The `leak`
parameter is GONE. Consequence at the TOP (the headline): the EMA leakage now
makes the top DISCRIMINATE A from B, where the full-absorption gate could not.
As the n-1 lesion deepens, A leaks an attenuated slow Hopf peak up (top
omega0-band 11k->82k, top var 6.1e-3->9.8e-3) because the slow oscillation sits
inside the top's passband; B's fast decorrelated jitter is low-passed away (top
omega0-band ~8-10k flat, top var ~6.5e-3 flat). The headline LABEL stays healthy
for both (still contained -- the swing never trips the classifier), but the
top's SPECTRUM carries A's signature and not B's. Verdict: dissociation, now
legible at the headline as well as the lesion. (Autocorrelation: lag-1 suffices
here because B's fall is large, 0.977->0.316; a tau_relax-scaled lag is the
cleaner measure when the fall is subtle, to clear the ~0.98 healthy ceiling.)
Numerical caveat: the `kP=0` limit-cycle frequency matches `omega0` at
`dt=0.005` but is ~40% off at `dt=0.01` (Euler under-resolves the violent
relaxation cycle) -- frequencies are only quantitative at finer `dt`.

## Healthy control (calibration; run it before any A/B sweep)

The control does three jobs: define the model's time-unit (so thresholds are
ratios, not absolute-tick guesses), set the severity-zero anchor, and confirm
real rest. Measured results (on record), all in model-time:

- **Unit.** `tau_relax` (first 1/e crossing of an impulse to a level's fill) =
  top 1.28, n-1 1.04. Predicted Hopf period `2*pi/sqrt(kI*Fstar)` = 8.9
  intrinsic, 13.2 at n-1 (x its clock). So Hopf-period / tau_relax ~= 10-13;
  size FFT windows in Hopf-periods, burn-in in tau_relax.
- **Rest.** Horizon gradient 6.45 -> 5.2 -> 4.32 -> 3.6, volatility ~floor,
  fill ~F*. (Caveat: n-1 max-share can read ~0.88 at an instant -- check
  plurality sustained, not single-tick.)

**Three things the control proved the naive indicators get WRONG -- use these
corrected forms in the sweep:**
1. Healthy fill is NOT flat: it carries the slow world-tracking rhythm
   (f~0.0475), so the GLOBAL peak-to-floor ratio is ~3e5 even at rest. The
   peak test must be the power in the **omega0 band** specifically
   (f0 = sqrt(kI*Fstar)*clockRate(level)/2pi ~= 0.076 at n-1), not the global
   peak. (omega0-band power is clean: healthy ~13 -> A ~38.)
2. Healthy lag-1 autocorrelation is ~0.99 (the fill is smooth), not
   low-to-moderate. So A has ~no headroom to rise; **B's FALL below 0.99 is the
   live autocorrelation signal**, not A's rise.
3. Variance is non-stationary on a 1024 window (~2x between halves, from the
   slow rhythm), so variance-matching is unreliable -- use long windows and
   lean on ratio/normalized indicators (omega0-band ratio, ac1, return-time)
   rather than raw variance matching.

dt-halving at rest leaves ac1 stable (dt-robust at rest).

## Working conventions

- Keep `docs/index.html` ASCII-only. Check with `grep -lP '[^\x00-\x7f]'`.
- Syntax-check the script after edits (extract the `<script>` body and
  `node --check` it).
- Visual/behavioural verification is done with headless Chromium (Puppeteer),
  driving the sliders and reading `#regime` + the readout. Probe from a fresh
  load per regime and let it settle — chained transitions inherit transients,
  and the bipolar limit cycle takes ~12 s to build.
- This is a sandbox for mechanics, not a clinical claim. Keep copy honest.
</content>
