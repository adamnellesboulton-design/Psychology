"""
Allocator Toy Model
===================

A runnable, deliberately minimal demonstration of the mechanics in
"One Allocator, Two Kinds of Fault." A sandbox for the dynamics, not a claim
that the hypothesis is true. See README.md for the full tour; this header keeps
only the one equation and the rules for editing it.

Pure Python standard library: no numpy, no matplotlib, nothing to install. The
default output is ASCII; --plot writes self-contained SVG files (any browser
opens them).

The one moving part is g, the allocator's net gain on relevance, in (0, 1).
high g = the flooding arm; low g = the collapse arm. Both arms are two readings
of one variable. The whole model is one update rule run with different knobs:

    dg_i/dt = ( -g_i + S( beta*(g_i - 0.5) + I - ka*(a - 0.5)
                          + c*(mean(g) - g_i) + noise_i ) ) / tau_g
    da/dt   = ( mean(g) - a ) / tau_a          # slow; only the oscillator uses it

S is the logistic squash; i indexes channels (1 by default, 12 for integration).
a is "the bar" of the paper: the level of relevance the homeostat demands before
it admits a bid, drifting slowly against whichever state the field is in. The
knobs map to named settings in the paper (see the Params class and README):
beta = self-reinforcement / loop gain, I = external drive, ka = strength of the
slow homeostat that sets the bar a, c = integrating gain / coupling across
channels, k = discount steepness (ADHD target), lam = flexibility (autism).

The allocator runs two slow controls, and the two malfunctions are each one of
them crossing a different bifurcation -- the whole cut of the theory:
- the INTEGRATING GAIN (coherence; c) crosses a FOLD. Past beta=4 the loop is
  bistable, two basins with a tipping point between; across many channels with
  weak coupling the field fragments and does not return -> schizophrenia.
- the HOMEOSTAT (the bar; ka, a) crosses a HOPF. The homeostat opposes the
  self-reinforcement, so the effective gain is beta-ka and a single euthymic
  resting state survives; but it can lose its damping (trace > 0) and the field
  orbits euthymia instead of resting at it -> bipolar. A euthymic baseline
  remains to return to, which a fold would not leave.
The two slowings differ and say which tip is coming: a fold slows monotonically,
a Hopf rings, the wobble growing and lengthening as the damping dies.

MISCALIBRATION = both controls intact (beta low) but a target (k or lam) set odd;
the output holds a fixed two-armed offset and never switches -> ADHD, autism.

House rules if Claude Code edits this:
- ASCII only. No em or en dashes, no curly quotes, no unicode math or block
  glyphs. Use straight quotes and the ASCII intensity ramp in RAMP.
- Pure standard library. Do not reintroduce numpy, matplotlib, or any other
  third-party dependency; keep it something that runs anywhere python does.
- Keep it a toy: one file, one update rule, readable over clever. If a change
  needs a second mechanism, ask whether the existing knob can do it first.
- Every knob stays mapped to a named setting in the paper (stability,
  integration, discount, flexibility). Do not add a parameter without saying
  which part of the hypothesis it stands for.
- The model demonstrates mechanics; it is not fitted to data and should not
  pretend to be. Keep claims in comments and output proportionate to that.
"""

import argparse
import http.server
import math
import os
import random
import webbrowser

# ASCII intensity ramp, low to high. Used for every sparkline and heatmap so
# the toy runs in a bare terminal with nothing to install.
RAMP = " .:-=+*#%@"


# ----------------------------------------------------------------------------
# Small numeric helpers (standard library only)
# ----------------------------------------------------------------------------

def S(x):
    """Logistic squash, written for numerical stability. Slope at the center is
    0.25, which is why beta=4 is the fold: beta * 0.25 = 1 is the gain at which
    one resting state splits."""
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def pstdev(xs):
    if not xs:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def pearson(a, b):
    """Pearson correlation of two equal-length sequences."""
    n = len(a)
    if n < 2:
        return float("nan")
    ma, mb = mean(a), mean(b)
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((a[i] - ma) ** 2 for i in range(n)))
    db = math.sqrt(sum((b[i] - mb) ** 2 for i in range(n)))
    return num / (da * db) if da > 0.0 and db > 0.0 else float("nan")


def linspace(a, b, n):
    if n == 1:
        return [a]
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ----------------------------------------------------------------------------
# The one update rule
# ----------------------------------------------------------------------------

