# Allocator Toy Model

A runnable, deliberately minimal demonstration of the mechanics in "One Allocator,
Two Kinds of Fault." This is a sandbox for the dynamics, not a claim that the
hypothesis is true. The point is to let someone turn the knobs and watch a malfunction
and a miscalibration behave differently for reasons you can see in one equation.

Everything lives in `allocator_toy.py`. It is pure Python standard library:
nothing to install, no numpy, no matplotlib. Start with
`python allocator_toy.py demo`.

## The one moving part

`g` is the allocator's net gain on relevance, a number in (0, 1).

    high g  =  the flooding arm        low g  =  the collapse arm

Both arms are two readings of one variable, not two faults. The whole model is one
update rule run with different knobs:

    dg_i/dt = ( -g_i + S( beta*(g_i - 0.5) + I - ka*(a - 0.5)
                          + c*(mean(g) - g_i) + noise_i ) ) / tau_g
    da/dt   = ( mean(g) - a ) / tau_a          # slow; only the oscillator uses it

`S` is the logistic squash. `i` indexes channels (1 by default; 12 for the
integration experiment).

## The knobs, and what each one is in the paper

    beta   self-reinforcement / loop gain.  The STABILITY setting.
           This is the master switch for the kind of fault. The recurrent term
           beta*(g-0.5) is positive feedback: high g raises the precision of the
           evidence that supports high g. Below beta=4 the loop has one resting
           state and slides; above beta=4 it folds into two resting states (the
           two arms) with an unstable threshold between them. beta=4 is the
           tipping point.
    I      external drive: stress, a salient input, a dopaminergic fluctuation.
    ka     strength of the slow variable a, "the bar": the level of relevance the
           regulator demands before it admits a bid. With a folded loop, ka>4 turns
           the system into a relaxation oscillator (the bar drifts up under the
           flood until it tips, then back down: the bipolar mechanism).
    c      integration coupling across channels: the single weighting laid over
           the whole contest. High c keeps the field one coherent thing; low c
           lets the channels fall into different basins (fragmentation).
    k      steepness of temporal discounting. The ADHD target.
    lam    flexibility: how fast gain tracks context volatility. The autism target.

Two ways to disturb the contest, and they are different knobs:
- MALFUNCTION = the loop loses stability. You raise `beta` past 4. The fault is
  dynamical; the output moves.
- MISCALIBRATION = the loop is fine (`beta` low) but a target is set oddly. You
  change `k` or `lam`. The fault is a fixed offset; the output holds still.

And the split within the malfunctions is which variable the positive feedback
destabilizes:
- the operating point, while the integrating coupling stays intact  -> oscillates,
  returns                                                            -> bipolar
- the integrating coupling itself                                    -> fragments,
  does not return                                                    -> schizophrenia

## The four conditions as presets

    preset          regime                              knobs              signature
    baseline        monostable                          beta=2             slides, recovers fast
    schizophrenia   folded loop, integration failed     beta=8, c=0.2      fragments, no return
    bipolar         folded loop, integration intact     beta=8, c=3, ka=6  slow coherent oscillation
    adhd            monostable, steep target            beta=2, k=0.95     two-armed over delay
    autism          monostable, stuck target            beta=2, lam=0.1    two-armed over volatility

## Run it

    python allocator_toy.py app                       # a browser UI with a slider for every knob
    python allocator_toy.py demo                      # the whole contrast, narrated
    python allocator_toy.py guide                     # how to use it, and every variable described
    python allocator_toy.py fp --beta 8               # stable fixed points (two arms appear past beta=4)

    python allocator_toy.py sweep --beta 8            # reversible drive sweep: hysteresis loop, area ~ 2.1
    python allocator_toy.py sweep --beta 2            # compare: paths retrace, area ~ 0
    python allocator_toy.py recover                   # critical slowing: recovery time vs beta

    python allocator_toy.py series --preset bipolar         # slow oscillation
    python allocator_toy.py series --preset schizophrenia   # sits in a basin, no stable middle
    python allocator_toy.py integration --preset bipolar        # coherent: one field
    python allocator_toy.py integration --preset schizophrenia  # fragmented: scattered basins

    python allocator_toy.py profile --preset adhd     # weight vs reward delay, two arms
    python allocator_toy.py profile --preset autism   # gain mismatch vs volatility, two arms

Any preset can be overridden: `--beta --c --ka --k --lam --adapt`. By default the
output is ASCII sparklines and heatmaps in the terminal. Add `--plot` to also write
self-contained SVG files to `out/` (any browser opens them; no libraries needed).

## Browser UI

The UI is `docs/index.html`: one self-contained page that runs the whole model in
the browser (a faithful JavaScript port of the update rule in `allocator_toy.py`),
with a slider for every knob, a preset menu, and a view switch (fixed points, sweep,
recover, series, integration, the two profiles). Drag a slider and the graph updates
live, in real time: the model recomputes once per animation frame as the knob moves,
redrawing the plot and the narration. No build step and no dependencies; each view
computes with only the knobs it uses, so the rest stay dimmed.

Three ways to open it:

