# Allocator — one channel, four controls

A real-time, interactive instrument for one idea: a single self-organising
control loop, run with four knobs, produces recognisable psychiatric regimes
when a knob is driven out of range. Turn a control and watch a disorder fall
out of the dynamics — you can see *why*, not just *that*.

This is a sandbox for the mechanics, not a clinical claim. It is a way to feel
the difference between a **malfunction** (the loop's machinery breaks) and a
**miscalibration** (the machinery is fine but the dial is set wrong).

**Run it:** open `docs/index.html` in any browser. No build step, no
dependencies, no server — it runs from `file://` and from GitHub Pages alike.
Everything (model, rendering, UI) is one self-contained HTML file.

## What you are looking at

One **channel** carries a moving piece of evidence about the world, `y`. A set
of competing coalitions bid to explain it. Two things evolve:

- **Division `p`** — who is winning the channel and how dominant one coalition
  is (replicator dynamics on a probability simplex). The bar chart shows the
  coalitions; dominance `H` (the Herfindahl concentration index) is the order
  parameter.
- **Fill `F`** — how hard the system is competing overall, held near a target
  by a PI homeostat. The vertical gauge shows it against its euthymic band.

The **channel** view plots the coalition directions `u`, the world `y` (blue),
and the system's shared state `m` (amber) — its current best guess. Healthy
means `m` tracks `y`. The estimate carries a small per-tick wobble (`sigmaM`),
an irreducible epistemic uncertainty: the system is never perfectly sure where
things stand. The **traces** scroll `F`, `H` and the tracking error,
and the **readout** prints the order parameters plus rolling early-warning
signals (lag-1 autocorrelation and variance — the generic precursors of a fold
or a Hopf bifurcation).

A **regime label** at the top names the current state: *healthy*, *division
collapsed*, *fill oscillating*, *fill flooded/starved*, *division scattered*,
*tracking lost*.

## The four controls

Grouped into the two kinds of fault.

**Malfunctions** — the loop's integrity fails.

| Control | Healthy | Driven out of range |
|---|---|---|
| **Integrating gain `G`** | 1.0 | High → the winner freezes and decouples from the world (delusional fixity, the *schizophrenia* collapse). Low → the winner wanders (disorganised). |
| **Homeostat damping `kP`** | 1.0 | → 0 the fill loses its damping and swings between flood and starvation (the *bipolar* limit cycle). |

**Miscalibrations** — the machinery is intact, the dial is wrong.

| Control | Healthy | Driven out of range |
|---|---|---|
| **Averaging clock `δ`** | 0.6 | The bar's clock — the horizon a level scores evidence over and averages its target across. Too short → chases the instant, never holds a thread (*ADHD*). Sibling of `kP`: the two faults of the one homeostat (clock vs damping). |
| **Precision flexibility `φ`** | 1.0 | → 0 precision freezes; the system is slow to re-weight after a context shift (*autism*). |

The two malfunctions produce **gross, named state changes** you can read off the
label (collapse, oscillation). The two miscalibrations are **subtler by
design** — they change *how* the system tracks (it churns, or it is rigid after
a shift) rather than throwing it into a collapsed state. That is clinically
honest: ADHD and autism are not states of gross system failure. Watch them in
the live division view, the traces and the early-warning numbers, and use
**context shift (jump y)** to provoke the autism rigidity.

## Feast and famine

The **environment** control sets the fitness landscape the fill competes in:

- **feast (+)** — a reproductive surplus; the fill's target rises and the
  system floods.
- **famine (−)** — a deficit; the target falls and the system starves.
- **neutral (0)** — the homeostat's own target.

A small amount of randomness rides on the fill at all times (an always-on
environmental wobble), so the system is never perfectly quiet.

**Mood** reads as the fill level along this axis: toward feast is elevated
(manic), toward famine is low (depressed). The bipolar limit cycle is exactly
this level swinging between the two poles.

## Layers (the nested stack)

The model is not one contest but a **stack of nested allocator contests**, one
per scale: level _n_ at the top, then _n−1_, down to the **cellular** nucleus at
the bottom. The two flows cross in **opposite directions**. Evidence/feedback
flows **down**: only the **top** reads the external world, and its pick `m`
propagates down as the target every level below tracks. Supply/throughput rises
**up**: each level's fill `F` is disturbed by the fill of the level below it, so
a break travels upward. **Clocks lengthen upward** — the bottom is fast and
local (a quick end-effector), the top is slow, global (mood), and world-facing.
Each level has its **own fill** with its own damping `kP`.

The layer picker (level n / n−1 / n−2 / cellular) drills the panels into any
level; `kP` is set on whichever level you're viewing.

### Bipolar as propagating severity

Bipolar and ADHD are the two faults of the one fill homeostat — **`kP` is its
damping, `delta` is its averaging clock** — siblings, not the same break. The
multi-level stack adds a **severity** axis to *bipolar*: drop a level's fill
damping (`kP → 0`) and watch how far it spreads.

- **At the bottom, levels above intact** → the slower, well-damped upper levels
  low-pass the fast oscillation and absorb it. **Contained**: local, never
  reaches the top. The headline stays healthy; drill to the bottom to see it
  swing.
- **At the top** (or low with the upper levels also weakened) → it reaches the
  slow global level: a full, slow mood swing. **Propagated**: the headline reads
  *fill oscillating* (full bipolar).

Same Hopf, contained or propagated by depth. The **break depth** readout (how
many levels are oscillating) is the quantitative form of severity. This is one
disorder at different severities, *not* bipolar-vs-ADHD. ADHD stays the clock
fault (`delta` short); the division pair (schizophrenia/autism) is separate,
read at the top, where the contest faces the world.

## Notes

- Canvas 2D, vanilla JS, `requestAnimationFrame`. Device-pixel-ratio aware,
  capped at 2×. No framework.
- All model parameters and classifier thresholds live in one `CONFIG` block at
  the top of the script, so the dynamics are easy to retune in one place.
- `docs/` is what GitHub Pages publishes (see `.github/workflows/pages.yml`).
  The root `index.html` just redirects into it.
</content>
