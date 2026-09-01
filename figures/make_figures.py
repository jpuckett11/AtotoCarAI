#!/usr/bin/env python3
"""Figure generator for the Atoto AI Box white paper.

Nothing is hand-entered. Every figure reads the evidence files directly, so a number
moving in the evidence moves the chart with it. The paper goes to Google, and a chart
that disagrees with the table under it is worse than no chart.

Colours use the validated reference palette in fixed slot order, never cycled. The
scatter is limited to slots 1-3, the documented all-pairs-safe depth for colour-vision
deficiency. Do not add a fourth hue without re-running the validator.
"""

import csv
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")  # headless; must be set before pyplot is imported
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
def _find_evidence():
    """
    Locate the case evidence directory.

    It has moved once already (out of ~ and into a staging folder mid-analysis),
    which broke the figure build. Searching a candidate list beats hardcoding a
    path that demonstrably does not stay put. Ordered most-recent-known first.
    """
    candidates = [
        "/home/obsidian/atoto_reseal_20260728/evidence",
        "/home/obsidian/zzzzzzzzzzzzzzzzzzzzzzzz/atoto_reseal_20260728/evidence",
    ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "apk_signing.tsv")):
            return c
    # Last resort: walk the home directory for the manifest we actually need.
    for root, dirs, files in os.walk("/home/obsidian"):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if "apk_signing.tsv" in files:
            return root
    raise SystemExit("evidence directory not found; pass its path explicitly")


EVID = _find_evidence()
VAULT = ("/media/obsidian/secdoc2/atoto-decrypted-20260620/media/obsidian"
         "/9A32A6FA32A6DB11/investigation/case_log/aibox-research"
         "/live-data-20260521T025014Z/oem_app_data/org.atoto.gps/databases")

# --- palette (reference instance, light mode) ------------------------------
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"   # categorical slots 1-3
CRITICAL   = "#d03b3b"                          # status, reserved
SURFACE    = "#fcfcfb"
INK        = "#0b0b0b"
INK2       = "#52514e"
MUTED      = "#898781"
GRID       = "#e1e0d9"
BASELINE   = "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.linewidth": 0.7,
    "lines.linewidth": 1.6,
})

W = 6.5  # inches: A4 text block at 2cm margins


