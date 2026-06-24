"""
Allocator Toy Model
===================

A runnable, deliberately minimal demonstration of the mechanics in
"One Allocator, Two Kinds of Fault." A sandbox for the dynamics, not a claim
that the hypothesis is true. See README.md for the full tour; this header keeps
only the one equation and the rules for editing it.

The one moving part is g, the allocator's net gain on relevance, in (0, 1).
high g = the flooding arm; low g = the collapse arm. Both arms are two readings
of one variable. The whole model is one update rule run with different knobs:

    dg_i/dt = ( -g_i + S( beta*(g_i - 0.5) + I - ka*(a - 0.5)
                          + c*(mean(g) - g_i) + noise_i ) ) / tau_g
    da/dt   = ( mean(g) - a ) / tau_a          # slow; only the oscillator uses it

S is the logistic squash; i indexes channels (1 by default, 12 for integration).
The knobs map to named settings in the paper (see the Params class and README):
beta = stability (loop gain; beta=4 is the fold), I = external drive,
ka = strength of the slow adaptation, c = integration coupling across channels,
k = discount steepness (ADHD target), lam = flexibility (autism target).

MALFUNCTION = the loop loses stability (raise beta past 4); the output moves.
MISCALIBRATION = the loop is fine (beta low) but a target (k or lam) is set odd;
the output holds a fixed offset. Within the malfunctions, the positive feedback
destabilizes either the operating point (integration intact) -> oscillates,
returns -> bipolar, or the integrating coupling itself -> fragments, no return
-> schizophrenia.

House rules if Claude Code edits this:
- ASCII only. No em or en dashes, no curly quotes, no unicode math or block
  glyphs. Use straight quotes and the ASCII intensity ramp in RAMP.
- Keep it a toy: one file, one update rule, readable over clever. If a change
  needs a second mechanism, ask whether the existing knob can do it first.
- Every knob stays mapped to a named setting in the paper (stability,
  integration, discount, flexibility). Do not add a parameter without saying
  which part of the hypothesis it stands for.
- The model demonstrates mechanics; it is not fitted to data and should not
  pretend to be. Keep claims in comments and output proportionate to that.
"""

import argparse

import numpy as np

# ASCII intensity ramp, low to high. Used for every sparkline and heatmap so
# the toy runs in a bare terminal with no plotting library.
RAMP = " .:-=+*#%@"


# ----------------------------------------------------------------------------
# The one update rule
# ----------------------------------------------------------------------------

def S(x):
    """Logistic squash. Slope at the center is 0.25, which is why beta=4 is
    the fold: beta * 0.25 = 1 is the gain at which one resting state splits."""
    return 1.0 / (1.0 + np.exp(-x))


class Params:
    """The knobs. Each maps to a named setting in the paper (see module docs)."""

    def __init__(self, beta=2.0, I=0.0, ka=0.0, c=1.0, k=0.2, lam=1.0,
                 adapt=True, noise=0.0, tau_g=1.0, tau_a=40.0, dt=0.05, seed=0):
        self.beta = beta      # stability setting (loop gain)
        self.I = I            # external drive
        self.ka = ka          # strength of slow adaptation
        self.c = c            # integration coupling across channels
        self.k = k            # discount steepness (ADHD target; profile only)
        self.lam = lam        # flexibility (autism target; profile only)
        self.adapt = adapt    # engage the slow variable a
        self.noise = noise    # noise amplitude inside the squash
        self.tau_g = tau_g    # fast timescale (the contest)
        self.tau_a = tau_a    # slow timescale (the adaptation)
        self.dt = dt
        self.seed = seed


