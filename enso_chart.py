#!/usr/bin/env python3
"""
Two-panel ENSO chart from a CPC ascii index file.

Usage
-----
    python3 enso_chart.py --data RONI.ascii.txt --index RONI --out roni.png
    python3 enso_chart.py --data oni.ascii.txt  --index ONI  --out oni.png --top 7

Data (fetch fresh each time; do NOT scrape the web tables, they serve stale
cached copies -- see NOTES.md):
    RONI  https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt
    ONI   https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

Both files are whitespace-delimited with a one-line header. The anomaly is
always the LAST column; RONI has 3 columns, ONI has 4 (TOTAL then ANOM).

Event selection: --threshold T keeps ENSO years whose peak reaches T (default
2.0); --top N instead keeps the N strongest. Threshold is applied to the
tenths-rounded series, matching the published tables.
"""

import argparse
from decimal import Decimal, ROUND_FLOOR

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
           "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
SIDX = {s: i for i, s in enumerate(SEASONS)}
# ENSO year: MAM of the onset year through FMA of the following year
ORDER = [(0, i) for i in range(3, 12)] + [(1, i) for i in range(0, 3)]
XLAB = [SEASONS[i] for _, i in ORDER]


def tenths(x):
    """Round half toward +inf -- this is what reproduces CPC's published
    tables (-0.75 -> -0.7, 0.65 -> 0.7)."""
    d = (Decimal(str(x)) * 10 + Decimal("0.5")).to_integral_value(ROUND_FLOOR)
    return float(d / 10)


def load(path):
    """Parse a CPC ascii index file -> ({year: [12 vals or None]}, same rounded)."""
    raw = {}
    for line in open(path):
        p = line.split()
        if len(p) < 3 or p[0] not in SIDX:
            continue                      # header or blank
        raw.setdefault(int(p[1]), [None] * 12)[SIDX[p[0]]] = float(p[-1])
    if not raw:
        raise SystemExit(f"no data parsed from {path} -- wrong file?")
    rnd = {y: [None if v is None else tenths(v) for v in vs]
           for y, vs in raw.items()}
    return raw, rnd


def enso_year(d, y0):
    return [d[y0 + o][i] if y0 + o in d else None for o, i in ORDER]