- Just open `docs/index.html` in a browser (works straight from disk, `file://`).
- `python allocator_toy.py app` serves it on localhost (opens your browser, or pass
  `--no-browser` and visit the printed URL). This is only a static file server; the
  page does the computing.
- Host it on GitHub Pages (below).

## Run it online (GitHub Pages)

The page is fully static, so GitHub Pages can host it as-is. A workflow at
`.github/workflows/pages.yml` publishes the `docs/` folder automatically on every
push. To turn it on once: in the repository, go to Settings > Pages > Build and
deployment, and set Source to "GitHub Actions". After that, pushes to the default
branch redeploy the site.

There is no port and nothing to boot: Pages serves the files over HTTPS, and the
app runs entirely in the visitor's browser. The live URL opens straight into the
app -- the workflow publishes `docs/` as the site root, and a small redirect at the
repository root (`index.html`) forwards into the app as well, so the site lands on
it however Pages is configured (Actions, "Deploy from a branch" with `/docs`, or
with the repository root). The port-based version is the local `app` command above;
the hosted site needs none.

## What the model is demonstrating (and what you should see)

- One number, `beta`, sorts the kinds of fault. `fp` shows beta=2 has a single
  resting state at 0.5 (it slides) while beta=8 has two at about 0.02 and 0.98
  (it snaps between arms). Nothing else changed.
- Malfunction versus miscalibration shows up under a reversible sweep. At beta=8
  the drive-up and drive-down paths differ (hysteresis loop area about 2.1); at
  beta=2 they lie on top of each other (area ~ 0). The malfunction's state depends
  on where it has been; the miscalibration's does not.
- Approaching the fold, recovery from a nudge slows without bound. `recover` shows
  return time climbing from about 3 to over 160 time units, and the variance and
  lag-1 autocorrelation of the fluctuations both climbing (autocorrelation rising to
  1.00) as beta goes from 1 to 3.95. That is the critical-slowing signature, and it
  is measurable without watching the system switch. Critical slowing is a fold
  signature specifically: it belongs to bipolar disorder and to the onset of
  psychosis, not to the established, fragmented schizophrenic state (which is chaos,
  not a fold, and does not slow).
- The two malfunctions differ by which variable folds. `series --preset bipolar`
  is a slow recurrent oscillation; `integration --preset bipolar` keeps all channels
  synchronized (cross-channel spread ~ 0): one coherent field that returns each cycle.
  `integration --preset schizophrenia` lets the channels scatter into different basins
  (spread ~ 0.45) and stay there: no single field, no return. That fragmentation is
  the established schizophrenic state; its signature is the lost integration itself,
  not an approach to a tipping point.
- The miscalibrations never switch. `profile --preset adhd` is a fixed curve, weight
  piled on the immediate option and starved from the delayed one, both at once.
  `profile --preset autism` is a fixed mismatch that is positive (gain too high,
  flooding) in volatile contexts and negative (gain too low, collapse) in stable ones,
  both at once. Sweeping the environment moves the profile smoothly; there is no jump.

## Things to try

- Push `beta` from 3.9 to 4.1 in `recover` and watch the return time blow up. That
  is the tipping point the malfunction lives near.
- In `integration`, sweep `c` down from 3 and find where coherence collapses into
  fragmentation. That is the line between the bipolar-type and schizophrenia-type fault.
- Hand a miscalibration preset a malfunction loop: `integration --preset autism
  --beta 8 --c 0.2`. It fragments. The settings are independent, so one person can
  carry a miscalibrated target and an unstable loop at once; the model does not forbid
  comorbidity.
- Drop `ka` below 4 in the bipolar preset and the oscillation dies into a stuck basin:
  the slow variable is what makes a folded loop cycle rather than just snap.
- Raise the noise in `series` and the bistable system switches arms more often. With
  the slow variable on, the same noise rides on top of a clean oscillation.

## Files

    allocator_toy.py   the model and CLI: the update rule, the commands, ASCII
                       rendering, and a built-in SVG plotter. Pure Python standard
                       library; runs anywhere python does, no installs.
    docs/index.html    the browser UI: a self-contained page that runs the same
                       model client-side (a JS port of the update rule). What the
                       `app` command serves and what GitHub Pages hosts.
    .github/workflows/pages.yml   publishes docs/ to GitHub Pages on push.

The update rule lives in two places now, Python (the CLI, the reference) and the
JavaScript port inside docs/index.html (so it can run in a browser with nothing
installed). They are kept in step; change one, change the other.

## House rules if Claude Code edits this

- ASCII only. No em or en dashes, no curly quotes, no unicode math or block glyphs.
  Use straight quotes and the ASCII intensity ramp already in the file.
- Keep it a toy: one file, one update rule, readable over clever. If a change needs a
  second mechanism, ask whether the existing knob can do it first.
- Every knob stays mapped to a named setting in the paper (stability, integration,
  discount, flexibility). Do not add a parameter without saying which part of the
  hypothesis it stands for.
- The model demonstrates mechanics; it is not fitted to data and should not pretend to
  be. Keep claims in comments and output proportionate to that.