def simulate(p, T, n=1, drive=None, g0=None, a0=0.5, rng=None):
    """Integrate the update rule for time T with n channels.

    Returns (t, g, a) where g has shape (steps, n) and a has shape (steps,).
    drive, if given, is a function of time returning the external drive I;
    otherwise the constant p.I is used.
    """
    steps = int(round(T / p.dt))
    if rng is None:
        rng = np.random.default_rng(p.seed)
    if g0 is None:
        g = np.full(n, 0.5)
    else:
        g = np.array(g0, dtype=float) * np.ones(n)
    a = float(a0)

    out_g = np.zeros((steps, n))
    out_a = np.zeros(steps)
    t = np.arange(steps) * p.dt

    for s in range(steps):
        now = s * p.dt
        drv = p.I if drive is None else drive(now)
        mean_g = g.mean()
        coupling = p.c * (mean_g - g)
        if p.noise > 0.0:
            noise = p.noise * rng.standard_normal(n)
        else:
            noise = 0.0
        x = p.beta * (g - 0.5) + drv - p.ka * (a - 0.5) + coupling + noise
        g = g + p.dt * (-g + S(x)) / p.tau_g
        if p.adapt:
            a = a + p.dt * (mean_g - a) / p.tau_a
        out_g[s] = g
        out_a[s] = a

    return t, out_g, out_a


def settle(p, drive_value, g0, a0=0.5, T=80.0):
    """Run a single channel to its resting state under a constant drive and
    return the final g. Used by the quasi-static sweep and the profiles."""
    q = Params(beta=p.beta, I=drive_value, ka=p.ka, c=p.c, adapt=p.adapt,
               noise=0.0, tau_g=p.tau_g, tau_a=p.tau_a, dt=p.dt)
    _, g, _ = simulate(q, T, n=1, g0=g0, a0=a0)
    return g[-1, 0]


# ----------------------------------------------------------------------------
# Fixed points of the single-channel loop
# ----------------------------------------------------------------------------

def fixed_points(beta, drive=0.0):
    """Resting states of dg/dt = (-g + S(beta*(g-0.5) + drive))/tau_g.

    Returns a list of (g, stable) pairs. Below beta=4 there is one; above it
    there are three (two stable arms and an unstable threshold between)."""
    grid = np.linspace(1e-4, 1 - 1e-4, 4000)
    h = S(beta * (grid - 0.5) + drive) - grid
    roots = []
    for i in range(len(grid) - 1):
        if h[i] == 0.0 or h[i] * h[i + 1] < 0.0:
            lo, hi = grid[i], grid[i + 1]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                hm = S(beta * (mid - 0.5) + drive) - mid
                if (S(beta * (lo - 0.5) + drive) - lo) * hm <= 0.0:
                    hi = mid
                else:
                    lo = mid
            g = 0.5 * (lo + hi)
            # Stable when the RHS slope is negative: -1 + beta*S'(.) < 0.
            sx = S(beta * (g - 0.5) + drive)
            slope = -1.0 + beta * sx * (1.0 - sx)
            roots.append((g, slope < 0.0))
    # Deduplicate near-identical roots.
    out = []
    for g, st in roots:
        if not any(abs(g - g2) < 1e-3 for g2, _ in out):
            out.append((g, st))
    return out


# ----------------------------------------------------------------------------
# ASCII rendering (matplotlib is optional)
# ----------------------------------------------------------------------------

def sparkline(values, lo=None, hi=None):
    """One-line ASCII sparkline using the intensity ramp."""
    v = np.asarray(values, dtype=float)
    if lo is None:
        lo = float(v.min())
    if hi is None:
        hi = float(v.max())
    if hi - lo < 1e-12:
        hi = lo + 1e-12
    idx = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    idx = np.round(idx * (len(RAMP) - 1)).astype(int)
    return "".join(RAMP[i] for i in idx)


def heatmap(matrix, lo=0.0, hi=1.0):
    """ASCII heatmap. Rows are channels, columns are time samples."""
    m = np.asarray(matrix, dtype=float)
    idx = np.clip((m - lo) / (hi - lo), 0.0, 1.0)
    idx = np.round(idx * (len(RAMP) - 1)).astype(int)
    lines = []
    for row in idx:
        lines.append("|" + "".join(RAMP[i] for i in row) + "|")
    return "\n".join(lines)


