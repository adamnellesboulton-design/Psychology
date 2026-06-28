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
- **Evidence** — a slow Lissajous wander at radius `yR`; `delta` sets the
  discount horizon `tau` over which `yhat` smooths it.

### The four controls → regimes

| Control | Group | Out-of-range regime |
|---|---|---|
| `G` integrating gain | malfunction | high → division collapses (frozen monopoly); low → disorganised |
| `kP` homeostat damping | malfunction | → 0 → fill oscillates (limit cycle) |
| `delta` discount rate | miscalibration | short → chases noise (ADHD) — subtle, trace-level |
| `phi` precision flexibility | miscalibration | → 0 → rigid after a context shift (autism) — subtle, trace-level |

Plus the environment: `env` > 0 floods, `env` < 0 starves.

Note (multi-level): this table and the malfunction/miscalibration split are the
single-level view. The recursion section below reexamines the fill pair, bipolar
and ADHD, as one break at two depths, contained versus propagated, rather than
two separate controls. Keep both views runnable so they can be compared; in
particular keep the discount-rate control and the existing ADHD preset. The
division pair, schizophrenia and autism, is not reframed this way.

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

## The recursive stack (multi-level), and breaks as propagation

This wraps the single-level core above; it replaces none of it. The same contest
runs at several levels (`n`, `n-1`, `n-2`, bottom). Couple them as the recursion
requires, then add one perturbation that demonstrates the central clinical
claim: the fill-disorders are one break at different depths, not separate
controls.

### Coupling the levels (this is the architecture; get it exact)
Run the identical `step()` core at each level `N`. Not independent stacked
copies; each reads the one beneath:
- **Supply from below.** `F_N` is the throughput of `N-1`, not a free scalar.
  Drive it from `N-1`'s output rate (its `pibar` / winning coalition's sustained
  output).
- **Bar from below.** `theta_N`'s resting value tracks `N-1`'s sustainable
  output. Do **not** expose independent free `kP_N`, `kI_N` per level; the
  damping regulating `F_N` is how fast `N-1` re-settles, let it emerge from the
  coupling. (If the build gives each level its own `kP`, refactor so it's
  inherited from below.)
- **Evidence from below.** `y_N` is the winning `m` of `N-1`. Only the bottom
  reads external `y`.
- **Clocks lengthen upward.** Each level's time constants a fixed factor slower
  than the one below. Top = mood/global/slowest, bottom = fast/local.
- **Bottom is the nucleus.** Lowest level where the bar comes alive; below it a
  fixed sieve, do not recurse past it.

### The break, and containment (the new demonstration)
Inject loss of fill damping (`kP -> 0`) as a lesion at a chosen level `N`. Watch
whether the oscillation is contained or propagates up.
- Break **low with intact levels above**: a well-damped upper level low-passes
  the oscillating throughput from below, absorbing it. Fast, bounded, local,
  never reaches the top. **Contained** (ADHD-like).
- Break **at/near the top**, or low **with upper levels also weakened**: reaches
  the slow global level, full sustained swing. **Propagated** (bipolar-like).
- **Same break.** Identical Hopf fingerprint (rising variance, dominant
  frequency, critical slowing), fast/small when contained, slow/large when
  propagated. Show it at the injected level **and** the top, side by side.

In the build: `kP` is per level, set on the currently viewed level (drill the
layer picker, drop `kP` there). Inject at the bottom with healthy levels above ->
contained; inject at the top -> propagated. A **break depth** readout (how many
levels show the oscillation) is the quantitative form of severity. The kI/kP
"emerge from below" ideal is approximated: damping is per-level `kP` but the
upward fill coupling plus the slower upper clocks supply the low-pass, so a
fast break from below is absorbed by the slow levels above.

### What this asserts, and what it does not (hold this line)
- **Keep `delta`.** Discount/horizon stays as in the core. Do not delete it,
  merge it into the homeostat timescale, or drop the control count.
- **Keep the four-control table.** `ADHD = short delta` stays. The multi-level
  mode lets you **compare** it against "ADHD as contained fill oscillation," not
  replace it.
- **Do not wire the division pair into propagation.** Schizophrenia/autism
  aren't claimed to reduce by containment; the division is a current-level
  quantity. Leave them on the single-level controls.

## Design decisions baked in (do not regress without being asked)

- **No presets.** The user explicitly removed all preset buttons. Do not add
  them back.
- **Randomness is "feast vs famine"** with +/− valence (the reproductive
  environment: surplus vs deficit), not a generic "randomness"/"stressor" knob.
- **Layers are a nested stack of contests**, not view-framings. The model is a
  BOTTOM-UP stack: only the bottom nucleus reads the world; each level above
  reads the level below (its `m` as evidence, its fill `F` as a disturbance).
  Each level is a live allocator contest with its OWN fill and per-level `kP`
  (the lesion site). Clocks lengthen upward (top slowest). The picker (level n /
  n-1 / n-2 / cellular) drills the panels into a level; `kP` is set on the viewed
  level. Headline reads division at the bottom, fill at the top (see recursion
  section). Do not revert to one shared fill or a top-down evidence flow.
- **No hysteresis graphs** or non-core printouts. The user removed them as an
  obvious idea not worth a full readout.

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
