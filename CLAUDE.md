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