def downsample(arr, width):
    """Pick `width` evenly spaced samples from a 1D or 2D (time-major) array."""
    arr = np.asarray(arr)
    n = arr.shape[0]
    if n <= width:
        return arr
    idx = np.linspace(0, n - 1, width).astype(int)
    return arr[idx]


def have_matplotlib():
    try:
        import matplotlib  # noqa: F401
        return True
    except Exception:
        return False


def maybe_plot(args):
    """True if the user asked for plots and matplotlib is available. Otherwise
    the ASCII output already printed stands on its own."""
    if not getattr(args, "plot", False):
        return False
    if not have_matplotlib():
        print("  (--plot: matplotlib not installed; showing ASCII only)")
        return False
    return True


def save_plot(fig, name):
    import os
    os.makedirs("out", exist_ok=True)
    path = "out/" + name
    fig.savefig(path, dpi=110, bbox_inches="tight")
    print("saved " + path)


# ----------------------------------------------------------------------------
# Presets: the four conditions plus baseline
# ----------------------------------------------------------------------------
#
#   preset          regime                            knobs              signature
#   baseline        monostable                        beta=2             slides, recovers
#   schizophrenia   folded loop, integration failed   beta=8, c=0.2      fragments, no return
#   bipolar         folded loop, integration intact   beta=8, c=3, ka=6  slow oscillation
#   adhd            monostable, steep target          beta=2, k=0.95     two-armed over delay
#   autism          monostable, stuck target          beta=2, lam=0.1    two-armed over volatility

PRESETS = {
    "baseline":      dict(beta=2.0),
    "schizophrenia": dict(beta=8.0, c=0.2, ka=0.0),
    "bipolar":       dict(beta=8.0, c=3.0, ka=6.0),
    "adhd":          dict(beta=2.0, k=0.95),
    "autism":        dict(beta=2.0, lam=0.1),
}


def resolve_params(args):
    """Start from defaults, lay the preset over them, then apply any explicit
    command-line overrides (only flags the user actually passed)."""
    p = Params()
    if getattr(args, "preset", None):
        for key, val in PRESETS[args.preset].items():
            setattr(p, key, val)
    for key in ("beta", "I", "ka", "c", "k", "lam", "noise", "seed", "dt"):
        val = getattr(args, key, None)
        if val is not None:
            setattr(p, key, val)
    if getattr(args, "adapt", None) is not None:
        p.adapt = bool(args.adapt)
    return p


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_fp(args):
    """Stable fixed points. Two arms appear past beta=4."""
    p = resolve_params(args)
    fps = fixed_points(p.beta)
    print("fixed points of the single-channel loop, beta = %.3g" % p.beta)
    print("  (beta=4 is the fold; below it one resting state, above it two)")
    for g, stable in fps:
        kind = "stable  " if stable else "unstable"
        arm = ""
        if stable and g > 0.6:
            arm = "  <- flooding arm"
        elif stable and g < 0.4:
            arm = "  <- collapse arm"
        print("  g* = %.4f   %s%s" % (g, kind, arm))
    n_stable = sum(1 for _, s in fps if s)
    if n_stable >= 2:
        print("two arms: the loop has folded.")
    else:
        print("one resting state at 0.5: the loop slides, it does not snap.")

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        g = np.linspace(0, 1, 400)
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(g, S(p.beta * (g - 0.5)), label="S(beta*(g-0.5))")
        ax.plot(g, g, "k--", lw=0.8, label="g")
        for gx, stable in fps:
            ax.plot(gx, gx, "o", color="C2" if stable else "C3")
        ax.set_xlabel("g"); ax.set_ylabel("update")
        ax.set_title("fixed points, beta = %.3g" % p.beta)
        ax.legend()
        save_plot(fig, "fp_beta%.3g.png" % p.beta)