class Params:
    """The knobs. Each maps to a named setting in the paper (see module docs)."""

    def __init__(self, beta=2.0, I=0.0, ka=0.0, c=1.0, k=0.2, lam=1.0,
                 adapt=True, noise=0.0, tau_g=1.0, tau_a=40.0, dt=0.05, seed=0):
        self.beta = beta      # self-reinforcement / loop gain (the fold engine)
        self.I = I            # external drive
        self.ka = ka          # homeostat strength (sets the bar a; its Hopf is bipolar)
        self.c = c            # integrating gain / coupling (its fold is schizophrenia)
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

    Returns (t, g, a) where t is a list of times, g is a list of per-step lists
    (one entry per channel), and a is a list of the slow variable. drive, if
    given, is a function of time returning the external drive I; otherwise the
    constant p.I is used.
    """
    steps = int(round(T / p.dt))
    if rng is None:
        rng = random.Random(p.seed)
    if g0 is None:
        g = [0.5] * n
    elif isinstance(g0, (list, tuple)):
        g = [float(x) for x in g0]
    else:
        g = [float(g0)] * n
    a = float(a0)

    out_g, out_a, t = [], [], []
    for s in range(steps):
        now = s * p.dt
        drv = p.I if drive is None else drive(now)
        mg = sum(g) / n
        new_g = []
        for gi in g:
            x = p.beta * (gi - 0.5) + drv - p.ka * (a - 0.5) + p.c * (mg - gi)
            if p.noise > 0.0:
                x += p.noise * rng.gauss(0.0, 1.0)
            new_g.append(gi + p.dt * (-gi + S(x)) / p.tau_g)
        g = new_g
        if p.adapt:
            a = a + p.dt * (mg - a) / p.tau_a
        out_g.append(g)
        out_a.append(a)
        t.append(now)
    return t, out_g, out_a


def settle(p, drive_value, g0, a0=0.5, T=80.0):
    """Run a single channel to its resting state under a constant drive and
    return the final g. Used by the quasi-static sweep and the profiles."""
    q = Params(beta=p.beta, I=drive_value, ka=p.ka, c=p.c, adapt=p.adapt,
               noise=0.0, tau_g=p.tau_g, tau_a=p.tau_a, dt=p.dt)
    _, g, _ = simulate(q, T, n=1, g0=g0, a0=a0)
    return g[-1][0]


# ----------------------------------------------------------------------------
# Fixed points of the single-channel loop
# ----------------------------------------------------------------------------

def fixed_points(beta, drive=0.0):
    """Resting states of dg/dt = (-g + S(beta*(g-0.5) + drive))/tau_g.

    Returns a list of (g, stable) pairs. Below beta=4 there is one; above it
    there are three (two stable arms and an unstable threshold between)."""
    grid = linspace(1e-4, 1 - 1e-4, 4000)

    def h(g):
        return S(beta * (g - 0.5) + drive) - g

    hs = [h(g) for g in grid]
    roots = []
    for i in range(len(grid) - 1):
        if hs[i] == 0.0 or hs[i] * hs[i + 1] < 0.0:
            lo, hi = grid[i], grid[i + 1]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if h(lo) * h(mid) <= 0.0:
                    hi = mid
                else:
                    lo = mid
            g = 0.5 * (lo + hi)
            # Stable when the RHS slope is negative: -1 + beta*S'(.) < 0.
            sx = S(beta * (g - 0.5) + drive)
            slope = -1.0 + beta * sx * (1.0 - sx)
            roots.append((g, slope < 0.0))
    out = []
    for g, st in roots:
        if not any(abs(g - g2) < 1e-3 for g2, _ in out):
            out.append((g, st))
    return out


# ----------------------------------------------------------------------------
# ASCII rendering
# ----------------------------------------------------------------------------

def sparkline(values, lo=None, hi=None):
    """One-line ASCII sparkline using the intensity ramp."""
    v = list(values)
    if lo is None:
        lo = min(v)
    if hi is None:
        hi = max(v)
    if hi - lo < 1e-12:
        hi = lo + 1e-12
    out = []
    for x in v:
        f = (x - lo) / (hi - lo)
        f = 0.0 if f < 0.0 else (1.0 if f > 1.0 else f)
        out.append(RAMP[int(round(f * (len(RAMP) - 1)))])
    return "".join(out)


def heatmap(matrix, lo=0.0, hi=1.0):
    """ASCII heatmap. Rows are channels, columns are time samples."""
    lines = []
    for row in matrix:
        chars = []
        for x in row:
            f = (x - lo) / (hi - lo)
            f = 0.0 if f < 0.0 else (1.0 if f > 1.0 else f)
            chars.append(RAMP[int(round(f * (len(RAMP) - 1)))])
        lines.append("|" + "".join(chars) + "|")
    return "\n".join(lines)


def downsample(arr, width):
    """Pick `width` evenly spaced entries from a list."""
    n = len(arr)
    if n <= width:
        return list(arr)
    idx = [int(round(i * (n - 1) / (width - 1))) for i in range(width)]
    return [arr[i] for i in idx]


# ----------------------------------------------------------------------------
# SVG plotting (self-contained; --plot writes plain-text SVG to out/)
# ----------------------------------------------------------------------------

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]


def _fmt(v):
    if v == 0:
        return "0"
    if abs(v) >= 1000 or abs(v) < 0.001:
        return "%.1e" % v
    return "%.3g" % v


def _svg_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_open(w, h):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" font-family="monospace" font-size="12">'
            '<rect width="%d" height="%d" fill="white"/>' % (w, h, w, h, w, h))


def _write_svg(name, parts):
    os.makedirs("out", exist_ok=True)
    path = "out/" + name + ".svg"
    with open(path, "w") as f:
        f.write("\n".join(parts) + "\n</svg>\n")
    print("saved " + path)


def save_svg_lines(name, title, xlabel, ylabel, series, markers=False, points=None):
    """One or more line series on shared axes. series is a list of
    (label, xs, ys). points, if given, is a list of (x, y, stable) markers."""
    W, H = 680, 420
    ml, mr, mt, mb = 64, 150, 44, 52
    px0, px1, py0, py1 = ml, W - mr, H - mb, mt

    xs_all = [x for _, xs, _ in series for x in xs]
    ys_all = [y for _, _, ys in series for y in ys]
    if points:
        xs_all += [q[0] for q in points]
        ys_all += [q[1] for q in points]
    xmin, xmax = min(xs_all), max(xs_all)
    ymin, ymax = min(ys_all), max(ys_all)
    if xmax <= xmin:
        xmax = xmin + 1.0
    if ymax <= ymin:
        ymax = ymin + 1.0
    ymin -= 0.06 * (ymax - ymin)
    ymax += 0.06 * (ymax - ymin)

    def X(x):
        return px0 + (x - xmin) / (xmax - xmin) * (px1 - px0)

    def Y(y):
        return py0 + (y - ymin) / (ymax - ymin) * (py1 - py0)

    out = [_svg_open(W, H)]
    out.append('<text x="%g" y="22" font-size="15">%s</text>' % (ml, _svg_escape(title)))
    out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="black"/>' % (px0, py0, px1, py0))
    out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="black"/>' % (px0, py0, px0, py1))
    for i in range(6):
        xv = xmin + (xmax - xmin) * i / 5
        xp = X(xv)
        out.append('<text x="%g" y="%g" text-anchor="middle" fill="#444">%s</text>'
                   % (xp, py0 + 18, _fmt(xv)))
        yv = ymin + (ymax - ymin) * i / 5
        yp = Y(yv)
        out.append('<text x="%g" y="%g" text-anchor="end" fill="#444">%s</text>'
                   % (px0 - 8, yp + 4, _fmt(yv)))
    out.append('<text x="%g" y="%g" text-anchor="middle">%s</text>'
               % ((px0 + px1) / 2, H - 14, _svg_escape(xlabel)))
    out.append('<text x="16" y="%g" transform="rotate(-90 16 %g)" text-anchor="middle">%s</text>'
               % ((py0 + py1) / 2, (py0 + py1) / 2, _svg_escape(ylabel)))
    for i, (label, xs, ys) in enumerate(series):
        col = PALETTE[i % len(PALETTE)]
        pts = " ".join("%.2f,%.2f" % (X(x), Y(y)) for x, y in zip(xs, ys))
        out.append('<polyline fill="none" stroke="%s" stroke-width="1.6" points="%s"/>'
                   % (col, pts))
        if markers:
            for x, y in zip(xs, ys):
                out.append('<circle cx="%.2f" cy="%.2f" r="2.5" fill="%s"/>' % (X(x), Y(y), col))
        ly = mt + 10 + i * 18
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2.5"/>'
                   % (px1 + 12, ly, px1 + 32, ly, col))
        out.append('<text x="%g" y="%g">%s</text>' % (px1 + 38, ly + 4, _svg_escape(label)))
    if points:
        for x, y, stable in points:
            col = "#2ca02c" if stable else "#d62728"
            out.append('<circle cx="%.2f" cy="%.2f" r="4" fill="%s" stroke="black"/>'
                       % (X(x), Y(y), col))
    _write_svg(name, out)


def _heat_rgb(f):
    f = 0.0 if f < 0.0 else (1.0 if f > 1.0 else f)
    stops = [(0.0, (0, 0, 4)), (0.25, (81, 18, 124)), (0.5, (183, 55, 121)),
             (0.75, (252, 137, 97)), (1.0, (252, 253, 191))]
    for i in range(len(stops) - 1):
        f0, c0 = stops[i]
        f1, c1 = stops[i + 1]
        if f <= f1:
            t = (f - f0) / (f1 - f0) if f1 > f0 else 0.0
            return "#%02x%02x%02x" % tuple(int(c0[j] + (c1[j] - c0[j]) * t) for j in range(3))
    return "#fcfdbf"


def save_svg_heatmap(name, title, matrix, vmin=0.0, vmax=1.0,
                     xlabel="time", ylabel="channel"):
    rows, cols = len(matrix), len(matrix[0])
    W, H = 680, 360
    ml, mr, mt, mb = 64, 24, 44, 50
    pw, ph = W - ml - mr, H - mt - mb
    cw, chh = pw / cols, ph / rows
    out = [_svg_open(W, H)]
    out.append('<text x="%g" y="22" font-size="15">%s</text>' % (ml, _svg_escape(title)))
    for r in range(rows):
        for cidx in range(cols):
            f = (matrix[r][cidx] - vmin) / (vmax - vmin) if vmax > vmin else 0.0
            x = ml + cidx * cw
            y = mt + r * chh
            out.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>'
                       % (x, y, cw + 0.6, chh + 0.6, _heat_rgb(f)))
    out.append('<text x="%g" y="%g" text-anchor="middle">%s</text>'
               % (ml + pw / 2, H - 14, _svg_escape(xlabel)))
    out.append('<text x="16" y="%g" transform="rotate(-90 16 %g)" text-anchor="middle">%s</text>'
               % (mt + ph / 2, mt + ph / 2, _svg_escape(ylabel)))
    _write_svg(name, out)


def maybe_plot(args):
    """SVG plotting is built in, so this is just whether the user asked for it."""
    return bool(getattr(args, "plot", False))


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
    """Resting states, and the two ways they can go unstable. The homeostat
    opposes the self-reinforcement, so the loop's effective gain is beta - ka.
    With the homeostat off (ka=0) a strong loop folds into two basins -- the
    fold behind schizophrenia. With it on, even a strong loop keeps a single
    euthymic resting state, but that state can lose its damping and orbit -- the
    Hopf behind bipolar."""
    p = resolve_params(args)
    ge = p.beta - (p.ka if p.adapt else 0.0)
    fps = fixed_points(ge)
    # 2D Jacobian trace at euthymia decides whether the single point rings (Hopf).
    trace = (0.25 * p.beta - 1.0) / p.tau_g - 1.0 / p.tau_a
    hopf = (len(fps) == 1 and trace > 0.0)
    print("resting states, beta = %.3g, ka = %.3g  (effective gain beta-ka = %.3g)"
          % (p.beta, p.ka if p.adapt else 0.0, ge))
    for g, stable in fps:
        st = stable and not hopf
        kind = "stable  " if st else ("orbited " if hopf else "unstable")
        arm = ""
        if st and g > 0.6:
            arm = "  <- flooding arm"
        elif st and g < 0.4:
            arm = "  <- collapse arm"
        elif hopf:
            arm = "  <- euthymia (the swing orbits this)"
        print("  g* = %.4f   %s%s" % (g, kind, arm))
    if len(fps) >= 3:
        print("a fold: two basins with a tipping point between. The integrating")
        print("gain has folded -- it falls into one basin and stays (schizophrenia).")
    elif hopf:
        print("a Hopf: one euthymic resting state, but it has lost its damping, so")
        print("the allocator orbits euthymia instead of resting at it (bipolar).")
    else:
        print("one calm resting state at euthymia: nudge it and it settles back.")

    if maybe_plot(args):
        grid = linspace(0.0, 1.0, 400)
        curve = [S(ge * (g - 0.5)) for g in grid]
        title = ("Where the allocator can settle (effective gain %.3g)" % ge)
        save_svg_lines("fp_beta%s" % _num(p.beta), title,
                       "its state: collapsed -> flooded", "where it moves next",
                       [("next state", grid, curve), ("stays put", grid, grid)],
                       points=[(g, g, st and not hopf) for g, st in fps])


def cmd_sweep(args):
    """Reversible drive sweep. A folded loop takes a different path up than
    down (hysteresis); a sliding loop retraces itself."""
    p = resolve_params(args)
    Imax, n_pts = 4.0, 161
    ups = linspace(-Imax, Imax, n_pts)
    downs = ups[::-1]

    g = settle(p, ups[0], g0=0.02)
    g_up = []
    for drv in ups:
        g = settle(p, drv, g0=g)
        g_up.append(g)
    g_down = []
    for drv in downs:
        g = settle(p, drv, g0=g)
        g_down.append(g)

    xs = ups + downs
    ys = g_up + g_down
    area = _loop_area(xs, ys)

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
        save_svg_lines("sweep_beta%s" % _num(p.beta),
                       "sweep, beta = %s, area = %.2f" % (_num(p.beta), area),
                       "drive I", "g", [("up", ups, g_up), ("down", downs, g_down)])


def cmd_recover(args):
    """Critical slowing down, and the two shapes it takes. Approaching either
    bifurcation the allocator recovers more and more slowly from a nudge -- the
    early warning, measurable before anything switches. But the two malfunctions
    slow differently, and the difference says which tip is coming: a fold (the
    integrating gain, schizophrenia's onset) creeps back monotonically, while a
    Hopf (the homeostat, bipolar) rings, the wobble growing and lengthening as
    the damping dies."""
    p = resolve_params(args)
    betas = [1.0, 2.0, 3.0, 3.5, 3.8, 3.9, 3.95]
    nudge = 0.1
    tol = 0.05 * nudge
    T_max = 600.0

    # The shared early warning: recovery time climbing toward the edge (fold).
    print("critical slowing down: the early warning, and which tip is coming")
    print("  approaching the edge, recovery from a nudge slows -- the early warning:")
    return_times, ar1s = [], []
    for beta in betas:
        q = Params(beta=beta, tau_g=p.tau_g, dt=p.dt, noise=0.0)
        _, g, _ = simulate(q, T_max, n=1, g0=0.5 + nudge)
        rt = T_max
        for s in range(len(g)):
            if abs(g[s][0] - 0.5) < tol:
                rt = s * q.dt
                break
        return_times.append(rt)
        qn = Params(beta=beta, tau_g=p.tau_g, dt=p.dt, noise=0.01, seed=1)
        _, gn, _ = simulate(qn, 400.0, n=1, g0=0.5)
        x = [gn[s][0] - 0.5 for s in range(1000, len(gn))]
        ar1s.append(pearson(x[:-1], x[1:]))
    print("    beta:        " + " ".join("%4.2g" % b for b in betas))
    print("    return time: " + " ".join("%4.0f" % r for r in return_times))

    # The discriminator: the SHAPE of the recovery near the edge. A fold (ka=0)
    # crawls back without overshoot; a Hopf (homeostat engaged) rings.
    T_shape = 200.0
    fold = Params(beta=3.97, ka=0.0, noise=0.0, tau_g=p.tau_g, tau_a=p.tau_a, dt=p.dt)
    hopf = Params(beta=3.97, ka=3.97, noise=0.0, tau_g=p.tau_g, tau_a=p.tau_a, dt=p.dt)
    _, gf, _ = simulate(fold, T_shape, n=1, g0=0.5 + nudge)
    _, gh, _ = simulate(hopf, T_shape, n=1, g0=0.5 + nudge)
    fold_dev = [row[0] - 0.5 for row in gf]
    hopf_dev = [row[0] - 0.5 for row in gh]
    print("  but a fold and a Hopf slow differently, near the edge:")
    print("    fold (schizophrenia), monotone crawl: "
          + sparkline(downsample(fold_dev, 48), -nudge, nudge))
    print("    Hopf (bipolar), a growing ring:       "
          + sparkline(downsample(hopf_dev, 48), -nudge, nudge))
    print("  the fold creeps to the edge without wobbling; the Hopf rings, and the")
    print("  ring grows and lengthens as the damping dies -- that is which tip is near.")

    if maybe_plot(args):
        save_svg_lines("recover_slowing", "Recovery slows approaching the edge",
                       "toward the tipping point ->", "recovery time",
                       [("recovery time", betas, return_times)], markers=True)
        tt = [i * p.dt for i in range(len(fold_dev))]
        save_svg_lines("recover_shape", "Two shapes of slowing near the edge",
                       "time after a nudge", "distance from euthymia",
                       [("fold: monotone crawl", tt, fold_dev),
                        ("Hopf: a growing ring", tt, hopf_dev)])


def cmd_series(args):
    """Time series of the field. With the homeostat past its Hopf (bipolar) the
    single euthymic point loses its damping and the field swings around it and
    back; a folded loop without the homeostat (schizophrenia) drops into a basin
    and stays."""
    p = resolve_params(args)
    if p.noise == 0.0:
        p.noise = 0.02
    T = 1000.0
    t, g, a = simulate(p, T, n=1, g0=0.5, a0=0.5)
    mean_g = [row[0] for row in g]

    # Pad the scale a little past [0,1] so a channel resting on the collapse
    # floor still shows as the lowest visible ramp char rather than blank.
    print("time series, preset = %s, beta = %.3g, ka = %.3g, c = %.3g"
          % (getattr(args, "preset", None), p.beta, p.ka, p.c))
    print("  g:  " + sparkline(downsample(mean_g, 70), -0.1, 1.1))
    if p.adapt and p.ka > 0:
        print("  a:  " + sparkline(downsample(a, 70), -0.1, 1.1))
    crossings = sum(1 for i in range(len(mean_g) - 1)
                    if (mean_g[i] > 0.5) != (mean_g[i + 1] > 0.5))
    print("  range %.2f to %.2f, crossings of the middle: %d"
          % (min(mean_g), max(mean_g), crossings))
    ge = p.beta - (p.ka if p.adapt else 0.0)
    trace = (0.25 * p.beta - 1.0) / p.tau_g - 1.0 / p.tau_a
    if p.adapt and p.ka > 0 and ge < 4 and trace > 0:
        print("  a slow swing around euthymia: the homeostat has crossed its Hopf,")
        print("  so the field rings between flood and collapse and back (bipolar).")
    elif p.beta > 4 and ge >= 4:
        print("  it falls into a basin and stays: the integrating gain has folded,")
        print("  with no euthymic middle to return to (schizophrenia).")
    else:
        print("  it rests near euthymia, wandering a little with the noise (stable).")

    if maybe_plot(args):
        series = [("g", t, mean_g)]
        if p.ka > 0:
            series.append(("a (slow)", t, a))
        save_svg_lines("series_%s" % (getattr(args, "preset", None) or "custom"),
                       "series, preset = %s" % getattr(args, "preset", None),
                       "time", "g", series)


def cmd_integration(args):
    """Twelve channels. Strong coupling (bipolar) keeps the field one coherent
    thing; weak coupling (schizophrenia) lets the channels scatter into
    different basins and stay there."""
    p = resolve_params(args)
    if p.noise == 0.0:
        p.noise = 0.05
    n = 12
    T = 2000.0
    t, g, a = simulate(p, T, n=n, g0=0.5, a0=0.5, rng=random.Random(p.seed))

    # Cross-channel spread: how far apart the channels sit, averaged over the
    # back half of the run (after any transient).
    half = len(g) // 2
    spread = mean([pstdev(g[s]) for s in range(half, len(g))])

    print("integration across %d channels, preset = %s, c = %.3g"
          % (n, getattr(args, "preset", None), p.c))
    gd = downsample(g, 60)
    mat = [[gd[s][ch] for s in range(len(gd))] for ch in range(n)]
    print(heatmap(mat))
    print("  cross-channel spread = %.3f" % spread)
    if spread < 0.1:
        print("  one coherent field: the channels move together.")
    else:
        print("  fragmented: the channels fall into different basins.")
        print("  this is the established schizophrenic state: chaos, not a fold,")
        print("  so its signature is lost integration, not critical slowing.")

    if maybe_plot(args):
        wide = downsample(g, 240)
        mat2 = [[wide[s][ch] for s in range(len(wide))] for ch in range(n)]
        save_svg_heatmap("integration_%s" % (getattr(args, "preset", None) or "custom"),
                         "integration, preset = %s, spread = %.3f"
                         % (getattr(args, "preset", None), spread), mat2)


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
        vol = linspace(0.0, 1.0, 41)               # environmental volatility
        # The context calls for a drive that is high in stable settings and low
        # in volatile ones. A flexible allocator applies it in full; a stuck one
        # (low lam) applies only a fraction, so its gain barely moves with the
        # context. Both the optimal and the realized gain are read off the same
        # loop, so a fully flexible setting (lam=1) lands exactly on optimal.
        drive_opt = [3.0 * (1.0 - 2.0 * v) for v in vol]   # +3 stable, -3 volatile
        g_opt = [settle(p, d, g0=0.5) for d in drive_opt]
        realized = [settle(p, p.lam * d, g0=0.5) for d in drive_opt]
        mismatch = [realized[i] - g_opt[i] for i in range(len(vol))]
        print("autism profile: gain mismatch vs volatility, lam = %.3g" % p.lam)
        print("  volatility:  stable %s volatile" % ("-" * 50))
        print("  mismatch:    " + sparkline(downsample(mismatch, 50)))
        print("  mismatch spans %.2f to %.2f"
              " (negative = gain too low, collapse; positive = gain too high,"
              " flooding)" % (min(mismatch), max(mismatch)))
        if max(mismatch) - min(mismatch) > 0.1:
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
        delay = linspace(0.0, 10.0, 41)
        value = [1.0 / (1.0 + p.k * d) for d in delay]
        weight = [settle(p, 4.0 * (val - 0.5), g0=0.5) for val in value]
        print("adhd profile: weight vs reward delay, k = %.3g" % p.k)
        print("  delay:       now %s later" % ("-" * 52))
        print("  weight:      " + sparkline(downsample(weight, 50), 0.0, 1.0))
        print("  crossover at delay ~ %.2f; weight piled on the immediate"
              " (%.2f) and starved from the delayed (%.2f)."
              % (1.0 / p.k, weight[0], weight[-1]))
        print("  both arms at once, held steady: a miscalibration, not a swing.")
        xs, ys, xlabel, ylabel, fname = delay, weight, "reward delay", "weight", "adhd"

    if maybe_plot(args):
        save_svg_lines("profile_%s" % fname, "%s profile" % fname,
                       xlabel, ylabel, [(ylabel, xs, ys)])


def cmd_demo(args):
    """The whole contrast, narrated."""
    print("=" * 70)
    print("ALLOCATOR TOY MODEL: one update rule, two kinds of fault")
    print("=" * 70)
    print()
    print("Two slow controls can lose stability, each at its own bifurcation,")
    print("which is the whole cut. The integrating gain folds (schizophrenia);")
    print("the homeostat that sets the bar crosses a Hopf (bipolar).")
    print()

    print("-- the integrating gain folds: two basins past beta=4 --")
    for beta in (2.0, 8.0):
        fps = fixed_points(beta)
        stable = ["%.3f" % g for g, s in fps if s]
        kind = "two basins (a fold)" if len(stable) >= 2 else "one euthymic point"
        print("  beta=%.0f: resting states at %s  (%s)" % (beta, ", ".join(stable), kind))
    print()

    print("-- the homeostat's Hopf keeps euthymia but loses its damping --")
    print("  bipolar (beta=8, ka=6): effective gain beta-ka = 2, so one euthymic")
    print("  point -- but it has crossed its Hopf, so the field orbits it.")
    print()

    print("-- malfunction vs miscalibration: a reversible drive sweep --")
    for beta in (8.0, 2.0):
        a = _sweep_area(beta)
        tag = "folded: history-dependent" if a > 0.3 else "sliding: no memory"
        print("  beta=%.0f: hysteresis area = %.2f  (%s)" % (beta, a, tag))
    print()

    print("-- approaching either edge, recovery slows (the early warning) --")
    for beta in (1.0, 3.0, 3.95):
        rt = _return_time(beta)
        print("  beta=%.2f: return time = %.1f" % (beta, rt))
    print("  a fold slows monotonically; a Hopf rings as it slows (see: recover).")
    print()

    print("-- the two malfunctions differ by which control fails --")
    bip = _spread("bipolar")
    scz = _spread("schizophrenia")
    print("  bipolar (homeostat Hopf):    cross-channel spread = %.3f  (one field, returns)" % bip)
    print("  schizophrenia (gain folds):  cross-channel spread = %.3f  (fragments, stays)" % scz)
    print()

    print("-- the miscalibrations never switch: a fixed two-armed profile --")
    print("  adhd:   weight high on the immediate, starved from the delayed.")
    print("  autism: gain too high in volatile contexts, too low in stable ones.")
    print()
    print("Run any of: fp, sweep, recover, series, integration, profile.")
    print("Add --preset {baseline,schizophrenia,bipolar,adhd,autism} and --plot.")
    print("For how to use this and every variable described: allocator_toy.py guide.")


# Small helpers reused by the demo so it stays a narration over the real runs.

def _loop_area(xs, ys):
    """Closed-loop area in the (x, y) plane via the shoelace formula."""
    n = len(xs)
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += xs[i] * ys[j] - xs[j] * ys[i]
    return 0.5 * abs(s)


def _sweep_area(beta):
    p = Params(beta=beta)
    ups = linspace(-4.0, 4.0, 161)
    g = settle(p, ups[0], g0=0.02)
    g_up = []
    for drv in ups:
        g = settle(p, drv, g0=g)
        g_up.append(g)
    g_down = []
    for drv in ups[::-1]:
        g = settle(p, drv, g0=g)
        g_down.append(g)
    return _loop_area(ups + ups[::-1], g_up + g_down)


def _return_time(beta):
    p = Params(beta=beta, noise=0.0)
    _, g, _ = simulate(p, 600.0, n=1, g0=0.6)
    for s in range(len(g)):
        if abs(g[s][0] - 0.5) < 0.005:
            return s * p.dt
    return 600.0


def _spread(preset):
    p = Params(**PRESETS[preset])
    p.noise = 0.05
    _, g, _ = simulate(p, 2000.0, n=12, g0=0.5, rng=random.Random(0))
    half = len(g) // 2
    return mean([pstdev(g[s]) for s in range(half, len(g))])


def _num(x):
    """Render a default as a short, plain string for the guide table."""
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def cmd_guide(args):
    """How to use this model, with a description of every variable."""
    d = Params()  # defaults are read off a fresh Params so they cannot drift
    line = "-" * 70

    print("=" * 70)
    print("ALLOCATOR TOY MODEL: HOW TO USE IT")
    print("=" * 70)
    print()
    print("A sandbox for the mechanics in 'One Allocator, Two Kinds of Fault.'")
    print("It is not fitted to data and makes no claim that the hypothesis is")
    print("true; it lets you turn the knobs and watch a malfunction and a")
    print("miscalibration behave differently for reasons you can see in one")
    print("equation. Pure Python standard library: nothing to install.")
    print()
    print("Run a command, optionally with a preset and knob overrides:")
    print()
    print("    python allocator_toy.py <command> [--preset NAME] [--knob VALUE] [--plot]")
    print()
    print("Good first runs:")
    print("    python allocator_toy.py demo                 # the whole contrast, narrated")
    print("    python allocator_toy.py fp --beta 8          # the loop folds into two arms")
    print("    python allocator_toy.py series --preset bipolar")
    print("    python allocator_toy.py <command> -h         # full help for one command")
    print()

    print(line)
    print("THE ONE UPDATE RULE  (every command is this, run with different knobs)")
    print(line)
    print()
    print("  dg_i/dt = ( -g_i + S( beta*(g_i-0.5) + I - ka*(a-0.5)")
    print("                        + c*(mean(g)-g_i) + noise_i ) ) / tau_g")
    print("  da/dt   = ( mean(g) - a ) / tau_a     # slow; only the oscillator uses it")
    print()
    print("  g   the allocator's net gain on relevance, in (0,1). This is the one")
    print("      moving part. high g = flooding arm (grips too hard, world too loud);")
    print("      low g = collapse arm (lets go, world goes flat). The two arms are")
    print("      two readings of one variable, not two faults.")
    print("  S   the logistic squash. Its slope at the center is 0.25, which is why")
    print("      beta=4 (where beta*0.25 = 1) is the tipping point.")
    print("  a   'the bar': the relevance level the homeostat demands before it admits")
    print("      a bid, a slow lagging average of g. It only bites when ka > 0. The")
    print("      homeostat opposes the self-reinforcement, so the effective gain is")
    print("      beta-ka: it keeps a single euthymic resting state but can lose its")
    print("      damping and orbit it (the Hopf behind bipolar).")
    print("  i   the channel index: 1 channel by default, 12 for `integration`.")
    print()

    print(line)
    print("THE KNOBS  (each stands for a named setting in the paper)")
    print(line)
    print()
    fmt = "  %-8s default %-5s %s"
    print(fmt % ("--beta", _num(d.beta),
                 "SELF-REINFORCEMENT / loop gain, the fold engine. beta<4:"))
    print("                         one resting state, the output slides. beta>4: with")
    print("                         the homeostat off the loop folds into two basins.")
    print(fmt % ("--I", _num(d.I),
                 "external drive: stress, a salient input, a dopaminergic"))
    print("                         fluctuation. Shifts the contest one way or other.")
    print(fmt % ("--ka", _num(d.ka),
                 "HOMEOSTAT strength (sets the bar a). It opposes the loop,"))
    print("                         so effective gain = beta-ka keeps one euthymic point;")
    print("                         past its HOPF that point orbits: the bipolar swing.")
    print(fmt % ("--c", _num(d.c),
                 "INTEGRATING gain / coupling across channels. High c keeps"))
    print("                         the field one coherent thing (bipolar stays one field);")
    print("                         low c lets the channels fall into separate basins")
    print("                         (the integrating gain's FOLD: schizophrenia).")
    print(fmt % ("--k", _num(d.k),
                 "DISCOUNT steepness (the ADHD target). Used by `profile`."))
    print("                         Steep k makes the immediate reward outrank the")
    print("                         delayed one: weight piled on now, starved from later.")
    print(fmt % ("--lam", _num(d.lam),
                 "FLEXIBILITY (the autism target). Used by `profile`. Low"))
    print("                         lam = a gain that is stuck and will not track the")
    print("                         volatility of the context: too high here, too low there.")
    print(fmt % ("--adapt", "1",
                 "engage the slow variable a (1 on, 0 frozen at 0.5). Turn"))
    print("                         it off to see a folded loop snap instead of cycle.")
    print()

    print(line)
    print("NUMERICAL SETTINGS  (the simulation, not the hypothesis)")
    print(line)
    print()
    print(fmt % ("--noise", _num(d.noise),
                 "noise amplitude inside the squash. series and"))
    print("                         integration set their own when you do not pass it.")
    print(fmt % ("--seed", _num(d.seed), "random seed, so runs are reproducible."))
    print(fmt % ("--dt", _num(d.dt), "integration time step (Euler)."))
    print(fmt % ("--plot", "off",
                 "also write SVG plots to out/ (any browser opens"))
    print("                         them; no libraries). The ASCII output always prints.")
    print()
    print("  tau_g=%s and tau_a=%s, the fast and slow timescales, are fixed in the file."
          % (_num(d.tau_g), _num(d.tau_a)))
    print()

    print(line)
    print("THE PRESETS  (the four conditions, plus a baseline)")
    print(line)
    print()
    print("  baseline       beta=2                monostable; slides, recovers fast")
    print("  schizophrenia  beta=8, c=0.2         folded loop, integration failed;")
    print("                                       fragments, no return")
    print("  bipolar        beta=8, c=3, ka=6     folded loop, integration intact;")
    print("                                       slow coherent oscillation")
    print("  adhd           beta=2, k=0.95        monostable, steep target;")
    print("                                       two-armed over reward delay")
    print("  autism         beta=2, lam=0.1       monostable, stuck target;")
    print("                                       two-armed over volatility")
    print()
    print("  A preset just sets some knobs; any of them can be overridden on top,")
    print("  so you can mix faults (e.g. a miscalibrated target on an unstable loop).")
    print()

    print(line)
    print("THE COMMANDS  (each reproduces a signature from the paper)")
    print(line)
    print()
    print("  app           a browser UI with sliders for every knob (no installs)")
    print("  demo          the whole contrast, narrated over real runs")
    print("  guide         this page")
    print("  fp            stable resting states (two arms appear past beta=4)")
    print("  sweep         reversible drive sweep: hysteresis if the loop has folded")
    print("  recover       critical slowing: recovery time and autocorrelation vs beta")
    print("  series        time series of the field for a preset")
    print("  integration   12 channels: one coherent field, or fragmented basins")
    print("  profile       the miscalibrations: a fixed two-armed curve, never switches")
    print()
    print("MALFUNCTION  = a slow control loses stability. The integrating gain folds")
    print("               (schizophrenia: fragments); the homeostat crosses a Hopf")
    print("               (bipolar: orbits euthymia). Either way the output moves.")
    print("MISCALIBRATION = both controls intact, a target (k or lam) set oddly; the")
    print("               output holds a fixed two-armed offset and never switches.")
    print()
    print("Both bifurcations slow near the edge (recover), but a fold slows monotonically")
    print("and a Hopf rings, which says which tip is coming. The established, fragmented")
    print("schizophrenic state is chaos rather than a fold, so it does not slow at all.")
    print()
    print("Output is ASCII sparklines and heatmaps by default, so it runs in a bare")
    print("terminal. Nothing to install: pure standard library, and --plot writes SVG.")
    print()
    print("Prefer sliders? 'python allocator_toy.py app' opens a browser UI.")


# ----------------------------------------------------------------------------
# Browser UI
# ----------------------------------------------------------------------------
#
# The UI is docs/index.html: a single self-contained page that runs the model
# in the browser (a faithful JS port of the update rule above), with a slider
# for every knob. The same file is what GitHub Pages serves, so the hosted site
# and the local `app` command are the identical page. The `app` command below
# just serves that file from the standard-library http.server -- nothing to
# install, and no server-side computation.

def _page_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "index.html")


def cmd_app(args):
    """Serve the browser UI (docs/index.html) on localhost.

    The page runs the whole model client-side, so this is just a static file
    server for local use; the same page is what GitHub Pages hosts. Nothing to
    install. Open the printed URL, or pass --no-browser and visit it yourself."""
    path = _page_path()
    if not os.path.exists(path):
        print("could not find " + path)
        print("the UI lives at docs/index.html next to this script; open that")
        print("file directly in a browser, or keep it beside allocator_toy.py.")
        return
    with open(path, "rb") as f:
        page = f.read()

    class _UIHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass  # keep the terminal quiet

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

    host = "127.0.0.1"
    start = args.port or 8000
    httpd = None
    for port in range(start, start + 20):
        try:
            httpd = http.server.ThreadingHTTPServer((host, port), _UIHandler)
            break
        except OSError:
            continue
    if httpd is None:
        print("could not bind a port in %d..%d" % (start, start + 19))
        return
    url = "http://%s:%d/" % (host, port)
    print("Allocator UI serving at " + url)
    print("(the same page also works opened straight from docs/index.html)")
    print("Open it in a browser; press Ctrl-C to stop.")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="allocator_toy.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Allocator toy model: one update rule, two kinds of fault.",
        epilog="Run 'allocator_toy.py guide' for how-to-use and a description of\n"
               "every variable, or '<command> -h' for help on one command.")
    sub = parser.add_subparsers(dest="command", metavar="command")

    def add_common(sp):
        sp.add_argument("--preset", choices=list(PRESETS.keys()),
                        help="one of the four conditions, plus baseline")
        sp.add_argument("--beta", type=float,
                        help="stability setting / loop gain (fold at beta=4)")
        sp.add_argument("--I", type=float, help="external drive (stress, salient input)")
        sp.add_argument("--ka", type=float,
                        help="strength of slow adaptation (ka>4 oscillates a folded loop)")
        sp.add_argument("--c", type=float,
                        help="integration coupling across channels (high coheres, low fragments)")
        sp.add_argument("--k", type=float, help="temporal discount steepness (ADHD target)")
        sp.add_argument("--lam", type=float, help="flexibility (autism target)")
        sp.add_argument("--adapt", type=int, choices=(0, 1),
                        help="engage the slow variable a (1 on, 0 frozen; default on)")
        sp.add_argument("--noise", type=float, help="noise amplitude inside the squash")
        sp.add_argument("--seed", type=int, help="random seed")
        sp.add_argument("--dt", type=float, help="integration step")
        sp.add_argument("--plot", action="store_true",
                        help="also write self-contained SVG plots to out/")

    for name, fn in (("demo", cmd_demo), ("guide", cmd_guide), ("fp", cmd_fp),
                     ("sweep", cmd_sweep), ("recover", cmd_recover),
                     ("series", cmd_series), ("integration", cmd_integration),
                     ("profile", cmd_profile)):
        doc = fn.__doc__ or name
        sp = sub.add_parser(name, help=doc.splitlines()[0],
                            description=doc,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
        add_common(sp)
        sp.set_defaults(func=fn)

    # `app` takes server options instead of the model knobs (those are sliders).
    app_sp = sub.add_parser("app", help=cmd_app.__doc__.splitlines()[0],
                            description=cmd_app.__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
    app_sp.add_argument("--port", type=int, default=None,
                        help="port to serve on (default 8000; hunts upward if busy)")
    app_sp.add_argument("--no-browser", action="store_true",
                        help="do not try to open a browser automatically")
    app_sp.set_defaults(func=cmd_app)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # Bare invocation: narrate the contrast, then point at the guide.
        cmd_demo(argparse.Namespace(plot=False))
        print()
        print("New here? Run 'python allocator_toy.py guide' for how to use this")
        print("and what every variable means.")
        return
    args.func(args)


if __name__ == "__main__":
    main()
