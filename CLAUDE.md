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
- **Precision `rho`** — outer loop, relaxes toward an evidence-fit target at
  rate `phi`.
- **Evidence** — a slow Lissajous wander at radius `yR`; `delta` sets the bar's
  averaging clock `tau` (`tau = tauMin + (tauMax-tauMin)*delta`). One time
  constant, two jobs: the scoring/evidence horizon over which `yhat` smooths the
  target, AND, in the multi-level build, the window over which a level averages
  the one below. Short `tau` chases the instant (ADHD). `delta` is the bar's
  clock; `kP` is its damping — bipolar and ADHD are the two faults of the one
  homeostat (siblings, not the same break).

### The four controls → regimes

| Control | Group | Out-of-range regime |
|---|---|---|
| `G` integrating gain | malfunction | high → division collapses (frozen monopoly); low → disorganised |
| `kP` homeostat damping | malfunction | → 0 → fill oscillates (limit cycle) |
| `delta` bar's averaging clock | miscalibration | short → chases noise (ADHD); governs scoring horizon + bar memory — subtle, trace-level |
| `phi` precision flexibility | miscalibration | → 0 → rigid after a context shift (autism) — subtle, trace-level |

Plus the environment: `env` > 0 floods, `env` < 0 starves.

Note (the one homeostat): bipolar and ADHD are the two faults of the single fill
homeostat — `kP` is its damping, `delta` is its averaging clock. Siblings, not
the same break. The multi-level recursion section below is a **bipolar-only**
demonstration: it shows the damping break (`kP -> 0`) propagating up the levels,
contained versus propagated, as a *severity* axis. It is NOT the ADHD mechanism
(do not frame ADHD as a contained fill oscillation). ADHD stays the clock fault
(`delta` short, preset `delta = 0.08`). The division pair, schizophrenia and
autism, is separate again (`G`, `phi`).

### Classifier

`classify(d, P)` is a priority cascade on windowed diagnostics: collapse (`H` >
`H_collapse`) → oscillation (`ampF` > `amp_osc`) → scatter (`H` < `H_scatter`) →
tracking lost (`err` > `errLost`) → flooded/starved (`|F − Fstar|` > `band`) →
healthy. Diagnostics are **windowed means/amplitudes**, not instantaneous values
— the instantaneous signals are noisy enough to make a label flicker.

Known and intended: the two malfunctions produce clean, named state labels; the
two miscalibrations (ADHD, autism) and low-`G` disorganised are subtle and read
as "healthy" on the gross label by design — they live in the division view,
traces and EWS numbers, not in a collapsed state. Do not fake a label for them.

In the built multi-level model the classifier reads the parts that matter for
each regime: division (collapse/scatter/tracking) at the fast bottom nucleus
(division is a current-level quantity), fill (oscillation/flood/starve) at the
slow top, where a break only registers once it has propagated up.

## The recursive stack (multi-level): bipolar as propagating severity

This wraps the single-level core above; it replaces none of it. The same contest
runs at several levels (`n`, `n-1`, `n-2`, bottom). It is a **bipolar-only**
demonstration: the damping break (`kP -> 0`) injected at a level either stays
contained or propagates up the stack — a *severity* axis. This is NOT the ADHD
mechanism. ADHD is the bar's clock fault (`delta` short) and is not reframed by
depth.

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

The four disorders are two malfunctions x depth: division collapse (`G` high) and
fill break (`kP` -> 0), at the top (schizophrenia/bipolar) or at n-1
(autism/ADHD). A separate hypothesis is that ADHD is a **short clock** at n-1
(`clk` > 1, the level runs faster) rather than a `kP` break. These two
mechanisms BOTH raise variance, so variance cannot tell them apart. The
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