def cmd_sweep(args):
    """Reversible drive sweep. A folded loop takes a different path up than
    down (hysteresis); a sliding loop retraces itself."""
    p = resolve_params(args)
    Imax = 4.0
    n_pts = 161
    ups = np.linspace(-Imax, Imax, n_pts)
    downs = ups[::-1]

    g = settle(p, ups[0], g0=0.02)
    g_up = []
    for drv in ups:
        g = settle(p, drv, g0=g)
        g_up.append(g)
    g_up = np.array(g_up)

    g_down = []
    for drv in downs:
        g = settle(p, drv, g0=g)
        g_down.append(g)
    g_down = np.array(g_down)

    # Closed-loop area in the (I, g) plane via the shoelace formula.
    xs = np.concatenate([ups, downs])
    ys = np.concatenate([g_up, g_down])
    area = 0.5 * abs(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys))

    print("reversible drive sweep, beta = %.3g" % p.beta)
    print("  drive I from %.1f up to %.1f and back" % (-Imax, Imax))
    print("  hysteresis loop area = %.2f" % area)
    if area > 0.3:
        print("  the paths differ: history-dependent, the malfunction signature.")
    else:
        print("  the paths lie on top of each other: it slides, no memory.")
    print("  up:   " + sparkline(downsample(g_up, 60), 0.0, 1.0))
    print("  down: " + sparkline(downsample(g_down, 60), 0.0, 1.0))

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(ups, g_up, label="up")
        ax.plot(downs, g_down, label="down")
        ax.set_xlabel("drive I"); ax.set_ylabel("g")
        ax.set_title("sweep, beta = %.3g, area = %.2f" % (p.beta, area))
        ax.legend()
        save_plot(fig, "sweep_beta%.3g.png" % p.beta)


def cmd_recover(args):
    """Critical slowing down. As beta approaches the fold, recovery from a
    nudge slows without bound and lag-1 autocorrelation climbs to 1."""
    p = resolve_params(args)
    betas = np.array([1.0, 2.0, 3.0, 3.5, 3.8, 3.9, 3.95])
    nudge = 0.1
    tol = 0.05 * nudge
    T_max = 600.0

    print("critical slowing down: recovery time and lag-1 autocorrelation")
    print("  beta      return time    AR(1)")
    return_times = []
    ar1s = []
    for beta in betas:
        q = Params(beta=beta, tau_g=p.tau_g, dt=p.dt, noise=0.0)
        # Deterministic recovery from a nudge off the resting state.
        _, g, _ = simulate(q, T_max, n=1, g0=0.5 + nudge)
        dev = np.abs(g[:, 0] - 0.5)
        back = np.where(dev < tol)[0]
        rt = back[0] * q.dt if len(back) else T_max
        return_times.append(rt)
        # Stochastic run at the resting state for the autocorrelation.
        qn = Params(beta=beta, tau_g=p.tau_g, dt=p.dt, noise=0.01, seed=1)
        _, gn, _ = simulate(qn, 400.0, n=1, g0=0.5)
        x = gn[1000:, 0] - 0.5
        ar1 = float(np.corrcoef(x[:-1], x[1:])[0, 1])
        ar1s.append(ar1)
        print("  %-8.3g  %10.1f   %6.3f" % (beta, rt, ar1))
    print("  return time blows up and AR(1) -> 1 as beta -> 4: the tipping point.")

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 4))
        ax[0].plot(betas, return_times, "o-")
        ax[0].set_xlabel("beta"); ax[0].set_ylabel("return time")
        ax[1].plot(betas, ar1s, "o-")
        ax[1].set_xlabel("beta"); ax[1].set_ylabel("lag-1 autocorrelation")
        fig.suptitle("critical slowing down approaching the fold")
        save_plot(fig, "recover.png")


