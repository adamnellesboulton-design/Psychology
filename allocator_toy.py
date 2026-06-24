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
a is "the bar" of the paper: the level of relevance the regulator demands before
it admits a bid, drifting slowly against whichever state the field is in. The
knobs map to named settings in the paper (see the Params class and README):
beta = stability (loop gain; beta=4 is the fold), I = external drive,
ka = strength of the slow bar a, c = integration coupling across channels,
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
import json
import math
import os
import random
import urllib.parse
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
        self.beta = beta      # stability setting (loop gain)
        self.I = I            # external drive
        self.ka = ka          # strength of the slow bar a (the relevance level demanded)
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


# When the browser UI is driving, plots are collected here as strings instead
# of being written to out/. None means the normal file-writing behavior.
_SVG_SINK = None


def _write_svg(name, parts):
    svg = "\n".join(parts) + "\n</svg>\n"
    if _SVG_SINK is not None:
        _SVG_SINK.append(svg)
        return
    os.makedirs("out", exist_ok=True)
    path = "out/" + name + ".svg"
    with open(path, "w") as f:
        f.write(svg)
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
        grid = linspace(0.0, 1.0, 400)
        curve = [S(p.beta * (g - 0.5)) for g in grid]
        save_svg_lines("fp_beta%s" % _num(p.beta), "fixed points, beta = %s" % _num(p.beta),
                       "g", "update",
                       [("S(beta*(g-0.5))", grid, curve), ("g", grid, grid)],
                       points=[(g, g, st) for g, st in fps])


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
    """Critical slowing down. As beta approaches the fold, recovery from a
    nudge slows without bound and the variance and lag-1 autocorrelation of
    the fluctuations climb. This is the early-warning signature of a fold
    specifically (bipolar disorder, and the onset of psychosis); the
    established, fragmented schizophrenic state is chaos, not a fold, and is
    not expected to slow."""
    p = resolve_params(args)
    betas = [1.0, 2.0, 3.0, 3.5, 3.8, 3.9, 3.95]
    nudge = 0.1
    tol = 0.05 * nudge
    T_max = 600.0

    print("critical slowing down: recovery time, variance, lag-1 autocorrelation")
    print("  beta      return time     variance     AR(1)")
    return_times, variances, ar1s = [], [], []
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
        var = pstdev(x) ** 2
        ar1 = pearson(x[:-1], x[1:])
        variances.append(var)
        ar1s.append(ar1)
        print("  %-8.3g  %10.1f   %10.2e   %6.3f" % (beta, rt, var, ar1))
    print("  return time, variance, and AR(1) all climb as beta -> 4: the fold.")

    if maybe_plot(args):
        save_svg_lines("recover_return", "critical slowing: return time",
                       "beta", "return time", [("return time", betas, return_times)],
                       markers=True)
        save_svg_lines("recover_ar1", "critical slowing: lag-1 autocorrelation",
                       "beta", "AR(1)", [("AR(1)", betas, ar1s)], markers=True)


def cmd_series(args):
    """Time series of the field. A folded oscillator (bipolar) cycles slowly;
    a folded loop without recovery (schizophrenia) sits in a basin."""
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
    if p.ka >= 4 and p.beta > 4 and p.adapt:
        print("  a slow, coherent oscillation: the operating point cycles and returns.")
    elif p.beta > 4:
        print("  it falls into an arm and stays: no stable middle to rest at.")
    else:
        print("  monostable: small wandering around the single resting state.")

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
    print("  a   'the bar': the level of relevance the regulator demands before it")
    print("      admits a bid, a slow lagging average of g. It only bites when ka > 0,")
    print("      and it is what turns a folded loop into an oscillator (bipolar) instead")
    print("      of a stuck snap.")
    print("  i   the channel index: 1 channel by default, 12 for `integration`.")
    print()

    print(line)
    print("THE KNOBS  (each stands for a named setting in the paper)")
    print(line)
    print()
    fmt = "  %-8s default %-5s %s"
    print(fmt % ("--beta", _num(d.beta),
                 "STABILITY setting (loop gain). The master switch for the"))
    print("                         kind of fault. beta<4: one resting state, the")
    print("                         output slides. beta>4: the loop folds into two")
    print("                         arms with an unstable threshold between; it snaps.")
    print(fmt % ("--I", _num(d.I),
                 "external drive: stress, a salient input, a dopaminergic"))
    print("                         fluctuation. Shifts the contest one way or other.")
    print(fmt % ("--ka", _num(d.ka),
                 "strength of the slow bar a (the relevance level demanded)."))
    print("                         With a folded loop, ka>4 makes a relaxation")
    print("                         oscillator (the bar drifts up under the flood until")
    print("                         it tips, then back down): the bipolar mechanism.")
    print(fmt % ("--c", _num(d.c),
                 "INTEGRATION coupling across channels. High c keeps the"))
    print("                         field one coherent thing (bipolar-type); low c")
    print("                         lets channels fall into separate basins")
    print("                         (fragmentation, schizophrenia-type).")
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
    print("MALFUNCTION  = the loop loses stability (raise beta past 4); the output moves.")
    print("MISCALIBRATION = the loop is fine (beta low) but a target (k or lam) is set")
    print("               oddly; the output holds a fixed offset and never switches.")
    print()
    print("Critical slowing (recover) is a fold signature: it belongs to bipolar and to")
    print("the onset of psychosis. The established schizophrenic state is fragmentation")
    print("(integration, low c) -- chaos, not a fold -- so it does not slow.")
    print()
    print("Output is ASCII sparklines and heatmaps by default, so it runs in a bare")
    print("terminal. Nothing to install: pure standard library, and --plot writes SVG.")
    print()
    print("Prefer sliders? 'python allocator_toy.py app' opens a browser UI.")


