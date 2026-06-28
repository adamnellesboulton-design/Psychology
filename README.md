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
| **Discount rate `δ`** | 0.6 | Too short → the horizon chases the instant and never holds a thread (*ADHD*). |
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

## Layers

The layer picker reframes the same running model at four levels:

- **1 — contest:** the literal channel. Coalitions bid; `p` says who wins, `F`
  how hard.
- **2 — coalition:** read the division as mass condensing onto a coalition.
- **3 — fit:** what the winner is answering to — the tracking of the world.
- **last (all):** everything merged.

## Notes

- Canvas 2D, vanilla JS, `requestAnimationFrame`. Device-pixel-ratio aware,
  capped at 2×. No framework.
- All model parameters and classifier thresholds live in one `CONFIG` block at
  the top of the script, so the dynamics are easy to retune in one place.
- `docs/` is what GitHub Pages publishes (see `.github/workflows/pages.yml`).
  The root `index.html` just redirects into it.
</content>