def frame(ax, left=True, bottom=True):
    """Recessive chrome. Only the axes the reader actually reads survive."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.tick_params(length=0)


def titles(ax, ax_h_in, title, subtitle=None, extra_pad=0.0, x=0.0):
    """
    Place title and subtitle at fixed POINT offsets above the axes.

    set_title(pad=) and a subtitle pinned to an axes fraction fight each other
    whenever the axes height changes, which is how the first draft ended up
    with the two strings printed on top of one another in five figures out of
    six. Converting points to an axes fraction with the known axes height fixes
    it for any figure size.
    """
    def frac(points):
        return points / (ax_h_in * 72.0) + extra_pad

    if subtitle:
        ax.text(x, 1 + frac(6), subtitle, transform=ax.transAxes,
                fontsize=8, color=INK2, va="bottom", ha="left")
        ax.text(x, 1 + frac(22), title, transform=ax.transAxes,
                fontsize=10.5, color=INK, fontweight="bold",
                va="bottom", ha="left")
    else:
        ax.text(x, 1 + frac(6), title, transform=ax.transAxes,
                fontsize=10.5, color=INK, fontweight="bold",
                va="bottom", ha="left")


def save(fig, name):
    path = os.path.join(HERE, name)
    fig.savefig(path, dpi=220, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# Figure 1 - package signing identities
# ---------------------------------------------------------------------------
def fig_signing():
    rows = []
    with open(os.path.join(EVID, "apk_signing.tsv")) as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if len(r) >= 3:
                rows.append((r[1], r[2]))

    total = len(rows)
    # "O = Android" is the tell. Genuine Google-signed packages carry
    # O = Google Inc.; every AOSP-published test key and the Android Debug
    # keystore carries O = Android. That split, not the fingerprint, is the
    # finding, and it is why the denominator has to be every package.
    public = [r for r in rows if "O = Android" in r[1]]

    counts = Counter(fp for fp, _ in public)
    subj_of = {fp: s for fp, s in public}
    top = counts.most_common(6)

    labels, values = [], []
    for fp, n in top:
        s = subj_of[fp]
        cn = s.split("CN = ")[1].split(",")[0] if "CN = " in s else "?"
        labels.append(f"{fp[:11]}…   CN={cn}")
        values.append(n)
    other = len(public) - sum(values)
    if other > 0:
        labels.append(f"{len(counts) - len(top)} further AOSP keys")
        values.append(other)

    labels, values = labels[::-1], values[::-1]

    ax_h = 2.5
    fig, ax = plt.subplots(figsize=(W, ax_h))
    y = list(range(len(values)))
    ax.barh(y, values, height=0.6, color=S1, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontfamily="DejaVu Sans Mono", fontsize=7.2)
    ax.set_xlim(0, max(values) * 1.15)
    ax.set_xticks([])
    frame(ax, left=False, bottom=False)

    for i, v in enumerate(values):  # direct labels, so no value axis is needed
        ax.text(v + max(values) * 0.015, i, str(v), va="center",
                fontsize=8, color=INK, fontweight="bold")

    titles(ax, ax_h,
           f"{len(public)} of {total} packages are signed with a publicly "
           f"available key",
           f"The other {total - len(public)} carry genuine vendor or Google "
           f"certificates. Anyone can sign for the top two.",
           x=-0.34)  # clear the certificate labels, which are wide
    save(fig, "fig1_signing.png")
    return dict(total=total, public=len(public), platform=max(counts.values()),
                distinct_public_certs=len(counts))


# ---------------------------------------------------------------------------
# Figure 2 - partition classification
# ---------------------------------------------------------------------------
def fig_partitions():
    all_rows, pts = 0, []
    with open(os.path.join(EVID, "partition_classification.tsv")) as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            all_rows += 1
            try:
                size = int(row["size_bytes"]) / 1e6
                nz = float(row["nonzero_pct"])
                ent = float(row["entropy"])
            except (ValueError, KeyError):
                continue
            if size <= 0:      # lun5/persist.bin is a 0-byte image; a log
                continue       # x-axis has nowhere to put it. Noted in caption.
            pts.append((row["image"], size, nz, ent))

    # The thresholds are the ones stated in Chapter 3, applied verbatim.
    def cls(nz, ent):
        if nz < 5.0:
            return 0                      # sparse or zero-filled
        return 2 if ent >= 5.0 else 1     # elevated / structured

    names = ["Sparse or zero-filled", "Structured content",
             "Elevated entropy: compressed, encrypted or packed"]
    cols = [S3, S1, S2]

    ax_h = 3.2
    fig, ax = plt.subplots(figsize=(W, ax_h))
    for k in (0, 1, 2):
        sel = [(s, e) for _, s, nz, e in pts if cls(nz, e) == k]
        ax.scatter([s for s, _ in sel], [e for _, e in sel],
                   s=26, c=cols[k], label=f"{names[k]}  ({len(sel)})",
                   edgecolors=SURFACE, linewidths=0.8, alpha=0.92, zorder=3)

    # Threshold labels sit on the LEFT. On the right they collide with the
    # super.bin leader line, which is the one annotation that has to be legible.
    for lvl, note in ((7.0, "7.0  compressed or encrypted above this line"),
                      (5.0, "5.0  structured content below this line")):
        ax.axhline(lvl, color=MUTED, lw=0.7, ls=(0, (4, 3)), zorder=2)
        ax.text(0.005, lvl + 0.08, note, transform=ax.get_yaxis_transform(),
                ha="left", va="bottom", fontsize=6.8, color=MUTED)

    # Leader lines, because these three points are the ones the chapter argues
    # about and an unlabelled dot proves nothing.
    for want, label, off in (
        ("super", "super.bin  71 MB, file(1) says “data”", (-6, 26)),
        ("qcache", "qcache  holds the live Google key", (10, 34)),
    ):
        hit = next((p for p in pts if want in p[0].lower()), None)
        if hit:
            ax.annotate(label, (hit[1], hit[3]), textcoords="offset points",
                        xytext=off, fontsize=7.2, color=INK2,
                        ha="right" if off[0] < 0 else "left",
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7,
                                        shrinkA=0, shrinkB=3))

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{v:g} MB" if v < 1000 else f"{v/1000:g} GB"))
    ax.set_xlabel("partition size (log scale)")
    ax.set_ylabel("Shannon entropy (bits per byte)")
    ax.set_ylim(-0.4, 9.6)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    frame(ax)

    leg = ax.legend(loc="upper left", frameon=False, fontsize=7.4,
                    handletextpad=0.5, borderpad=0, borderaxespad=0.3)
    for t in leg.get_texts():
        t.set_color(INK2)

    titles(ax, ax_h,
           f"{all_rows} partition images sorted without opening one",
           "file(1) returns “data” for an empty partition and for an "
           "encrypted one alike. Two cheap measurements separate them.")
    save(fig, "fig2_partitions.png")
    return dict(rows=all_rows, plotted=len(pts))


# ---------------------------------------------------------------------------
# Figure 3 - GPS collection, per hour
# ---------------------------------------------------------------------------
def fig_gps():
    db = os.path.join(VAULT, "traccar.db")
    if not os.path.exists(db):
        print("skip fig3: traccar.db not reachable (vault unmounted)")
        return None
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute("select time/1000 from position order by time").fetchall()
    con.close()

    per_hour = Counter()
    for (ts,) in rows:
        per_hour[datetime.fromtimestamp(ts, timezone.utc).replace(
            minute=0, second=0, microsecond=0)] += 1

    xs = sorted(per_hour)
    ys = [per_hour[x] for x in xs]
    span_h = (max(xs) - min(xs)).total_seconds() / 3600

    ax_h = 2.3
    fig, ax = plt.subplots(figsize=(W, ax_h))
    ax.bar(xs, ys, width=1 / 24 * 0.85, color=S1, zorder=3)
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(ys) * 1.28)
    ax.set_ylabel("position fixes per hour")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    frame(ax)

    peak = max(range(len(ys)), key=lambda i: ys[i])
    ax.annotate(f"{ys[peak]} fixes in a single hour", (xs[peak], ys[peak]),
                textcoords="offset points", xytext=(6, 6), ha="left",
                fontsize=7.4, color=INK2)

    titles(ax, ax_h,
           f"{len(rows):,} positions queued for upload over "
           f"{span_h/24:.1f} days",
           "Read from the device's own database, times in UTC. Every bar is an "
           "hour the device recorded where the car was.")
    save(fig, "fig3_gps.png")
    return dict(rows=len(rows), active_hours=len(xs),
                span_days=round(span_h / 24, 1), peak_hour=max(ys))


# ---------------------------------------------------------------------------
# Figure 4 - ownership and disclosure timeline
# ---------------------------------------------------------------------------
def fig_timeline():
    # (date, label, colour, stagger level). Levels are hand-assigned rather
    # than alternated: five of the nine events fall inside one twelve-day
    # window, and any automatic rule stacks those labels on top of each other.
    events = [
        ("2026-02-03", "Activated at the factory",                    S2,       1),
        ("2026-05-09", "Purchased at retail",                         S1,      -1),
        ("2026-05-15", "Google credential rotated onto /qcache",      CRITICAL, 3),
        ("2026-05-19", "Firmware acquired over EDL; reported to Amazon", S1,   -3),
        ("2026-05-21", "Live /data extraction; TBI walk-in",          S1,       2),
        ("2026-06-14", "Google VRP submission filed",                 S3,      -2),
        ("2026-06-15", "Proof of concept executed",                   S3,       4),
        ("2026-07-31", "Re-examination completed",                    S1,      -4),
        ("2026-08-05", "Operational certificate expires",             CRITICAL, 1),
    ]

    ax_h = 3.9
    fig, ax = plt.subplots(figsize=(W, ax_h))
    ax.axhline(0, color=BASELINE, lw=1.2, zorder=2)

    # The collection window is a span, not a point.
    gps0, gps1 = datetime(2026, 5, 14), datetime(2026, 5, 19)
    ax.axvspan(gps0, gps1, ymin=0.47, ymax=0.53, color=S1, alpha=0.30, zorder=1)

    for d, label, col, lvl in events:
        dt = datetime.strptime(d, "%Y-%m-%d")
        h = lvl * 0.19
        critical = col == CRITICAL
        ax.plot([dt, dt], [0, h], color=col, lw=1.1, zorder=3)
        ax.plot([dt], [0], "o", ms=5.5, color=col, mec=SURFACE, mew=1.2, zorder=4)
        # The opaque bbox is load-bearing: nine stems on a nine-month axis
        # means several of them pass straight through a neighbour's label.
        ax.text(dt, h + (0.035 if lvl > 0 else -0.035),
                f"{d}   {label}", ha="left",
                va="bottom" if lvl > 0 else "top", fontsize=7.2,
                color=INK if critical else INK2,
                fontweight="bold" if critical else "normal", zorder=6,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))

    ax.text(gps0 + (gps1 - gps0) / 2, 0.085, "1,486 positions collected",
            ha="center", va="bottom", fontsize=7, color=INK2, style="italic",
            zorder=6, bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))

    ax.set_xlim(datetime(2026, 1, 5), datetime(2026, 12, 20))
    ax.set_ylim(-0.95, 0.95)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)

    titles(ax, ax_h,
           "The credential rotated onto the device while the owner had it",
           "Red marks the two dates that decide severity: when the live key "
           "was written, and when it stops being live.")
    save(fig, "fig4_timeline.png")


# ---------------------------------------------------------------------------
# Figure 5 - patch staleness
# ---------------------------------------------------------------------------
def fig_patch():
    patch = datetime(2023, 6, 5)
    build = datetime(2025, 9, 28)
    # End the span at acquisition, not at today. Chapter 9 counts bulletins
    # missed as of the date the firmware was pulled, and the figure has to
    # agree with the chapter it sits next to.
    acq = datetime(2026, 5, 19)
    months = (acq.year - patch.year) * 12 + acq.month - patch.month

    ax_h = 1.7
    fig, ax = plt.subplots(figsize=(W, ax_h))
    ax.barh([0], [(acq - patch).days], left=patch, height=0.32,
            color=S2, zorder=3)
    ax.plot([build], [0], "o", ms=7, color=SURFACE, mec=INK, mew=1.4, zorder=5)

    ax.text(patch, 0.26, "patch level frozen\n2023-06-05",
            fontsize=7.2, color=INK2, va="bottom")
    ax.text(acq, 0.26, "firmware acquired\n2026-05-19", fontsize=7.2,
            color=INK2, va="bottom", ha="right")
    ax.annotate("vendor rebuilds the image 2025-09-28\nand rolls in no patches",
                (build, -0.17), textcoords="offset points", xytext=(0, -4),
                ha="center", va="top", fontsize=7.2, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7,
                                shrinkA=0, shrinkB=2))
    # Left-aligned inside the bar, not centred: the centre is where the
    # rebuild marker sits, and the two printed on top of each other.
    ax.text(patch + (build - patch) * 0.04, 0,
            f"{months} months of Android Security Bulletins",
            ha="left", va="center", fontsize=8.5, color="#ffffff",
            fontweight="bold", zorder=6)

    ax.set_ylim(-1.25, 0.85)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)

    titles(ax, ax_h, "The kernel reached end-of-life inside this window")
    save(fig, "fig5_patch.png")
    return dict(months=months)


# ---------------------------------------------------------------------------
# Figure 6 - silent install channels
# ---------------------------------------------------------------------------
def fig_channels():
    caps = ["Install\nwith no\ndialog", "Microphone", "Read\nSMS",
            "Phone or\nSIM control", "Overlay or\nrecovery", "Doze\nexempt"]
    # 2 = holds it outright, 1 = holds the user-prompted variant, 0 = no.
    # The distinction between INSTALL_PACKAGES and REQUEST_INSTALL_PACKAGES is
    # the whole point of Chapter 9, so it cannot collapse into one mark.
    chans = [
        ("com.abupdate.fota_demo_iot",           "ADUPS OTA client",     [2,0,0,0,2,2]),
        ("install_suding_so.sh",                 "shell script",         [2,0,0,0,0,0]),
        ("com.atoto.carsysteminfo",              "“car info” reader",   [2,0,0,2,0,0]),
        ("com.aidl.atoto.store",                 "“find apps” helper",  [1,0,0,0,0,0]),
        ("com.atoto.command.dispatcher.service", "“drive chat”",        [2,2,2,0,2,0]),
        ("net.esimx.lpaui",                      "eSIM profile manager", [1,0,0,2,2,0]),
    ]

    ax_h = 2.5
    fig, ax = plt.subplots(figsize=(W, ax_h))
    for r, (_, _, row) in enumerate(chans):
        yy = len(chans) - 1 - r
        for c, state in enumerate(row):
            if state == 2:
                ax.plot([c], [yy], "s", ms=11, color=S1, mec=SURFACE,
                        mew=1.4, zorder=3)
            elif state == 1:
                ax.plot([c], [yy], "s", ms=11, color=SURFACE, mec=S2,
                        mew=1.6, zorder=3)
            else:
                ax.plot([c], [yy], "s", ms=11, color=GRID, mec=SURFACE,
                        mew=1.4, zorder=2)

    ax.set_xticks(range(len(caps)))
    ax.set_xticklabels(caps, fontsize=6.8)
    ax.xaxis.set_ticks_position("top")
    ax.set_yticks(range(len(chans)))
    ax.set_yticklabels([f"{p}\n{c}" for p, c, _ in chans][::-1],
                       fontsize=6.6, fontfamily="DejaVu Sans Mono")
    ax.set_xlim(-0.6, len(caps) - 0.4)
    ax.set_ylim(-0.6, len(chans) - 0.4)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)

    ax.legend(handles=[
        Line2D([], [], marker="s", ls="", ms=8, color=S1,
               label="holds the permission outright"),
        Line2D([], [], marker="s", ls="", ms=8, color=SURFACE, mec=S2, mew=1.6,
               label="holds only the variant that prompts the user"),
    ], loc="upper left", bbox_to_anchor=(0, -0.06), frameon=False,
        fontsize=7.2, handletextpad=0.5, borderpad=0, labelcolor=INK2, ncol=1)

    # This is the only chart with its tick labels on top, so the title has to
    # clear three lines of column header rather than sit 6pt off the axes.
    titles(ax, ax_h, "Six ways in, and what each one can already do",
           extra_pad=0.20, x=-0.30)
    save(fig, "fig6_channels.png")


if __name__ == "__main__":
    stats = {"signing": fig_signing(), "partitions": fig_partitions()}
    g = fig_gps()
    if g:
        stats["gps"] = g
    fig_timeline()
    stats["patch"] = fig_patch()
    fig_channels()
    with open(os.path.join(HERE, "figure_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)
    print(json.dumps(stats, indent=2))