# ----------------------------------------------------------------------------
# Browser UI (an optional front-end over the same one update rule)
# ----------------------------------------------------------------------------
#
# The `app` command serves a small single-page UI from the standard-library
# http.server: sliders for the knobs, the same SVG plots, and the same ASCII
# narration. No third-party packages, nothing to install; it opens in a browser.

# Map a UI view name to (command function, forced preset for the profile axis).
_VIEWS = {
    "fp": (cmd_fp, None),
    "sweep": (cmd_sweep, None),
    "recover": (cmd_recover, None),
    "series": (cmd_series, None),
    "integration": (cmd_integration, None),
    "profile_adhd": (cmd_profile, "adhd"),
    "profile_autism": (cmd_profile, "autism"),
}


def _run_view(view, params):
    """Run one view with the given knob values. Returns (text, [svg, ...]) by
    capturing what the command prints and the plots it would have saved."""
    import io
    import contextlib

    fn, preset = _VIEWS.get(view, _VIEWS["fp"])
    args = argparse.Namespace(
        preset=preset, plot=True, seed=None, dt=None,
        beta=params.get("beta"), I=params.get("I"), ka=params.get("ka"),
        c=params.get("c"), k=params.get("k"), lam=params.get("lam"),
        noise=params.get("noise"), adapt=params.get("adapt"))

    global _SVG_SINK
    _SVG_SINK = []
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn(args)
        svgs = list(_SVG_SINK)
    finally:
        _SVG_SINK = None
    return buf.getvalue(), svgs


def _run_request(query):
    """Translate a parsed /run query into a model run and a JSON payload."""
    def num(key):
        v = query.get(key, [None])[0]
        return float(v) if v not in (None, "") else None

    view = query.get("view", ["fp"])[0]
    adapt_raw = query.get("adapt", [None])[0]
    adapt = int(adapt_raw) if adapt_raw not in (None, "") else None
    params = dict(beta=num("beta"), I=num("I"), ka=num("ka"), c=num("c"),
                  k=num("k"), lam=num("lam"), noise=num("noise"), adapt=adapt)
    text, svgs = _run_view(view, params)
    return {"text": text, "svgs": svgs}


class _UIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # keep the terminal quiet

    def _send(self, code, body, content_type):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, APP_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/run":
            query = urllib.parse.parse_qs(parsed.query)
            try:
                payload = _run_request(query)
            except Exception as exc:  # a bad knob should not kill the server
                payload = {"text": "error: " + str(exc), "svgs": []}
            self._send(200, json.dumps(payload), "application/json")
            return
        self._send(404, "not found", "text/plain")


def cmd_app(args):
    """Launch a browser UI with a slider for every knob.

    Serves a single self-contained page from the standard library (no installs).
    Move a slider and the model reruns; the plot and the narration update."""
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