def build(args):
    raw, data = load(args.data)
    years = sorted(data)
    cur = args.current or years[-1]

    xs, ys = [], []
    for y in years:
        for i, v in enumerate(data[y]):
            if v is not None:
                xs.append(y + i / 12.0)
                ys.append(v)
    xs, ys = np.array(xs), np.array(ys)

    peaks_r, peaks_h = {}, {}
    for y in years:
        if y == cur:
            continue
        a = [v for v in enso_year(data, y) if v is not None]
        b = [v for v in enso_year(raw, y) if v is not None]
        if a:
            peaks_r[y], peaks_h[y] = max(a), max(b)

    if args.top:
        events = sorted(sorted(peaks_h, key=lambda y: -peaks_h[y])[:args.top])
        rule = f"the {args.top} strongest by peak {args.index}"
    else:
        events = sorted(y for y in peaks_r if peaks_r[y] >= args.threshold)
        rule = f"peak {args.index} \u2265 +{args.threshold:.1f} \u00b0C over the ENSO year"
    if not events:
        raise SystemExit("no events selected -- loosen --threshold or use --top")
    print("events:", [(y, peaks_h[y]) for y in events])

    cmap = plt.get_cmap("YlOrRd")
    n = max(len(events) - 1, 1)
    col = {y: cmap(0.35 + 0.60 * k / n) for k, y in enumerate(events)}
    lab = {y: f"{y}\u2013{str(y+1)[2:]}" for y in events}
    unit = f"{args.index} (\u00b0C)"

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#444444"})
    fig, (axA, axB) = plt.subplots(
        2, 1, figsize=(14, 10.5),
        gridspec_kw={"height_ratios": [1.05, 1.0], "hspace": 0.30})

    # ---- Panel A: full monthly series ----
    axA.axhspan(-0.5, 0.5, color="#f4f4f4", zorder=0)
    axA.axvspan(cur - 1 / 24, xs.max() + 1 / 12, color="#d9d9d9",
                alpha=0.65, zorder=0.5)
    axA.fill_between(xs, 0.5, ys, where=ys > 0.5, interpolate=True,
                     color="#c0392b", alpha=0.85, lw=0, zorder=2)
    axA.fill_between(xs, -0.5, ys, where=ys < -0.5, interpolate=True,
                     color="#2471a3", alpha=0.85, lw=0, zorder=2)
    axA.plot(xs, ys, color="#1a1a1a", lw=0.7, zorder=3)

    m = xs >= cur
    axA.plot(xs[m], ys[m], color="black", lw=2.6, zorder=6, solid_capstyle="round")
    axA.plot(xs[m], ys[m], "o", color="black", ms=3.4, zorder=7)

    for lv, st in ((0.0, "-"), (0.5, "--"), (-0.5, "--")):
        axA.axhline(lv, color="#555555", lw=0.9 if lv == 0 else 0.8, ls=st, zorder=4)

    for y in events:
        seq = enso_year(data, y)
        k = int(np.nanargmax([np.nan if v is None else v for v in seq]))
        off, i = ORDER[k]
        px, py = (y + off) + i / 12.0, seq[k]
        axA.plot(px, py + 0.22, marker="v", ms=7, color=col[y],
                 mec="#333333", mew=0.6, zorder=8, clip_on=False)
        axA.text(px, py + 0.42, lab[y], rotation=90, ha="center", va="bottom",
                 fontsize=8, color="#222222", zorder=8)

    axA.set_xlim(years[0] - 0.4, xs.max() + 0.6)
    axA.set_ylim(-2.4, 3.55)
    axA.set_yticks(np.arange(-2, 3.5, 0.5))
    axA.set_xticks(np.arange(years[0], years[-1] + 6, 5))
    axA.tick_params(axis="x", labelsize=8)
    axA.set_ylabel(unit)
    axA.set_title(f"A  \u2014  {args.title}, monthly, {years[0]}\u2013{cur}",
                  loc="left", fontsize=11, fontweight="bold", pad=8)
    axA.text(cur + 0.30, 3.40, str(cur), fontsize=8, color="#333333",
             ha="center", va="center")
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)
    axA.legend(handles=[
        Line2D([], [], color="#c0392b", lw=7, alpha=0.85, label="El Ni\u00f1o (> +0.5)"),
        Line2D([], [], color="#2471a3", lw=7, alpha=0.85, label="La Ni\u00f1a (< \u22120.5)"),
        Line2D([], [], color="black", lw=2.6, marker="o", ms=4, label=str(cur)),
        Line2D([], [], color=col[events[-1]], marker="v", ls="none", ms=7,
               mec="#333", label="highlighted events"),
    ], loc="lower left", bbox_to_anchor=(0.005, 0.02), frameon=True,
        facecolor="white", edgecolor="none", framealpha=0.92,
        fontsize=8, ncol=4, handletextpad=0.6, columnspacing=1.6)

    # ---- Panel B: ENSO-year overlay ----
    X = np.arange(12)
    axB.axhspan(-0.5, 0.5, color="#f4f4f4", zorder=0)
    for y in years:
        if y in events or y == cur:
            continue
        seq = enso_year(data, y)
        xx = [X[i] for i, v in enumerate(seq) if v is not None]
        yy = [v for v in seq if v is not None]
        if len(yy) > 1:
            axB.plot(xx, yy, color="#b8b8b8", lw=0.7, alpha=0.65, zorder=1)
    for lv, st in ((0.0, "-"), (0.5, "--"), (-0.5, "--")):
        axB.axhline(lv, color="#555555", lw=0.9 if lv == 0 else 0.8, ls=st, zorder=2)
    axB.axvline(8.5, color="#333333", lw=1.0, ls="--", zorder=2)
    axB.text(8.5, 3.28, "boreal winter", fontsize=8, color="#333333",
             ha="center", va="bottom", bbox=dict(fc="white", ec="none", pad=1.5))

    anchors = []
    for y in events:
        seq = enso_year(data, y)
        axB.plot(X, seq, color=col[y], lw=2.0, zorder=4, solid_capstyle="round")
        anchors.append([seq[-1], seq[-1], lab[y], col[y], 11])

    seq = enso_year(data, cur)
    xx = [X[i] for i, v in enumerate(seq) if v is not None]
    yy = [v for v in seq if v is not None]
    axB.plot(xx, yy, color="black", lw=3.0, zorder=6, solid_capstyle="round")
    axB.plot(xx, yy, "o", color="black", ms=5, zorder=7)
    if len(yy) == 12:                       # current year now runs to FMA
        anchors.append([yy[-1], yy[-1], f"{cur}\u2013{str(cur+1)[2:]}", "black", 11])
    else:
        axB.annotate(f"{cur}\u2013{str(cur+1)[2:]}", xy=(xx[-1], yy[-1]),
                     xytext=(xx[-1] + 0.18, yy[-1] - 0.30), fontsize=9.5,
                     color="black", fontweight="bold", va="center", ha="left",
                     zorder=8)

    MIN = 0.175                             # vertical de-overlap of edge labels
    anchors.sort(key=lambda a: a[0])
    for _ in range(400):
        moved = False
        for i in range(len(anchors) - 1):
            gap = anchors[i + 1][1] - anchors[i][1]
            if gap < MIN:
                sh = (MIN - gap) / 2
                anchors[i][1] -= sh
                anchors[i + 1][1] += sh
                moved = True
        if not moved:
            break
    for y0, y1, t, c, xa in anchors:
        axB.annotate(t, xy=(xa, y0), xytext=(11.55, y1), fontsize=8.5, color=c,
                     va="center", ha="left", annotation_clip=False, zorder=8,
                     fontweight="bold" if t.startswith(str(cur)) else "normal",
                     arrowprops=dict(arrowstyle="-", color=c, lw=0.7,
                                     shrinkA=1, shrinkB=1,
                                     connectionstyle="arc3,rad=0"))

    axB.set_xlim(-0.35, 11.4)
    axB.set_ylim(-2.4, 3.3)
    axB.set_xticks(X)
    axB.set_xticklabels(XLAB)
    axB.set_yticks(np.arange(-2, 3.5, 0.5))
    axB.set_ylabel(unit)
    axB.set_xlabel("season of the ENSO year "
                   "(MAM of onset year \u2192 FMA following)")
    axB.set_title(f"B  \u2014  ENSO years overlaid, {years[0]}\u2013"
                  f"{str(years[0]+1)[2:]} to {cur-1}\u2013{str(cur)[2:]}, "
                  "aligned on the winter peak",
                  loc="left", fontsize=11, fontweight="bold", pad=8)
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)

    fig.text(0.008, 0.026, f"Data: {args.source} CPC may revise the most recent "
             "values for up to two months.", fontsize=7.5, color="#555555")
    fig.text(0.008, 0.008, f"Highlighted years: {rule}.",
             fontsize=7.5, color="#555555")

    fig.subplots_adjust(left=0.055, right=0.935, top=0.955, bottom=0.080)
    fig.savefig(args.out, dpi=200, facecolor="white")
    print("saved", args.out)

    # a few numbers worth checking each update
    jja = sorted(((raw[y][6], y) for y in years if raw[y][6] is not None),
                 reverse=True)[:6]
    print("top JJA:", jja)
    ly, li = max((y, i) for y in years
                 for i, v in enumerate(raw[y]) if v is not None)
    print(f"latest season: {SEASONS[li]} {ly} = {raw[ly][li]:+.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--index", default="RONI")
    ap.add_argument("--out", default="chart.png")
    ap.add_argument("--threshold", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=None,
                    help="use the N strongest instead of a threshold")
    ap.add_argument("--current", type=int, default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--source", default=None)
    a = ap.parse_args()
    if a.title is None:
        a.title = ("Relative Oceanic Ni\u00f1o Index (ERSSTv6)"
                   if a.index.upper() == "RONI"
                   else "Oceanic Ni\u00f1o Index (ERSSTv6)")
    if a.source is None:
        a.source = (f"NOAA CPC {a.index}, ERSSTv6 "
                    f"({'RONI.ascii.txt, 1991-2020 base' if a.index.upper() == 'RONI' else 'oni.ascii.txt, centered 30-year base periods'}), "
                    "rounded to tenths as published.")
    build(a)