def cmd_series(args):
    """Time series of the field. A folded oscillator (bipolar) cycles slowly;
    a folded loop without recovery (schizophrenia) sits in a basin."""
    p = resolve_params(args)
    if p.noise == 0.0:
        p.noise = 0.02
    T = 1000.0
    t, g, a = simulate(p, T, n=1, g0=0.5, a0=0.5)
    mean_g = g[:, 0]

    # Pad the scale a little past [0,1] so a channel resting on the collapse
    # floor still shows as the lowest visible ramp char rather than blank.
    print("time series, preset = %s, beta = %.3g, ka = %.3g, c = %.3g"
          % (getattr(args, "preset", None), p.beta, p.ka, p.c))
    print("  g:  " + sparkline(downsample(mean_g, 70), -0.1, 1.1))
    if p.adapt and p.ka > 0:
        print("  a:  " + sparkline(downsample(a, 70), -0.1, 1.1))
    # Count arm crossings through the unstable middle as a coarse swing count.
    crossings = int(np.sum(np.diff((mean_g > 0.5).astype(int)) != 0))
    print("  range %.2f to %.2f, crossings of the middle: %d"
          % (mean_g.min(), mean_g.max(), crossings))
    if p.ka >= 4 and p.beta > 4 and p.adapt:
        print("  a slow, coherent oscillation: the operating point cycles and returns.")
    elif p.beta > 4:
        print("  it falls into an arm and stays: no stable middle to rest at.")
    else:
        print("  monostable: small wandering around the single resting state.")

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(t, mean_g, lw=0.8, label="g")
        if p.ka > 0:
            ax.plot(t, a, lw=0.8, label="a (slow)")
        ax.set_xlabel("time"); ax.set_ylabel("g"); ax.set_ylim(-0.02, 1.02)
        ax.set_title("series, preset = %s" % getattr(args, "preset", None))
        ax.legend()
        save_plot(fig, "series_%s.png" % getattr(args, "preset", "custom"))


def cmd_integration(args):
    """Twelve channels. Strong coupling (bipolar) keeps the field one coherent
    thing; weak coupling (schizophrenia) lets the channels scatter into
    different basins and stay there."""
    p = resolve_params(args)
    if p.noise == 0.0:
        p.noise = 0.05
    n = 12
    T = 2000.0
    t, g, a = simulate(p, T, n=n, g0=0.5, a0=0.5,
                       rng=np.random.default_rng(p.seed))

    # Cross-channel spread: how far apart the channels sit, averaged over the
    # back half of the run (after any transient).
    half = g.shape[0] // 2
    spread = float(np.mean(np.std(g[half:], axis=1)))

    print("integration across %d channels, preset = %s, c = %.3g"
          % (n, getattr(args, "preset", None), p.c))
    print(heatmap(downsample(g, 60).T))
    print("  cross-channel spread = %.3f" % spread)
    if spread < 0.1:
        print("  one coherent field: the channels move together.")
    else:
        print("  fragmented: the channels fall into different basins.")

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.imshow(g.T, aspect="auto", cmap="magma", vmin=0, vmax=1,
                  extent=[0, T, 0, n])
        ax.set_xlabel("time"); ax.set_ylabel("channel")
        ax.set_title("integration, preset = %s, spread = %.3f"
                     % (getattr(args, "preset", None), spread))
        save_plot(fig, "integration_%s.png" % getattr(args, "preset", "custom"))


