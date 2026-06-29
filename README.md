# Allocator — one channel, four controls

A real-time, interactive instrument for one idea: a single self-organising
control loop produces recognisable psychiatric regimes when a control is driven
out of range. Turn a control and watch a disorder fall out of the dynamics — you
can see *why*, not just *that*.

This is a sandbox for the mechanics, not a clinical claim. It is a way to feel
the difference between a **malfunction** (the loop's machinery breaks) and a
**miscalibration** (the machinery is fine but the dial is set wrong).

**Run it:** open `docs/index.html` in any browser. No build step, no
dependencies, no server — it runs from `file://` and from GitHub Pages alike.
Everything (model, rendering, UI) is one self-contained HTML file.

## What you are looking at

One **channel** carries a moving piece of evidence about the world, `y`. A set
of competing coalitions bid to explain it. Two things evolve at every level of
the stack:

- **Division `p`** — who is winning the channel and how dominant one coalition
  is (replicator dynamics on a probability simplex). Dominance `H` (the
  Herfindahl concentration index) is the order parameter.
- **Fill `F`** — how hard the system is competing overall, held near a target by
  a PI homeostat.

The display is **just the lines**: four stacked trace graphs for the viewed
level, each on its own fixed axis —

- **fill `F`** (the homeostat, green),
- **dominance `H`** (concentration, amber),
- **tracking error** (how far the system's shared state `m` is from its target,
  cyan), and
- **averaging horizon** (the level's emergent clock, violet).

A **readout** beside them prints the order parameters, the break/freeze
propagation, and rolling early-warning signals (lag-1 autocorrelation and
variance — the generic precursors of a fold or a Hopf bifurcation). A **regime
label** at the top names the current state: *healthy*, *division collapsed*,
*fill oscillating*, *fill flooded/starved*, *division scattered*, *tracking
lost*. The estimate `m` carries a small **low-passed** epistemic wobble
(`sigmaM`, an Ornstein–Uhlenbeck drift): the system is never perfectly sure where
things stand, and that uncertainty meanders rather than buzzing.

## The four controls

All four disorders are breaks of the **top** (world-facing) contest — **two
axes, each broken two ways**. There is no "deeper" disorder hidden in the stack;
the controls are set on the top. The gross/subtle split lives *within* each axis:
the violent break trips a named state, the milder break is **trace-level** (the
headline still reads "healthy", but the fingerprint is plain in the lines).

**Division — binding gain `G`** (healthy 1.0)

| Driven | Effect |
|---|---|
| **High** | the winner freezes into a self-confirming monopoly, decoupled from the world — the *schizophrenia* collapse (gross). |
| **Low** | weak binding: the contest cannot concentrate, many weak coalitions, no integrated whole — *autism*'s **weak central coherence** (trace-level: dominance `H` sags and churns; faint under clear input, pronounced under an *ambiguous* field, which is precisely when binding is needed). |

**Fill — the one homeostat, two sibling faults** (both healthy 1.0)

| Control | Driven | Effect |
|---|---|---|
| **Damping `kP`** | → its floor | the fill loses its damping and swings in a bounded limit cycle — *bipolar* (gross). (The floor is a small positive value: exactly 0 is undamped and blows up rather than settling.) |
| **Averaging clock `tauW`** | short | the level forgets fast, the fill hugs its setpoint with fast, decorrelated jitter — *ADHD* (trace-level). Its fingerprint is the **opposite** of bipolar's: variance **down** (~35×), autocorrelation **down**, no rhythmic peak. With a strong winner it holds (hyperfocus); with a weak/ambiguous one it can't keep a thread (scatter) — the two faces of one short clock. |

Plus the **environment** (see below). The two fill faults are siblings on one
homeostat: `kP` is its damping, `tauW` its averaging clock. They cross-dissociate
cleanly — bipolar drives fill variance up / correlated / into a slow swing; ADHD
drives it down / decorrelated / broadband. The division axis is `G` alone (high
vs low); there is no separate "precision flexibility" control (it was tested and
found not to be separable from `G`).

### A note on autism (an honest, two-part claim)

The instrument captures autism's **weak-central-coherence** face — it is low /
context-frozen binding on the `G` axis, a real-time deficit of integration. It
deliberately does **not** reduce autism's **insistence-on-sameness / rigidity**
face to the same control, and that is a *result*, not a gap: the model's winner
always tracks the world through an unconditional world-coupling term, so no
binding lesion can make it fail to update. The model therefore predicts that
autism's two faces are **structurally distinct mechanisms** — weak central
coherence a deficit of integration (this fast contest), insistence on sameness a
gating of world-coupling that plausibly lives at a slower, learned,
developmental-basin level — which co-occur in a person because both are affected,
not because they are one thing. (A separate "precision flexibility" control was
tested and found not to be separable from `G`; it is not on the board.)

## Environment: chaos and feast/famine

- **Chaos** is the environment's **volatility** — a global multiplier on the
  always-on external noise (on the fill and on the world reading). 1× is the
  calibrated baseline; turn it up to stress a regime's stability. (The system is
  strongly homeostatic: chaos roughens the traces and stresses a lesioned level
  far more than a healthy one.)
- **Feast / famine `env`** is the reproductive **tilt** on that environment —
  the surplus/deficit the noisy environment leans toward. It applies per level
  and is proportional to the population already enrolled. **Mood** reads as the
  fill level along this axis: feast (+) lifts it (manic), famine (−) lowers it
  (depressed), 0 is neutral. The bipolar limit cycle is exactly this level
  swinging between the two poles.

## Layers (the nested stack)

The model is not one contest but a **stack of nested allocator contests**, one
per scale: level _n_ at the top, then _n−1_, down to the **cellular** nucleus at
the bottom. The two flows cross in **opposite directions**. Evidence/feedback
flows **down**: only the **top** reads the external world, and its pick `m`
propagates down as the target every level below tracks. Supply/throughput rises
**up**: each level's fill `F` is disturbed (through a one-pole low-pass read) by
the fill of the level below it, so a break travels upward. **Clocks lengthen
upward** — the bottom is fast and local (a quick end-effector), the top is slow,
global (mood), and world-facing. Each level carries its **own** division and
fill, with its own `G`, `kP` and `tauW`.

The layer picker (level n / n−1 / n−2 / cellular) drills the traces into any
level; the per-level controls are set on whichever level you are viewing.

The disorders themselves are breaks of the **top** — the world-facing level
where the contest meets the world. The stack is the architecture, not a place
where disorders hide: a lesion injected *below* the top is **contained** — the
slower, well-damped upper levels low-pass it, so by the top it has washed out
(drill down to see it swing locally). A lower lesion is therefore a *contained*
version of a top break, not a separate or deeper disorder. (This retires an
earlier "depth = severity" framing: the disorders live at the top, and the depth
axis only buys containment.)

## Notes

- Canvas 2D, vanilla JS, `requestAnimationFrame`. Device-pixel-ratio aware,
  capped at 2×. No framework.
- All model parameters and classifier thresholds live in one `CONFIG` block at
  the top of the script, so the dynamics are easy to retune in one place.
- `docs/` is what GitHub Pages publishes (see `.github/workflows/pages.yml`).
  The root `index.html` just redirects into it.
- `CLAUDE.md` is the model's working notebook — the per-control mechanics, the
  A-vs-B discrimination protocol, the healthy-control calibration, and the
  recorded results (including what the model refused to capture, and why).
</content>