# The whole UI is this one ASCII string: HTML, CSS, and vanilla JS. It talks to
# /run and draws the SVG the model returns. Kept dependency-free on purpose.
APP_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Allocator Toy Model</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--ink:#1b1b1f;--muted:#6b6b76;--line:#e4e4ea;--accent:#2563eb;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg);}
header{padding:16px 24px;border-bottom:1px solid var(--line);background:var(--panel);}
header h1{margin:0;font-size:18px;}
header p{margin:4px 0 0;color:var(--muted);font-size:13px;}
main{display:flex;gap:20px;padding:20px;align-items:flex-start;flex-wrap:wrap;}
#controls{flex:0 0 330px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;}
#out{flex:1 1 460px;min-width:360px;}
.group{margin-bottom:18px;}
.group > label{display:block;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;}
.hint{color:var(--muted);font-size:12px;margin:8px 0 0;}
.seg{display:flex;flex-wrap:wrap;gap:6px;}
.seg button{font:inherit;font-size:12px;padding:6px 10px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer;color:var(--ink);}
.seg button:hover{border-color:var(--accent);}
.seg button.active{background:var(--accent);color:#fff;border-color:var(--accent);}
select{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px;font:inherit;background:#fff;}
.slider{margin-bottom:12px;transition:opacity .15s;}
.slider.dim{opacity:.38;}
.slider .row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:2px;}
.slider .name{font-size:12px;}
.slider .val{font-size:12px;color:var(--accent);font-weight:700;font-variant-numeric:tabular-nums;}
input[type=range]{width:100%;accent-color:var(--accent);}
.check{display:flex;align-items:center;gap:8px;font-size:13px;}
#plots{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:14px;min-height:120px;}
#plots svg{max-width:100%;height:auto;display:block;margin:0 auto 6px;}
pre#text{background:#0f1117;color:#d7dae0;border-radius:12px;padding:14px;font-size:12px;line-height:1.4;overflow:auto;white-space:pre;margin:0;}
footer{padding:6px 24px 26px;color:var(--muted);font-size:12px;}
footer code{font-family:ui-monospace,Menlo,Consolas,monospace;}
.loading{opacity:.5;}
</style>
</head>
<body>
<header>
  <h1>Allocator Toy Model</h1>
  <p>One update rule, two kinds of fault. Move a knob and watch.</p>
</header>
<main>
  <section id="controls">
    <div class="group">
      <label>View</label>
      <div id="views" class="seg"></div>
      <p id="viewhint" class="hint"></p>
    </div>
    <div class="group">
      <label for="preset">Preset</label>
      <select id="preset">
        <option value="custom">custom</option>
        <option value="baseline">baseline</option>
        <option value="schizophrenia">schizophrenia (malfunction, fragments)</option>
        <option value="bipolar">bipolar (malfunction, oscillates)</option>
        <option value="adhd">adhd (miscalibration, steep discount)</option>
        <option value="autism">autism (miscalibration, stuck gain)</option>
      </select>
    </div>
    <div class="group">
      <label>Knobs</label>
      <div id="sliders"></div>
      <label class="check"><input type="checkbox" id="adapt" checked> engage slow adaptation (a)</label>
    </div>
  </section>
  <section id="out">
    <div id="plots"></div>
    <pre id="text">loading...</pre>
  </section>
</main>
<footer>
  <code>dg/dt = ( -g + S( beta*(g-0.5) + I - ka*(a-0.5) + c*(mean(g)-g) + noise ) ) / tau_g</code><br>
  S is the logistic squash. beta=4 is the fold. Malfunction = raise beta past 4 (it moves);
  miscalibration = set k or lam oddly with beta low (it holds a fixed offset).
</footer>
<script>
var KNOBS = [
  {key:"beta", name:"beta - stability (fold at 4)", min:0, max:10, step:0.05},
  {key:"I", name:"I - external drive", min:-4, max:4, step:0.05},
  {key:"ka", name:"ka - slow adaptation strength", min:0, max:8, step:0.1},
  {key:"c", name:"c - integration coupling", min:0, max:4, step:0.05},
  {key:"k", name:"k - discount steepness (ADHD)", min:0.05, max:1.5, step:0.01},
  {key:"lam", name:"lam - flexibility (autism)", min:0, max:1, step:0.01},
  {key:"noise", name:"noise", min:0, max:0.2, step:0.005}
];
var DEFAULTS = {beta:2, I:0, ka:0, c:1, k:0.2, lam:1, noise:0, adapt:1};
var PRESETS = {
  baseline:{beta:2}, schizophrenia:{beta:8, c:0.2, ka:0},
  bipolar:{beta:8, c:3, ka:6}, adhd:{beta:2, k:0.95}, autism:{beta:2, lam:0.1}
};
var VIEWS = [
  {key:"series", label:"series", uses:["beta","ka","c","noise"], hint:"Time series of the field. Try the bipolar preset for the oscillation."},
  {key:"fp", label:"fixed points", uses:["beta"], hint:"Resting states. Two arms appear once beta passes 4."},
  {key:"sweep", label:"sweep", uses:["beta"], hint:"Reversible drive sweep. A folded loop takes a different path up than down."},
  {key:"recover", label:"recover", uses:[], hint:"Sweeps beta itself: recovery time blows up nearing the fold."},
  {key:"integration", label:"integration", uses:["beta","c","noise"], hint:"12 channels. High c stays one field; low c fragments."},
  {key:"profile_adhd", label:"ADHD profile", uses:["k"], hint:"Weight vs reward delay: a fixed two-armed curve."},
  {key:"profile_autism", label:"autism profile", uses:["lam"], hint:"Gain mismatch vs volatility: a fixed two-armed curve."}
];

var state = Object.assign({}, DEFAULTS);
var view = "series";
var timer = null;

function el(id){ return document.getElementById(id); }

function buildViews(){
  var box = el("views");
  VIEWS.forEach(function(v){
    var b = document.createElement("button");
    b.textContent = v.label;
    b.onclick = function(){ view = v.key; markViews(); applyDim(); run(); };
    b.dataset.key = v.key;
    box.appendChild(b);
  });
}
function markViews(){
  var defn = currentView();
  el("viewhint").textContent = defn.hint;
  Array.prototype.forEach.call(el("views").children, function(b){
    b.classList.toggle("active", b.dataset.key === view);
  });
}
function currentView(){
  for(var i=0;i<VIEWS.length;i++){ if(VIEWS[i].key===view) return VIEWS[i]; }
  return VIEWS[0];
}

function buildSliders(){
  var box = el("sliders");
  KNOBS.forEach(function(kn){
    var wrap = document.createElement("div");
    wrap.className = "slider";
    wrap.dataset.key = kn.key;
    var row = document.createElement("div"); row.className = "row";
    var nm = document.createElement("span"); nm.className = "name"; nm.textContent = kn.name;
    var val = document.createElement("span"); val.className = "val"; val.id = "v_"+kn.key;
    row.appendChild(nm); row.appendChild(val);
    var inp = document.createElement("input");
    inp.type = "range"; inp.min = kn.min; inp.max = kn.max; inp.step = kn.step; inp.id = "s_"+kn.key;
    inp.oninput = function(){
      state[kn.key] = parseFloat(inp.value);
      val.textContent = (+state[kn.key]).toFixed(2);
      el("preset").value = "custom";
      schedule();
    };
    wrap.appendChild(row); wrap.appendChild(inp);
    box.appendChild(wrap);
  });
}

function syncSliders(){
  KNOBS.forEach(function(kn){
    el("s_"+kn.key).value = state[kn.key];
    el("v_"+kn.key).textContent = (+state[kn.key]).toFixed(2);
  });
  el("adapt").checked = !!state.adapt;
}

function applyDim(){
  var uses = currentView().uses;
  Array.prototype.forEach.call(el("sliders").children, function(w){
    var on = uses.length === 0 ? false : uses.indexOf(w.dataset.key) >= 0;
    w.classList.toggle("dim", !on);
  });
}

function applyPreset(name){
  state = Object.assign({}, DEFAULTS);
  if(PRESETS[name]) Object.assign(state, PRESETS[name]);
  state.adapt = el("adapt").checked ? 1 : 0;
  syncSliders();
}

function schedule(){
  if(timer) clearTimeout(timer);
  timer = setTimeout(run, 110);
}

function run(){
  var q = new URLSearchParams();
  q.set("view", view);
  KNOBS.forEach(function(kn){ q.set(kn.key, state[kn.key]); });
  q.set("adapt", el("adapt").checked ? 1 : 0);
  el("text").classList.add("loading");
  fetch("/run?" + q.toString()).then(function(r){ return r.json(); }).then(function(d){
    el("plots").innerHTML = (d.svgs && d.svgs.length) ? d.svgs.join("") : "";
    el("text").textContent = d.text || "";
    el("text").classList.remove("loading");
  }).catch(function(e){
    el("text").textContent = "request failed: " + e;
    el("text").classList.remove("loading");
  });
}

el("preset").onchange = function(){
  if(this.value !== "custom") applyPreset(this.value);
  run();
};
el("adapt").onchange = function(){ state.adapt = this.checked ? 1 : 0; schedule(); };

buildViews();
buildSliders();
applyPreset("bipolar");
el("preset").value = "bipolar";
markViews();
applyDim();
run();
</script>
</body>
</html>
"""


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