def cmd_profile(args):
    """The miscalibrations. A stable loop aimed at an unusual target shows
    both arms at once as a fixed curve over the environment, never switching.

    adhd:   weight vs reward delay. Steep discounting (k) piles weight on the
            immediate option and starves the delayed one.
    autism: gain mismatch vs volatility. A stuck flexibility (lam) leaves the
            gain too high in volatile contexts and too low in stable ones."""
    p = resolve_params(args)
    preset = getattr(args, "preset", None)

    if preset == "autism" or (preset not in ("adhd",) and p.lam < 1.0):
        # Autism: the autistic gain is stuck; a flexible gain would track the
        # context-optimal precision. Mismatch = realized minus optimal.
        vol = np.linspace(0.0, 1.0, 41)            # environmental volatility
        # The context calls for a drive that is high in stable settings and low
        # in volatile ones. A flexible allocator applies it in full; a stuck one
        # (low lam) applies only a fraction, so its gain barely moves with the
        # context. Both the optimal and the realized gain are read off the same
        # loop, so a fully flexible setting (lam=1) lands exactly on optimal.
        drive_opt = 3.0 * (1.0 - 2.0 * vol)        # +3 when stable, -3 when volatile
        g_opt = np.array([settle(p, d, g0=0.5) for d in drive_opt])
        realized = np.array([settle(p, p.lam * d, g0=0.5) for d in drive_opt])
        mismatch = realized - g_opt
        print("autism profile: gain mismatch vs volatility, lam = %.3g" % p.lam)
        print("  volatility:  stable %s volatile" % ("-" * 50))
        print("  mismatch:    " + sparkline(downsample(mismatch, 50)))
        print("  mismatch spans %.2f to %.2f"
              " (negative = gain too low, collapse; positive = gain too high,"
              " flooding)" % (mismatch.min(), mismatch.max()))
        if mismatch.max() - mismatch.min() > 0.1:
            print("  a stuck gain: too low in stable contexts, too high in"
                  " volatile ones, both at once.")
        else:
            print("  a flexible gain tracks the context: almost no mismatch.")
        print("  a fixed profile either way: it slides with the environment,"
              " it never switches.")
        xs, ys, xlabel, ylabel, fname = vol, mismatch, "volatility", "gain mismatch", "autism"
    else:
        # ADHD: value of a reward falls with delay as 1/(1+k*d). Steep k makes
        # the immediate option outrank the delayed one. The allocator's weight
        # is the resting g under a drive set by that discounted value.
        delay = np.linspace(0.0, 10.0, 41)
        value = 1.0 / (1.0 + p.k * delay)
        weight = []
        for val in value:
            drive = 4.0 * (val - 0.5)
            weight.append(settle(p, drive, g0=0.5))
        weight = np.array(weight)
        print("adhd profile: weight vs reward delay, k = %.3g" % p.k)
        print("  delay:       now %s later" % ("-" * 52))
        print("  weight:      " + sparkline(downsample(weight, 50), 0.0, 1.0))
        print("  crossover at delay ~ %.2f; weight piled on the immediate"
              " (%.2f) and starved from the delayed (%.2f)."
              % (1.0 / p.k, weight[0], weight[-1]))
        print("  both arms at once, held steady: a miscalibration, not a swing.")
        xs, ys, xlabel, ylabel, fname = delay, weight, "reward delay", "weight", "adhd"

    if maybe_plot(args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, ys, "o-")
        ax.axhline(0.5 if fname == "adhd" else 0.0, color="k", lw=0.6, ls="--")
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.set_title("%s profile" % fname)
        save_plot(fig, "profile_%s.png" % fname)


def cmd_demo(args):
    """The whole contrast, narrated."""
    print("=" * 70)
    print("ALLOCATOR TOY MODEL: one update rule, two kinds of fault")
    print("=" * 70)
    print()
    print("One number, beta, sorts the kinds of fault. It is the loop gain on")
    print("self-supporting evidence. beta=4 is the tipping point.")
    print()

    print("-- fixed points: beta=2 slides, beta=8 has folded into two arms --")
    for beta in (2.0, 8.0):
        fps = fixed_points(beta)
        stable = ["%.3f" % g for g, s in fps if s]
        print("  beta=%.0f: stable resting states at %s" % (beta, ", ".join(stable)))
    print()

    print("-- malfunction vs miscalibration: a reversible drive sweep --")
    for beta in (8.0, 2.0):
        a = _sweep_area(beta)
        tag = "folded: history-dependent" if a > 0.3 else "sliding: no memory"
        print("  beta=%.0f: hysteresis area = %.2f  (%s)" % (beta, a, tag))
    print()

    print("-- approaching the fold: recovery slows without bound --")
    for beta in (1.0, 3.0, 3.95):
        rt = _return_time(beta)
        print("  beta=%.2f: return time = %.1f" % (beta, rt))
    print()

    print("-- the two malfunctions differ by which variable folds --")
    bip = _spread("bipolar")
    scz = _spread("schizophrenia")
    print("  bipolar (c=3):       cross-channel spread = %.3f  (one field, returns)" % bip)
    print("  schizophrenia (c=0.2): cross-channel spread = %.3f  (fragments, stays)" % scz)
    print()

    print("-- the miscalibrations never switch: a fixed two-armed profile --")
    print("  adhd:   weight high on the immediate, starved from the delayed.")
    print("  autism: gain too high in volatile contexts, too low in stable ones.")
    print()
    print("Run any of: fp, sweep, recover, series, integration, profile.")
    print("Add --preset {baseline,schizophrenia,bipolar,adhd,autism} and --plot.")


