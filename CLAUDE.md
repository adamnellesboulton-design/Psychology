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

## Design decisions baked in (do not regress without being asked)

- **No presets.** The user explicitly removed all preset buttons. Do not add
  them back.
- **Randomness is "feast vs famine"** with +/− valence (the reproductive
  environment: surplus vs deficit), not a generic "randomness"/"stressor" knob.
- **Layers are a nested stack of contests**, not view-framings. The model is a
  top-down stack: level n (top) tracks the world; each lower level (n-1 ...
  cellular) is its own live allocator contest chasing its parent's pick `m`. The
  four controls act at every scale (malfunctions cascade down). The top is the
  collated headline (classifier reads `levels[0]`); the picker (level n / n-1 /
  n-2 / cellular) drills the panels into a level. One shared fill `F`.
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
