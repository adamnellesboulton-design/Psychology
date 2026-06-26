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

    beta   self-reinforcement / loop gain. The recurrent term beta*(g-0.5) is
           positive feedback: winning begets winning. It is the engine behind both
           bifurcations. With the homeostat off, beta>4 folds the loop into two
           basins; beta=4 is that fold.
    I      external drive: stress, a salient input, a dopaminergic fluctuation.
    ka     HOMEOSTAT strength. The homeostat sets the bar (the slow variable a:
           the level of relevance a bid must clear) and opposes the loop, so the
           effective gain is beta-ka. It keeps a single euthymic resting state
           rather than two basins, but past its HOPF that state loses its damping
           and the field orbits euthymia -- the bipolar swing.
    c      INTEGRATING gain / coupling across channels: the binding of the field
           into one coherent state. High c keeps the field one thing; low c lets
           the channels fall into different basins. Its FOLD is schizophrenia.
    k      steepness of temporal discounting. The ADHD target.
    lam    flexibility: how fast gain tracks context volatility. The autism target.

The allocator runs two slow controls, and the whole cut is that the two
malfunctions are each one of them crossing a different bifurcation:
- the INTEGRATING GAIN crosses a FOLD: two basins with a tipping point between,
  so a field that loses coherence tips into the captured basin and, across many
  channels, fragments and does not return -> schizophrenia.
- the HOMEOSTAT crosses a HOPF: euthymia is a single fixed point that loses its
  damping, so the field swings around it and back rather than resting -> bipolar.
  Because the centre survives, a euthymic baseline remains to return to, which a
  fold would not leave.
- MISCALIBRATION = both controls intact (`beta` low), a target (`k` or `lam`) set
  oddly: a fixed two-armed offset that never switches -> ADHD, autism.

The two bifurcations even slow differently as they near the edge, which says which
tip is coming: a fold slows monotonically, a Hopf rings, the wobble growing and
lengthening as the damping dies.

## The four conditions as presets

    preset          regime                              knobs              signature
    baseline        rests at euthymia                   beta=2             slides, recovers fast
    schizophrenia   integrating gain folds              beta=8, c=0.2      fragments, no return
    bipolar         homeostat crosses a Hopf            beta=8, c=3, ka=6  swings around euthymia
    adhd            both controls intact, steep target  beta=2, k=0.95     two-armed over delay
    autism          both controls intact, stuck target  beta=2, lam=0.1    two-armed over volatility

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
the browser (a faithful JavaScript port of the update rule in `allocator_toy.py`).
It is built around the five conditions: pick one and the page shows all of that
condition's graphs at once, each with a plain-language reading of what it means.
The captions talk in the model's own terms (flooding and collapse, swinging,
fragmenting, mania and depression) rather than the numbers, and each condition shows
the views that tell its story honestly -- a malfunction shows its dynamics, a
miscalibration leads with its fixed profile and shows the (normal) dynamics after as
contrast. Bipolar omits the hysteresis sweep on purpose, since that stickiness is the
fold's, not the Hopf's. A collapsed "Adjust the dials yourself" panel exposes a
slider for every knob for anyone who wants to drive the model by hand, and a "Show
the math" button opens the full update rule, the parameters, and the bifurcation
conditions (the fold at effective gain 4, the Hopf from the Jacobian trace). The
captions read plainly while the axes carry the symbols (g, I, beta, d, v, g*), so
legibility and precision sit side by side. No build step and no dependencies.

It stays snappy: the heavy loops are allocation-free, `recover` is computed once,
and each condition's dashboard is cached, so the first condition renders in about
a tenth of a second and every switch after is instant.

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

- `fp` reads the resting states off the effective gain (beta-ka). With the homeostat
  off, beta=2 has a single euthymic state (it slides) and beta=8 has folded into two
  basins at about 0.02 and 0.98 (schizophrenia). With the homeostat on (bipolar:
  beta=8, ka=6), the effective gain is 2, so there is a single euthymic state again
  -- but it has lost its damping, so the field orbits it (the Hopf).
- Malfunction versus miscalibration shows up under a reversible sweep. At beta=8
  the drive-up and drive-down paths differ (hysteresis loop area about 2.1); at
  beta=2 they lie on top of each other (area ~ 0). The malfunction's state depends
  on where it has been; the miscalibration's does not.
- Approaching either edge, recovery from a nudge slows -- the early warning,
  measurable before anything switches (`recover` shows return time climbing from
  about 4 to over 200). But the two malfunctions slow in different shapes, and the
  shape says which tip is coming: a fold (the integrating gain, the onset of
  psychosis) creeps back monotonically, while a Hopf (the homeostat, bipolar) rings,
  the wobble growing and lengthening as the damping dies. (The established,
  fragmented schizophrenic state is chaos rather than a fold, so it does not slow.)
- The two malfunctions differ by which control fails. `series --preset bipolar`
  swings around euthymia and back (the homeostat's Hopf); `integration --preset
  bipolar` keeps all channels synchronized (cross-channel spread ~ 0): one coherent
  field that returns each cycle. `integration --preset schizophrenia` lets the
  channels scatter into different basins (spread ~ 0.45) and stay: the integrating
  gain has folded, no single field, no return.
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