# Small helpers reused by the demo so it stays a narration over the real runs.

def _sweep_area(beta):
    p = Params(beta=beta)
    Imax, n_pts = 4.0, 161
    ups = np.linspace(-Imax, Imax, n_pts)
    g = settle(p, ups[0], g0=0.02)
    g_up = []
    for drv in ups:
        g = settle(p, drv, g0=g)
        g_up.append(g)
    g_down = []
    for drv in ups[::-1]:
        g = settle(p, drv, g0=g)
        g_down.append(g)
    xs = np.concatenate([ups, ups[::-1]])
    ys = np.concatenate([g_up, g_down])
    return 0.5 * abs(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys))


def _return_time(beta):
    p = Params(beta=beta, noise=0.0)
    _, g, _ = simulate(p, 600.0, n=1, g0=0.6)
    dev = np.abs(g[:, 0] - 0.5)
    back = np.where(dev < 0.005)[0]
    return back[0] * p.dt if len(back) else 600.0


def _spread(preset):
    p = Params(**PRESETS[preset])
    p.noise = 0.05
    _, g, _ = simulate(p, 2000.0, n=12, g0=0.5, rng=np.random.default_rng(0))
    half = g.shape[0] // 2
    return float(np.mean(np.std(g[half:], axis=1)))


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Allocator toy model: one update rule, two kinds of fault.")
    sub = parser.add_subparsers(dest="command")

    def add_common(sp):
        sp.add_argument("--preset", choices=list(PRESETS.keys()))
        sp.add_argument("--beta", type=float, help="stability setting (loop gain)")
        sp.add_argument("--I", type=float, help="external drive")
        sp.add_argument("--ka", type=float, help="strength of slow adaptation")
        sp.add_argument("--c", type=float, help="integration coupling")
        sp.add_argument("--k", type=float, help="discount steepness (ADHD)")
        sp.add_argument("--lam", type=float, help="flexibility (autism)")
        sp.add_argument("--adapt", type=int, choices=(0, 1),
                        help="engage the slow adaptation a (default on)")
        sp.add_argument("--noise", type=float, help="noise amplitude")
        sp.add_argument("--seed", type=int, help="random seed")
        sp.add_argument("--dt", type=float, help="integration step")
        sp.add_argument("--plot", action="store_true",
                        help="save PNGs to out/ if matplotlib is installed")

    for name, fn in (("demo", cmd_demo), ("fp", cmd_fp), ("sweep", cmd_sweep),
                     ("recover", cmd_recover), ("series", cmd_series),
                     ("integration", cmd_integration), ("profile", cmd_profile)):
        sp = sub.add_parser(name, help=fn.__doc__.splitlines()[0] if fn.__doc__ else name)
        add_common(sp)
        sp.set_defaults(func=fn)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        cmd_demo(args if hasattr(args, "plot") else argparse.Namespace(plot=False))
        return
    args.func(args)


if __name__ == "__main__":
    main()
