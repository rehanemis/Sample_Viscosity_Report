"""viscosity.py - ASTM D341 maths plus chart and report drawing (Matplotlib).

Chart scales (ASTM D341):
    X = log10(T + 273.15)            T in degrees Celsius
    Y = log10(log10(v + 0.7))        v in centistokes (cSt)
On these scales the viscosity-temperature line of a mineral oil is straight:
    Y = A - B * X
A and B are found from the viscosities at 40 C and 100 C.
"""
import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

BLUE = "#0B4A8F"
ORANGE = "#F28C1B"
RED = "#D62828"
LIGHT = "#EAF1FA"
EDGE = "#9DB4CE"

K = 273.15   # kelvin offset (ASTM D341)
C0 = 0.7     # viscosity offset (ASTM D341)

# Chart bounds, copied from the reference chart: -20..165 C and 4..100,000 cSt
T_MIN, T_MAX = -20.0, 165.0
V_MIN, V_MAX = 4.0, 100000.0

MAJOR_V = [4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 400, 500,
           1000, 2000, 3000, 5000, 10000, 20000, 50000, 100000]


def _minor_v():
    out = []
    for d in (1, 10, 100, 1000, 10000):
        m = 1.0
        while m < 10:
            v = m * d
            if V_MIN <= v <= V_MAX and v not in MAJOR_V and v not in out:
                out.append(v)
            m += 0.5
    return sorted(out)


MINOR_V = _minor_v()
MAJOR_T = list(range(-20, 161, 10))
MINOR_T = list(range(-15, 166, 10))


def fx(t_c):
    return np.log10(np.asarray(t_c, dtype=float) + K)


def fy(v):
    return np.log10(np.log10(np.asarray(v, dtype=float) + C0))


def check_inputs(v40, v100):
    """Return an error message, or None when the inputs can be used."""
    if v40 is None or v100 is None:
        return "Enter both viscosities."
    if v100 <= 0.3 or v40 <= 0.3:
        return "Viscosities must be greater than 0.3 cSt."
    if v40 <= v100:
        return "The 40 \u00b0C viscosity must be higher than the 100 \u00b0C viscosity."
    return None


def fit_line(v40, v100):
    """Return (A, B) of the ASTM D341 line through the two measured points."""
    w1, w2 = float(fy(v40)), float(fy(v100))
    b = (w1 - w2) / float(fx(100) - fx(40))
    a = w1 + b * float(fx(40))
    return a, b


def viscosity_at(t_c, a, b):
    """Kinematic viscosity (cSt) at temperature t_c (C) from the fitted line."""
    return float(10 ** (10 ** (a - b * fx(t_c))) - C0)


def _fmt_v(v):
    return f"{v:g}" if v < 10 else f"{int(v)}"


def draw_chart(ax, a, b, v40, v100, ops, label_size=6.5):
    """Draw the ASTM D341 chart on ax. ops = [(name, temperature_C), ...]."""
    x0, x1 = float(fx(T_MIN)), float(fx(T_MAX))
    y0, y1 = float(fy(V_MIN)), float(fy(V_MAX))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)

    for v in MINOR_V:
        ax.hlines(float(fy(v)), x0, x1, colors="#B0B0B0", linewidth=0.4, zorder=1)
    for t in MINOR_T:
        ax.vlines(float(fx(t)), y0, y1, colors="#B0B0B0", linewidth=0.4, zorder=1)
    for v in MAJOR_V:
        ax.hlines(float(fy(v)), x0, x1, colors="#262626", linewidth=0.9, zorder=2)
    for t in MAJOR_T:
        ax.vlines(float(fx(t)), y0, y1, colors="#262626", linewidth=0.9, zorder=2)

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_linewidth(1.3)

    kw = dict(fontsize=label_size, annotation_clip=False)
    for v in MAJOR_V:
        ax.annotate(_fmt_v(v), (x0, float(fy(v))), xytext=(-4, 0),
                    textcoords="offset points", ha="right", va="center", **kw)
        ax.annotate(_fmt_v(v), (x1, float(fy(v))), xytext=(4, 0),
                    textcoords="offset points", ha="left", va="center", **kw)
    for t in MAJOR_T:
        ax.annotate(str(t), (float(fx(t)), y1), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", **kw)
    for f in range(0, 321, 20):
        ax.annotate(str(f), (float(fx((f - 32) / 1.8)), y0), xytext=(0, -3),
                    textcoords="offset points", ha="center", va="top", **kw)

    title_kw = dict(transform=ax.transAxes, fontsize=7.5, fontweight="bold",
                    ha="center", va="center")
    ax.text(0.5, 1.055, "TEMPERATURE, DEGREES CELSIUS", **title_kw)
    ax.text(0.5, -0.075, "TEMPERATURE, DEGREES FAHRENHEIT", **title_kw)
    ax.text(-0.05, 0.5, "KINEMATIC VISCOSITY, CENTISTOKES", rotation=90, **title_kw)
    ax.text(1.05, 0.5, "KINEMATIC VISCOSITY, CENTISTOKES", rotation=90, **title_kw)

    # the oil: straight line on these scales (Matplotlib clips it to the chart)
    ax.plot([x0, x1], [a - b * x0, a - b * x1], color=RED, linewidth=2.4,
            label="Your oil (ASTM D341 line)", zorder=5)
    ax.scatter([float(fx(40)), float(fx(100))], [float(fy(v40)), float(fy(v100))],
               s=55, color=RED, edgecolor="white", linewidth=0.8, zorder=6,
               label="Measured at 40 \u00b0C and 100 \u00b0C")

    first = True
    for name, t in ops:
        if t is None or not (T_MIN <= t <= T_MAX):
            continue
        v = viscosity_at(t, a, b)
        if not (V_MIN <= v <= V_MAX):
            continue
        ax.scatter([float(fx(t))], [float(fy(v))], s=70, marker="D", color=ORANGE,
                   edgecolor="black", linewidth=0.8, zorder=7,
                   label="Operating min / normal / max" if first else None)
        first = False
        ax.annotate(f"{v:,.1f} cSt @ {t:g} \u00b0C", (float(fx(t)), float(fy(v))),
                    xytext=(8, 7), textcoords="offset points", fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ORANGE, lw=0.8),
                    zorder=8)

    ax.legend(loc="upper right", fontsize=8, framealpha=0.95, edgecolor="#444444",
              borderaxespad=1.0)


def chart_figure(a, b, v40, v100, ops, subtitle=""):
    """Chart-only picture (11 x 7 in), meant for the image box of the PDF form."""
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_axes([0.075, 0.09, 0.85, 0.80])
    draw_chart(ax, a, b, v40, v100, ops)
    fig.text(0.5, 0.965, "VISCOSITY-TEMPERATURE CHART (ASTM D341)", ha="center",
             va="center", fontsize=13, fontweight="bold")
    if subtitle:
        fig.text(0.5, 0.935, subtitle, ha="center", va="center", fontsize=9)
    return fig


def _rect(fig, x, y, w, h, fc, ec="none", lw=0.6):
    fig.add_artist(Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=fc,
                             edgecolor=ec, linewidth=lw))


def _box(fig, x, y_top, w, title, rows, label_frac=0.45, row_h=0.0215):
    _rect(fig, x, y_top - 0.022, w, 0.022, BLUE)
    fig.text(x + 0.006, y_top - 0.011, title, color="white", fontsize=8,
             fontweight="bold", va="center")
    y = y_top - 0.022
    for label, value in rows:
        y -= row_h
        _rect(fig, x, y, w * label_frac, row_h, LIGHT, EDGE)
        _rect(fig, x + w * label_frac, y, w * (1 - label_frac), row_h, "white", EDGE)
        fig.text(x + 0.005, y + row_h / 2, label, fontsize=7.5, va="center")
        fig.text(x + w * label_frac + 0.005, y + row_h / 2, value, fontsize=7.5,
                 va="center")


def report_figure(info, a, b, ops):
    """Full A4-landscape report page: header, details, operating table, chart."""
    fig = plt.figure(figsize=(11.69, 8.27))
    _rect(fig, 0, 0.915, 1, 0.085, BLUE)
    _rect(fig, 0, 0.905, 1, 0.010, ORANGE)
    fig.text(0.03, 0.963, "VISCOSITY TEMPERATURE ANALYSIS", color="white", fontsize=18,
             fontweight="bold", va="center")
    fig.text(0.03, 0.929, "LUBRICANT VISCOSITY CHARACTERISTICS", color="white",
             fontsize=8, va="center")

    top = 0.885
    _box(fig, 0.03, top, 0.30, "LUBRICANT DETAILS", [
        ("Lubricant", info.get("lubricant", "")),
        ("ISO VG", info.get("iso_vg", "")),
        ("Viscosity Index (VI)", info.get("vi", "")),
        ("Viscosity at 40 \u00b0C (cSt)", f"{info['v40']:g}"),
        ("Viscosity at 100 \u00b0C (cSt)", f"{info['v100']:g}"),
        ("Date Plotted", info.get("date", "")),
    ])
    _box(fig, 0.35, top, 0.22, "CALCULATION (ASTM D341)", [
        ("Slope B", f"{b:.4f}"),
        ("Constant A", f"{a:.4f}"),
        ("Kelvin offset", f"{K}"),
        ("Viscosity offset", f"{C0}"),
    ], label_frac=0.55)

    # operating conditions table
    x, w = 0.59, 0.38
    _rect(fig, x, top - 0.022, w, 0.022, BLUE)
    fig.text(x + 0.006, top - 0.011, "OPERATING CONDITIONS", color="white",
             fontsize=8, fontweight="bold", va="center")
    cols = [0.40, 0.30, 0.30]
    heads = ["Condition", "Temperature (\u00b0C)", "Viscosity (cSt)"]
    y = top - 0.022 - 0.0215
    cx = x
    for frac, head in zip(cols, heads):
        _rect(fig, cx, y, w * frac, 0.0215, LIGHT, EDGE)
        fig.text(cx + w * frac / 2, y + 0.01075, head, fontsize=7.5, fontweight="bold",
                 ha="center", va="center")
        cx += w * frac
    for name, t in ops:
        y -= 0.0215
        v = viscosity_at(t, a, b) if t is not None else None
        cells = [name, f"{t:g}" if t is not None else "", f"{v:,.1f}" if v else ""]
        cx = x
        for frac, text in zip(cols, cells):
            _rect(fig, cx, y, w * frac, 0.0215, "white", EDGE)
            fig.text(cx + (0.005 if text == name else w * frac / 2), y + 0.01075, text,
                     fontsize=7.5, ha="left" if text == name else "center", va="center")
            cx += w * frac

    ax = fig.add_axes([0.075, 0.095, 0.85, 0.585])
    draw_chart(ax, a, b, info["v40"], info["v100"], ops)

    comments = info.get("comments", "")
    if comments:
        fig.text(0.03, 0.040, "Comments: " + textwrap.shorten(comments, 170),
                 fontsize=7.5, va="center")
    fig.text(0.03, 0.015, "Method: ASTM D341 viscosity-temperature relationship. "
             "Viscosity Index is entered by the user and does not drive the line.",
             fontsize=6.5, color="#595959", va="center")
    return fig


def fig_bytes(fig, fmt="png", dpi=300):
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi)
    plt.close(fig)
    return buf.getvalue()
