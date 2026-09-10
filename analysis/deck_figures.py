"""Deck figure engine for the SanDisk short pitch.

Every chart in deck/ is produced here from analysis/outputs (contract_dcf.json,
mc_contract_vals.npy, sndk_report.json), analysis/data, and the facts tabulated
in docs/CASE_SANDISK_SHORT.md. One theme, one palette, one font.

Run:  analysis/.venv/bin/python analysis/deck_figures.py
Writes: deck/figures/*.png and deck/figures/numbers.json (values used by deck/build_deck.py)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from quant.bl_density import implied_vol, fit_smile, rn_density, bs_call  # noqa: E402
import sndk_contract_dcf as engine  # noqa: E402  (module-level: loads data, defines sop())

DATA = ROOT / "analysis" / "data"
OUTS = ROOT / "analysis" / "outputs"
FIG = ROOT / "deck" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

ASOF = "2026-09-09"
# ---------------------------------------------------------------- theme
INK = "#14213D"       # primary ink / titles
INK2 = "#4A5468"      # secondary ink
MUTED = "#8A8F98"     # axis labels, history, de-emphasis
GRID = "#E4E6EA"
SURF = "#FFFFFF"
BLUE = "#2A5DB0"      # the market / consensus / bull case
RED = "#B5382F"       # our view / the short
GOLD = "#C9A227"      # dated catalysts, timing (always direct-labelled)
BLUE_L = "#C7D6EE"
RED_L = "#EBC9C5"
GREY_L = "#D9DCE1"

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "font.family": "Avenir Next",
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 8.5,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.edgecolor": "#C3C6CC", "axes.linewidth": 0.8, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.7, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.axisbelow": True, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF,
    "axes.facecolor": SURF, "legend.frameon": False, "text.parse_math": False,
})

cdcf = json.loads((OUTS / "contract_dcf.json").read_text())
report = json.loads((OUTS / "sndk_report.json").read_text())
info = json.loads((DATA / "SNDK" / "info.json").read_text())
S = cdcf["price"]
NUM = {"asof": ASOF, "price": S}


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", pad_inches=0.04, facecolor=SURF)
    plt.close(fig)
    print("  saved", name)


def money(x, bn=True):
    return f"${x/1e9:,.1f}bn" if bn else f"${x:,.0f}"


def rounded_bar(ax, x, h, w=0.55, color=BLUE, bottom=0.0, alpha=1.0, zorder=3):
    """Column with a rounded top (4px-ish) and square base, per the mark spec."""
    r = min(w * 0.18, abs(h) * 0.15) if h else 0
    p = FancyBboxPatch((x - w / 2, bottom), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       linewidth=0, facecolor=color, alpha=alpha, zorder=zorder, mutation_aspect=1)
    ax.add_patch(p)
    return p


# =========================================================== 1. price path
px = pd.read_csv(DATA / "SNDK" / "prices.csv", index_col=0)
px.index = pd.to_datetime(px.index, utc=True).tz_convert(None).normalize()
close = px["Close"]
fig, ax = plt.subplots(figsize=(7.6, 4.3))
ax.plot(close.index, close.values, color=INK, lw=1.8, solid_capstyle="round", zorder=3)
ax.fill_between(close.index, close.values, 20, color=INK, alpha=0.05, lw=0)
ax.set_yscale("log")
ax.set_yticks([30, 100, 300, 1000, 3000])
ax.set_yticklabels(["$30", "$100", "$300", "$1,000", "$3,000"])
ax.set_ylim(25, 4200)
ax.set_xlim(pd.Timestamp("2025-02-01"), pd.Timestamp("2027-01-20"))
ax.grid(axis="x", visible=False)
ev = [("2025-02-13", 36.0, "Spin from WDC, $36", (6, 17)),
      ("2025-12-31", 237.4, "2026 open $237", (8, -14)),
      ("2026-06-22", 2354.4, "22 Jun high $2,354 (intraday)", (-158, 8)),
      ("2026-07-29", 1015.9, "29 Jul low $1,016\n−56% in five weeks", (-70, -30)),
      ("2026-09-09", 1764.2, f"9 Sep ${S:,.0f}\n+74% from the low on\nMSCI and S&P 100 flows", (12, -16))]
for d, y, lbl, off in ev:
    ax.plot(pd.Timestamp(d), y, "o", ms=7, color=RED if "high" in lbl or "9 Sep" in lbl else BLUE,
            mec=SURF, mew=1.5, zorder=5)
    ax.annotate(lbl, (pd.Timestamp(d), y), xytext=off, textcoords="offset points",
                fontsize=7.6, color=INK2, ha="left", va="center")
for d, lbl in (("2026-08-31", "MSCI\n31 Aug"), ("2026-09-04", "S&P 100\nannounced")):
    ax.axvline(pd.Timestamp(d), color=GOLD, lw=1.0, zorder=2)
ax.text(pd.Timestamp("2026-09-12"), 32, "index inclusion:\nMSCI 31 Aug,\nS&P 100 4 Sep\n(effective 21 Sep)", fontsize=6.6,
        color=INK2, ha="left", va="bottom")
ax.set_ylabel("SNDK close, log scale")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b\n%y"))
save(fig, "price_path")
NUM["price_path"] = dict(spin=36.0, open26=237.38, high=2354.39, low_close=1015.89, low_date="2026-07-29",
                         from_low=S / 1015.89 - 1, from_high=S / 2354.39 - 1,
                         high_close=2335.0, drawdown_close=1015.89 / 2335.0 - 1, ytd=S / 237.38 - 1)

# ============================================== 2. quarterly revenue + GM (two panels)
qi = pd.read_csv(DATA / "SNDK" / "income_quarterly.csv", index_col=0)
qcols = [c for c in qi.columns if pd.notna(qi.loc["Total Revenue", c])]
qcols = sorted(qcols)
rev_q = qi.loc["Total Revenue", qcols].astype(float) / 1e9
gm_q = (qi.loc["Gross Profit", qcols].astype(float) / qi.loc["Total Revenue", qcols].astype(float)) * 100
op_q = (qi.loc["Operating Income", qcols].astype(float) / 1e9)
labels = ["FQ4-25", "FQ1-26", "FQ2-26", "FQ3-26", "FQ4-26"]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(4.4, 3.2), sharex=True,
                             gridspec_kw=dict(height_ratios=[1.35, 1], hspace=0.42))
xs = np.arange(len(labels))
for i, v in enumerate(rev_q.values):
    rounded_bar(a1, i, v, w=0.56, color=RED if i == len(xs) - 1 else BLUE)
    a1.text(i, v + 0.18, f"${v:.1f}bn", ha="center", fontsize=7.8, color=INK)
a1.set_xlim(-0.6, len(xs) - 0.4)
a1.set_ylim(0, 10.6)
a1.set_ylabel("Revenue, $bn")
a1.grid(axis="x", visible=False)
a1.set_title("Quarterly revenue: 4.7× in five quarters", loc="left", fontsize=9, color=INK)
a2.plot(xs, gm_q.values, "-o", color=RED, lw=2, ms=6, mec=SURF, mew=1.5, zorder=4)
for i, v in enumerate(gm_q.values):
    a2.text(i, v + 6, f"{v:.0f}%", ha="center", fontsize=7.8, color=INK)
a2.set_ylim(0, 105)
a2.set_yticks([0, 25, 50, 75, 100])
a2.set_ylabel("Gross margin")
a2.set_xticks(xs)
a2.set_xticklabels(labels)
a2.grid(axis="x", visible=False)
a2.set_title("Gross margin 26% to 85% in five quarters", loc="left", fontsize=9, color=INK)
save(fig, "quarterly_pnl")
NUM["quarterly"] = dict(labels=labels, rev=list(map(float, rev_q.values)), gm=list(map(float, gm_q.values)),
                        opinc=list(map(float, op_q.values)))

# ============================================ 3. NAND contract price path (2nd derivative)
fig, ax = plt.subplots(figsize=(4.4, 3.0))
q_lbl = ["1Q26", "2Q26", "3Q26", "Aug-26\nmonthly", "wk of 7 Sep\nspot wafer"]
lo = [55, 70, 10, 1.4, -2.7]
hi = [60, 75, 15, 1.4, -2.7]
mid = [(a + b) / 2 for a, b in zip(lo, hi)]
for i, (m, a, b) in enumerate(zip(mid, lo, hi)):
    col = BLUE if i < 3 else (GOLD if i == 3 else RED)
    rounded_bar(ax, i, m, w=0.56, color=col)
    if a != b:
        ax.plot([i, i], [a, b], color=SURF, lw=2.2, zorder=4)
        ax.plot([i, i], [a, b], color=INK, lw=0.9, zorder=5)
        ax.text(i, b + 2.5, f"+{a}–{b}%", ha="center", fontsize=7.8, color=INK)
    else:
        ax.text(i, m + (2.5 if m > 0 else -6.5), f"{m:+.1f}%", ha="center", fontsize=7.8, color=INK)
ax.axhline(0, color="#C3C6CC", lw=0.8)
ax.set_xticks(range(5))
ax.set_xticklabels(q_lbl, fontsize=7.4)
ax.set_ylim(-14, 92)
ax.set_ylabel("NAND contract price, QoQ %")
ax.grid(axis="x", visible=False)
ax.annotate("the second derivative\nturned in July", (2, 14), xytext=(2.45, 55), fontsize=8, color=RED,
            ha="left", arrowprops=dict(arrowstyle="-", color=RED, lw=0.9))
save(fig, "contract_price_path")

# ================================================= 4. what the price forces you to believe
req = cdcf["C_required"]
ev_bn = cdcf["ev"] / 1e9
pv2 = cdcf["A_pay2"]["pv"] / 1e9
pv_floor = (req["pv_paid"] - cdcf["A_pay2"]["pv"]) / 1e9
resid = req["residual"] / 1e9
fig, ax = plt.subplots(figsize=(7.4, 3.5))
xs = [0, 1, 2, 3]
rounded_bar(ax, 0, ev_bn, w=0.6, color=INK)
ax.text(0, ev_bn + 5, f"${ev_bn:,.0f}bn", ha="center", fontsize=9.5, color=INK, fontweight="bold")
ax.bar(1, pv2, 0.6, bottom=ev_bn - pv2, color=BLUE, lw=0, zorder=3)
ax.text(1, ev_bn - pv2 / 2, f"−${pv2:,.0f}bn", ha="center", va="center", fontsize=9, color=SURF, fontweight="bold")
ax.bar(2, pv_floor, 0.6, bottom=ev_bn - pv2 - pv_floor, color=BLUE, alpha=0.6, lw=0, zorder=3)
ax.text(2, ev_bn - pv2 + 5, f"−${pv_floor:,.0f}bn", ha="center", va="bottom", fontsize=9, color=INK, fontweight="bold")
rounded_bar(ax, 3, resid, w=0.6, color=RED)
ax.text(3, resid + 5, f"${resid:,.0f}bn\n{resid/ev_bn:.0%} of EV", ha="center", va="bottom", fontsize=9.5, color=RED, fontweight="bold")
for x0, x1, y in ((0, 1, ev_bn), (1, 2, ev_bn - pv2), (2, 3, ev_bn - pv2 - pv_floor)):
    ax.plot([x0 + 0.3, x1 - 0.3], [y, y], color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=2)
ax.set_xticks(xs)
ax.set_xticklabels(["Enterprise\nvalue today", "less PV of\nconsensus\nFY27–28 NI", "less PV of\ncontract floor\nFY29–31", "Residual:\npost-contract\nperpetuity"], fontsize=7.4)
ax.set_ylim(0, 290)
ax.set_ylabel("$bn")
ax.grid(axis="x", visible=False)
ax.annotate(f"needs ${req['nopat_req']/1e9:,.1f}bn of NOPAT\nevery year from FY32, forever\n\n= a permanent {req['gm_req']:.0%} gross\nmargin on a ${req['cogs32']/1e9:.1f}bn cost base\n(NAND mid-cycle: 25–40%)",
            (3.32, resid * 0.55), xytext=(3.55, 120), fontsize=8.2, color=RED, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=RED, lw=0.9))
ax.set_ylim(0, 300)
ax.set_xlim(-0.5, 5.6)
save(fig, "priced_in_bridge")
NUM["bridge"] = dict(ev=ev_bn, pv2=pv2, pv_floor=pv_floor, resid=resid, nopat_req=req["nopat_req"] / 1e9,
                     gm_req=req["gm_req"], cogs32=req["cogs32"] / 1e9, rev_req=req["rev_req"] / 1e9,
                     pv_paid=req["pv_paid"] / 1e9)

# ============================================= 5. required perpetual profit vs history
perp2 = cdcf["A_pay2"]["perp_nopat"] / 1e9
perp5 = cdcf["B_pay5"]["perp_nopat"] / 1e9
items = [
    ("Price needs after boom + floors paid (FY32+, forever)", req["nopat_req"] / 1e9, RED),
    ("Price needs after 2 consensus years (FY29+, forever)", perp2, RED),
    ("Price needs after 5 peak years (FY32+, forever)", perp5, RED),
    ("Entire NAND industry, best pre-2026 year (2018, est.)", 19.0, MUTED),
    ("Goldman 'normalised' SanDisk net income ($110 EPS)", 16.1, MUTED),
    ("Morgan Stanley through-cycle net income ($76 EPS)", 11.1, MUTED),
    ("Micron, whole company op. income, FY2022 peak", 9.7, MUTED),
    ("SanDisk standalone, best year op. income (FY2014)", 1.56, MUTED),
]
fig, ax = plt.subplots(figsize=(5.6, 3.35))
ys = np.arange(len(items))[::-1]
for y, (lbl, v, c) in zip(ys, items):
    ax.barh(y, v, height=0.58, color=c, lw=0, zorder=3)
    ax.text((21.4 if "industry" in lbl else v + 0.4), y, (f"${v:,.0f}bn (17–21)" if "industry" in lbl else f"${v:,.1f}bn"), va="center", fontsize=8, color=INK, fontweight="bold" if c == RED else "normal")
ax.plot([17, 21], [ys[3], ys[3]], color=SURF, lw=2.5, zorder=4)
ax.plot([17, 21], [ys[3], ys[3]], color=INK, lw=0.9, zorder=5)
ax.set_yticks(ys)
ax.set_yticklabels([i[0] for i in items], fontsize=7.6)
ax.set_xlim(0, 33)
ax.set_xlabel("After-tax profit per year, $bn")
ax.grid(axis="y", visible=False)
save(fig, "required_vs_history")
NUM["required"] = dict(perp2=perp2, perp5=perp5, post=req["nopat_req"] / 1e9,
                       x2014=cdcf["E_floor"]["x_fy2014"])

# ============================================= 6. floor vs consensus
cons = cdcf["consensus"]
fl = cdcf["E_floor"]
rev_est = pd.read_csv(DATA / "SNDK" / "revenue_estimate.csv").set_index("period")
fy28_lo, fy28_hi = rev_est.loc["+1y", "low"] / 1e9, rev_est.loc["+1y", "high"] / 1e9
fy27_lo, fy27_hi = rev_est.loc["0y", "low"] / 1e9, rev_est.loc["0y", "high"] / 1e9
bars = [("FY26\nactual", 20.248, MUTED, None), ("NBM floor\nrun-rate\n(~2/3 of bits)", fl["run_rate"] / 1e9, RED, None),
        ("Floor on\nevery bit", fl["all_bits"] / 1e9, RED, None),
        ("FY27\nconsensus", cons["rev"]["27"] / 1e9, BLUE, (fy27_lo, fy27_hi)),
        ("FY28\nconsensus", cons["rev"]["28"] / 1e9, BLUE, (fy28_lo, fy28_hi))]
fig, ax = plt.subplots(figsize=(4.6, 4.9))
for i, (lbl, v, c, rng) in enumerate(bars):
    rounded_bar(ax, i, v, w=0.58, color=c)
    ax.text(i, v + 1.6, f"${v:,.1f}bn", ha="center", fontsize=8.2, color=INK, fontweight="bold")
    if rng:
        ax.plot([i + 0.36, i + 0.36], list(rng), color=BLUE, lw=1.2, zorder=4)
        ax.plot([i + 0.31, i + 0.41], [rng[0]] * 2, color=BLUE, lw=1.2)
        ax.plot([i + 0.31, i + 0.41], [rng[1]] * 2, color=BLUE, lw=1.2)
ax.set_xticks(range(5))
ax.set_xticklabels([b[0] for b in bars], fontsize=7.4)
ax.set_ylim(0, 90)
ax.set_ylabel("Annual revenue, $bn")
ax.grid(axis="x", visible=False)
ax.annotate(f"{fl['vs_fy28_consensus']:.0%} vs FY28\nconsensus", (2, fl["all_bits"] / 1e9), xytext=(1.55, 62),
            fontsize=8.2, color=RED, ha="center", arrowprops=dict(arrowstyle="-", color=RED, lw=0.9))
ax.text(4.45, fy28_hi + 1, f"range\n${fy28_lo:.0f}–{fy28_hi:.0f}bn", fontsize=6.8, color=INK2, ha="center", va="bottom")
ax.set_xlim(-0.6, 4.9)
save(fig, "floor_vs_consensus")
NUM["floor"] = dict(run_rate=fl["run_rate"] / 1e9, all_bits=fl["all_bits"] / 1e9, vs28=fl["vs_fy28_consensus"],
                    fy27=cons["rev"]["27"] / 1e9, fy28=cons["rev"]["28"] / 1e9, fy28_lo=fy28_lo, fy28_hi=fy28_hi,
                    fy27_lo=fy27_lo, fy27_hi=fy27_hi, eps27=cons["eps"]["27"], eps28=cons["eps"]["28"],
                    ni27=cons["ni"]["27"] / 1e9, ni28=cons["ni"]["28"] / 1e9)

# ============================================= 7. base rates: every NAND company-year
sd = {2005: 25.0, 2006: 10.0, 2007: 7.1, 2008: -58.9, 2009: 14.6, 2010: 30.3, 2011: 27.0, 2012: 13.8, 2013: 25.3, 2014: 23.5, 2015: 11.1}
wdc = {2023: -22.4, 2024: -7.0, 2025: 6.2}
mu = {2010: 11.4, 2011: 12.6, 2012: 7.2, 2013: 7.1, 2016: -4, 2017: 12, 2018: 19, 2019: -10, 2020: 1, 2021: 4, 2022: 11, 2023: -74, 2024: -8}
kx = {2018: 9.2, 2019: -17.5, 2021: 14.2, 2022: -7.7, 2023: -23.5, 2024: 26.5}
rows = []
for name, d in (("SanDisk standalone / WDC Flash", sd), ("SanDisk standalone / WDC Flash", wdc), ("Micron NAND unit", mu), ("Kioxia", kx)):
    for y, v in d.items():
        rows.append((name, y, v))
br = pd.DataFrame(rows, columns=["co", "yr", "om"]).sort_values("om", ascending=False).reset_index(drop=True)
n_yrs, med, mean_, best, neg = len(br), br.om.median(), br.om.mean(), br.om.max(), int((br.om < 0).sum())
cols = {"SanDisk standalone / WDC Flash": RED, "Micron NAND unit": BLUE, "Kioxia": GOLD}
fig, ax = plt.subplots(figsize=(7.4, 2.9))
for i, r in br.iterrows():
    ax.bar(i, r.om, width=0.72, color=cols[r.co], lw=0, zorder=3)
ax.axhline(0, color="#C3C6CC", lw=0.8)
ax.axhline(med, color=INK, lw=1.0, ls=(0, (3, 2)), zorder=4)
ax.text(n_yrs - 0.5, med + 2.5, f"median {med:.0f}%", ha="right", fontsize=8, color=INK)
ax.axhline(75, color=RED, lw=1.4, zorder=4)
ax.text(n_yrs - 0.5, 77.5, "management's long-term model: ~75% operating margin, indefinitely", ha="right", fontsize=8, color=RED)
ax.axhline(61.2, color=RED, lw=1.0, ls=(0, (2, 2)), zorder=4)
ax.text(n_yrs - 0.5, 63.5, "SanDisk FY2026 (61%) — the only year above 40% in the record", ha="right", fontsize=7.6, color=RED)
ax.set_xticks(range(n_yrs))
ax.set_xticklabels([f"{r.yr}" for r in br.itertuples()], rotation=90, fontsize=6.4, color=INK2)
ax.set_ylim(-80, 90)
ax.set_ylabel("GAAP operating margin, %")
ax.grid(axis="x", visible=False)
handles = [plt.Rectangle((0, 0), 1, 1, color=c, lw=0) for c in cols.values()]
ax.legend(handles, list(cols.keys()), loc="lower left", ncol=3, fontsize=7.4, handlelength=1.0, columnspacing=1.0)
ax.set_title(f"{n_yrs} documented NAND company-years before the 2026 spike, ranked: median {med:.0f}%, mean {mean_:.0f}%, best {best:.0f}%, {neg} of {n_yrs} loss-making",
             loc="left", fontsize=8.6, color=INK)
save(fig, "base_rates")
# best 3-year consecutive run
best3 = -99
for co, g in pd.DataFrame(rows, columns=["co", "yr", "om"]).groupby("co"):
    g = g.sort_values("yr")
    v, yrs = g.om.values, g.yr.values
    for i in range(len(v) - 2):
        if yrs[i + 2] - yrs[i] == 2:
            best3 = max(best3, v[i:i + 3].mean())
NUM["base_rates"] = dict(n=n_yrs, median=med, mean=mean_, best=best, neg=neg, best3=best3,
                         table=[dict(co=r.co, yr=int(r.yr), om=float(r.om)) for r in br.itertuples()])

# ============================================ 8. centerpiece: MC value vs option-implied density
r = 0.0380
T = (pd.Timestamp("2027-01-15") - pd.Timestamp(ASOF)).days / 365
ivs, strikes = [], []
for f_, kind in (("calls", "call"), ("puts", "put")):
    df = pd.read_csv(DATA / "SNDK" / f"{f_}_2027-01-15.csv")
    df = df[(df.bid > 0) & (df.ask > 0) & (df.openInterest.fillna(0) >= 50)]
    for _, row in df.iterrows():
        K = row.strike
        if (kind == "call") != (K >= S):
            continue
        iv = implied_vol(0.5 * (row.bid + row.ask), S, K, T, r, kind=kind)
        if np.isfinite(iv) and 0.05 < iv < 4:
            ivs.append(iv)
            strikes.append(K)
sfn, (klo, khi) = fit_smile(strikes, ivs, S)
k_lo, k_hi = max(min(strikes) * 1.15, 400), min(max(strikes) * 0.95, 3600)
K, f = rn_density(S, T, r, sfn, k_lo, k_hi, n=4001)
f = f / np.trapezoid(f, K)
atm_iv = float(sfn(S))
# flat lognormal at ATM IV for the honest comparison
mu_ln = np.log(S) + (r - 0.5 * atm_iv ** 2) * T
sig_ln = atm_iv * np.sqrt(T)
f_ln = np.exp(-(np.log(K) - mu_ln) ** 2 / (2 * sig_ln ** 2)) / (K * sig_ln * np.sqrt(2 * np.pi))
f_ln = f_ln / np.trapezoid(f_ln, K)
vals = np.load(OUTS / "mc_contract_vals.npy")
med_mc = float(np.median(vals))
pct = float((vals < S).mean() * 100)
bl = report["bl"]["jan27"]
p_target = bl["probs"]["2125.0"]
p_above = bl["probs"][str(S)] if str(S) in bl["probs"] else bl["probs"]["1764.17"]

fig, ax = plt.subplots(figsize=(6.9, 3.1))
ax.fill_between(K, f, alpha=0.18, color=BLUE, lw=0)
ax.plot(K, f, color=BLUE, lw=2, label=f"What the market prices in — option-implied density to Jan-27 (ATM IV {atm_iv:.0%})")
hist, edges = np.histogram(vals[(vals > k_lo) & (vals < k_hi)], bins=70, density=True)
centers = 0.5 * (edges[1:] + edges[:-1])
scale = f.max() / hist.max()
ax.fill_between(centers, hist * scale, alpha=0.22, color=RED, lw=0)
ax.plot(centers, hist * scale, color=RED, lw=2, label="What we think it is worth — contract-aware Monte Carlo DCF, 20,000 paths")
ymax = max(f.max(), (hist * scale).max()) * 1.2
ax.set_ylim(0, ymax)
ax.axvline(S, color=INK, lw=1.3, zorder=4)
ax.text(S + 25, ymax * 0.74, f"price ${S:,.0f}\n{pct:.0f}th percentile of\nour value distribution", fontsize=7.8, color=INK, va="top")
ax.axvline(med_mc, color=RED, lw=1.0, ls=(0, (3, 2)))
ax.text(med_mc + 20, ymax * 0.66, f"our median ${med_mc:,.0f}\n({med_mc/S-1:+.0%})", fontsize=7.8, color=INK)
ax.axvline(2125, color=MUTED, lw=1.0, ls=(0, (3, 2)))
ax.text(2150, ymax * 0.42, f"sell-side mean target $2,125\noptions: P(above) = {p_target:.0%}", fontsize=7.8, color=INK2)
ax.set_yticks([])
ax.set_xlim(k_lo, k_hi)
ax.set_xlabel("SNDK share price, $")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
ax.legend(loc="upper right", fontsize=7.4, bbox_to_anchor=(1.0, 1.02))
ax.grid(axis="y", visible=False)
save(fig, "centerpiece")
NUM["mc"] = dict(median=med_mc, pct=pct, p5=cdcf["D_mc"]["p5"], p25=cdcf["D_mc"]["p25"], p75=cdcf["D_mc"]["p75"],
                 p95=cdcf["D_mc"]["p95"], p_above=cdcf["D_mc"]["p_above"], attribution=cdcf["D_mc"]["attribution"])
NUM["bl"] = dict(atm_iv=atm_iv, p_target=p_target, p_above=p_above, p_below_1000=1 - bl["probs"]["1000.0"],
                 p_below_1200=1 - bl["probs"]["1200.0"], rr25=bl["rr25"], n_quotes=len(strikes), integral=bl["integral"])

# 8b. B-L vs flat lognormal + smile (appendix)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.9), gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.28))
a1.plot(K, f, color=BLUE, lw=2, label="Breeden–Litzenberger density (fitted smile)")
a1.plot(K, f_ln, color=MUTED, lw=1.6, ls=(0, (3, 2)), label=f"Flat lognormal at ATM IV {atm_iv:.0%}")
a1.axvline(S, color=INK, lw=1.0)
a1.text(S + 25, f.max() * 0.08, f"price ${S:,.0f}", fontsize=7.6, color=INK)
a1.set_yticks([])
a1.set_xlim(k_lo, k_hi)
a1.set_xlabel("SNDK at 15 Jan 2027, $")
a1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
a1.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.02, 1.0))
a1.set_ylim(0, f.max() * 1.45)
a1.grid(axis="y", visible=False)
a1.set_title("The smile adds little to a lognormal: use it for sizing, not as dissent", loc="left", fontsize=8.4)
a2.scatter(np.array(strikes), np.array(ivs) * 100, s=12, color=BLUE, alpha=0.7, lw=0, zorder=3)
kk = np.linspace(min(strikes), max(strikes), 200)
a2.plot(kk, sfn(kk) * 100, color=INK, lw=1.6)
a2.axvline(S, color=INK, lw=0.8)
a2.set_xlabel("Strike, $")
a2.set_ylabel("Implied vol, % (own, from mids)")
a2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
a2.set_title(f"{len(strikes)} OTM quotes, OI ≥ 50; 25Δ risk-reversal {bl['rr25']:+.1%}", loc="left", fontsize=8.4)
save(fig, "bl_vs_lognormal")

# ============================================ 9. value vs post-contract GM
fig, ax = plt.subplots(figsize=(4.7, 3.4))
gms = np.linspace(0.20, 0.85, 40)
ax.axvspan(25, 40, color=GREY_L, alpha=0.5, lw=0)
ax.text(32.5, 120, "NAND mid-cycle\nGM 25–40%", fontsize=7.4, color=INK2, ha="center")
ax.plot(gms * 100, [engine.sop(g) for g in gms], color=RED, lw=2.2, label="15% bit growth (company guide: mid-teens)")
ax.plot(gms * 100, [engine.sop(g, bit_growth=0.25) for g in gms], color=BLUE, lw=1.8, ls=(0, (3, 2)), label="25% bit growth (AI-storage bull)")
ax.axhline(S, color=INK, lw=1.2)
ax.text(44, S * 1.04, f"price ${S:,.0f}", fontsize=8, color=INK)
ax.plot([req["gm_req"] * 100], [S], "o", ms=8, color=RED, mec=SURF, mew=1.5, zorder=5)
ax.annotate(f"{req['gm_req']:.0%} GM forever\nis what the price needs", (req["gm_req"] * 100, S), xytext=(56, 1350),
            fontsize=7.8, color=RED, ha="center", arrowprops=dict(arrowstyle="-", color=RED, lw=0.9))
ax.set_xlabel("Permanent gross margin after the contracts expire (FY32+), %")
ax.set_ylabel("Value per share, $")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
ax.set_ylim(0, 2400)
ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, 1.0))
save(fig, "value_vs_gm")
NUM["sop"] = {k: float(v) for k, v in cdcf["C_sop_by_gm"].items()}

# ============================================ 10. scenarios / asymmetry
sc = cdcf["F_12m"]["scenarios"]
order = ["Deep bust: bullwhip + China supply, floors renegotiated", "Base: contract prices flat by 1Q27, down from 2Q27",
         "Against us: prices rise through CY27, FY28 consensus holds"]
short = ["Deep bust (20%)", "Base (50%)", "Against us (30%)"]
fig, ax = plt.subplots(figsize=(4.8, 2.5))
for i, (k, lbl) in enumerate(zip(order, short)):
    t = sc[k]["target"]
    c = RED if t < S else BLUE
    ax.barh(i, t - S, left=S, height=0.5, color=c, lw=0, zorder=3)
    if t > S:
        ax.text(t + 18, i, f"${t:,.0f}  ({sc[k]['short_return']:+.0%} to the short)", va="center", ha="left", fontsize=8, color=INK, fontweight="bold")
    else:
        ax.text(t + 25, i, f"${t:,.0f}  ({sc[k]['short_return']:+.0%})", va="center", ha="left", fontsize=8, color=SURF, fontweight="bold", zorder=5)
ax.axvline(S, color=INK, lw=1.3)
ax.text(S, 2.62, f"price ${S:,.0f}", ha="center", fontsize=7.8, color=INK)
ax.set_yticks(range(3))
ax.set_yticklabels(short, fontsize=8)
ax.set_xlim(300, 3300)
ax.set_ylim(-0.6, 2.9)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
ax.grid(axis="y", visible=False)
ax.set_xlabel("12-month target, $")
save(fig, "scenarios")
NUM["scen"] = dict(ev=cdcf["F_12m"]["expected_short_return"], rr=cdcf["F_12m"]["reward_risk"],
                   rows=[dict(name=k, **sc[k]) for k in order])

# ============================================ 11. Kioxia relative value
fig, (a1, a2) = plt.subplots(1, 2, figsize=(4.6, 2.6), gridspec_kw=dict(wspace=0.45))
for ax, (title, sn, kx_, unit) in zip((a1, a2), (("EV / NTM sales", 5.2, 3.1, "×"), ("NTM P/E", 8.2, 4.4, "×"))):
    rounded_bar(ax, 0, sn, w=0.55, color=RED)
    rounded_bar(ax, 1, kx_, w=0.55, color=BLUE)
    ax.text(0, sn + 0.15, f"{sn:.1f}{unit}", ha="center", fontsize=9, color=INK, fontweight="bold")
    ax.text(1, kx_ + 0.15, f"{kx_:.1f}{unit}", ha="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["SanDisk\n(NASDAQ)", "Kioxia\n(TSE: 285A)"], fontsize=7.6)
    ax.set_ylim(0, max(sn, kx_) * 1.3)
    ax.set_title(title, loc="left", fontsize=8.6)
    ax.grid(axis="x", visible=False)
    ax.set_xlim(-0.6, 1.6)
save(fig, "kioxia_rv")

# ============================================ 12. P/B at cycle peaks
fig, ax = plt.subplots(figsize=(4.6, 2.3))
peaks = [("SanDisk\n2010 peak", 2.6), ("SanDisk\n2014 peak", 3.6), ("Micron\n2018 peak", 2.2), ("Micron\n2022 peak", 2.6), ("SanDisk\ntoday", 16.7)]
for i, (lbl, v) in enumerate(peaks):
    rounded_bar(ax, i, v, w=0.55, color=RED if i == 4 else MUTED)
    ax.text(i, v + 0.4, f"{v:.1f}×", ha="center", fontsize=8.4, color=INK, fontweight="bold" if i == 4 else "normal")
ax.set_xticks(range(5))
ax.set_xticklabels([p[0] for p in peaks], fontsize=7.4)
ax.set_ylim(0, 20)
ax.set_ylabel("Price / book")
ax.grid(axis="x", visible=False)
ax.text(1.5, 15.5, "every prior peak at 2.2–3.6× book was\nfollowed by a 40–59% drawdown in 6–12 months", fontsize=7.4, color=INK2, ha="center")
save(fig, "pb_peaks")

# ============================================ 13. reflexive estimates: EPS revisions vs price
tr = pd.read_csv(DATA / "SNDK" / "eps_trend.csv").set_index("period")
lags = [90, 60, 30, 7, 0]
cols_ = ["90daysAgo", "60daysAgo", "30daysAgo", "7daysAgo", "current"]
dates = [pd.Timestamp(ASOF) - pd.Timedelta(days=d) for d in lags]
px_at = [close[:d].iloc[-1] for d in dates]
fy27 = tr.loc["0y", cols_].values.astype(float)
fy28 = tr.loc["+1y", cols_].values.astype(float)
fig, ax = plt.subplots(figsize=(4.6, 3.5))
x = np.arange(5)
ax.plot(x, fy28 / fy28[0] * 100, "-o", color=BLUE, lw=2, ms=6, mec=SURF, mew=1.5, label="Consensus FY28 EPS")
ax.plot(x, fy27 / fy27[0] * 100, "-o", color=BLUE, lw=1.6, ms=6, mec=SURF, mew=1.5, alpha=0.55, label="Consensus FY27 EPS")
ax.plot(x, np.array(px_at) / px_at[0] * 100, "-o", color=INK, lw=2, ms=6, mec=SURF, mew=1.5, label="SNDK price")
ax.set_xticks(x)
ax.set_xticklabels(["−90d\n(11 Jun)", "−60d", "−30d", "−7d", "9 Sep"], fontsize=7.6)
ax.set_ylabel("Indexed, 90 days ago = 100")
ax.text(4.08, fy28[-1] / fy28[0] * 100, f"${fy28[-1]:.0f}\n(+{fy28[-1]/fy28[0]-1:.0%})", fontsize=7.4, color=INK, va="center")
ax.text(4.08, px_at[-1] / px_at[0] * 100, f"${px_at[-1]:,.0f}\n({px_at[-1]/px_at[0]-1:+.0%})", fontsize=7.4, color=INK, va="center")
ax.set_xlim(-0.3, 4.9)
ax.legend(fontsize=7, loc="upper left")
ax.set_title("Estimates follow price: FY28 EPS +45% in 90 days; the boom is marked to spot", loc="left", fontsize=8.4)
save(fig, "reflexive_estimates")
NUM["revisions"] = dict(fy28=list(map(float, fy28)), fy27=list(map(float, fy27)), px=list(map(float, px_at)))

# ============================================ 14. supply timeline
fig, ax = plt.subplots(figsize=(8.6, 2.9))
t0, t1 = pd.Timestamp("2026-06-01"), pd.Timestamp("2029-06-30")
events = [  # (start, end, label, kind)  kind: density | wafer | fab | demandcross | now
    ("2026-07-01", "2026-09-01", "Kioxia/SanDisk BiCS10 in mass production (+59% density)", "density"),
    ("2026-08-01", "2026-10-01", "Samsung V10 (400-layer) ramp", "density"),
    ("2026-09-01", "2026-12-31", "SK hynix 321L to half of Korean capacity", "density"),
    ("2026-07-01", "2027-06-30", "YMTC Wuhan Fab 3 pulled into 2H26 (14% bit share; 500k wpm ambition)", "wafer"),
    ("2026-09-01", "2027-06-30", "SK hynix Dalian 2 build-out: +30–50k wafers/month", "wafer"),
    ("2027-01-01", "2027-06-30", "Samsung Xi'an 286L at full output", "wafer"),
    ("2027-07-01", "2027-12-31", "Supply/demand crossover: TrendForce, Yole, Kioxia, Samsung all date it 2H27", "cross"),
    ("2028-07-01", "2028-12-31", "Micron Singapore greenfield NAND fab output", "fab"),
    ("2029-01-01", "2029-06-30", "Kioxia/SanDisk Kitakami Fab 3 output (¥5tn Japan plan, announced 27 Aug 26)", "fab"),
]
kc = {"density": BLUE, "wafer": BLUE, "cross": RED, "fab": MUTED}
for i, (s_, e_, lbl, kind) in enumerate(events):
    y = len(events) - i
    s_, e_ = pd.Timestamp(s_), pd.Timestamp(e_)
    ax.barh(y, (e_ - s_).days, left=s_, height=0.48, color=kc[kind], lw=0, zorder=3, alpha=0.9 if kind != "cross" else 1)
    ax.text(e_ + pd.Timedelta(days=12), y, lbl, va="center", fontsize=7.2, color=INK,
            fontweight="bold" if kind == "cross" else "normal")
ax.axvline(pd.Timestamp(ASOF), color=GOLD, lw=1.2, zorder=4)
ax.axvspan(pd.Timestamp("2027-04-01"), pd.Timestamp("2027-06-30"), color=RED_L, alpha=0.5, lw=0)
ax.text(pd.Timestamp("2027-05-15"), 0.25, "2Q27 = quarter 8\nof the up-leg", fontsize=6.8, color=RED, ha="center")
ax.set_yticks([])
ax.set_ylim(-0.2, len(events) + 1.3)
ax.set_xlim(t0, t1)
ax.text(pd.Timestamp("2026-09-15"), len(events) + 0.85, "today", fontsize=7.4, color=INK2, ha="left")
ax.grid(axis="y", visible=False)
ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1, 7]))
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
handles = [plt.Rectangle((0, 0), 1, 1, color=c, lw=0) for c in (BLUE, RED, MUTED)]
ax.legend(handles, ["2027 bits: density migration and China (no new fabs)", "Every dated primary forecast", "Greenfield fabs (2H28+)"],
          loc="upper right", fontsize=6.8, ncol=1, handlelength=1.0, bbox_to_anchor=(1.0, 1.0))
save(fig, "supply_timeline")

# ============================================ 15. catalyst timeline (event path, equal spacing)
fig, ax = plt.subplots(figsize=(8.2, 2.9))
cats = [
    ("21 Sep 26", "S&P 100 inclusion\neffective", "last mechanical bid;\nentry begins after", GOLD),
    ("30 Sep 26", "Micron FQ4", "NAND ASP, FY27 capex,\nCY27 supply/demand", RED),
    ("early Oct 26", "TrendForce 4Q26\nNAND forecast", "first official 4Q print;\nwafer/client SSD flat?", RED),
    ("late Oct 26", "Hyperscaler Q3,\nSamsung/SK hynix Q3", "2027 capex framing,\ninventory days", BLUE),
    ("6 Nov 26", "SanDisk FQ1 FY27", "FQ2 GM guide, NBM terms,\ninventory days, buyback pace", RED),
    ("mid Nov 26", "Kioxia 2Q", "2027 bit plan,\nJV economics", BLUE),
    ("late Dec 26", "TrendForce 1Q27\nforecast", "first quarter a decline\ncan print; kill check", RED),
    ("late Jan 27", "Hyperscaler 2027\ncapex guides; SNDK FQ2", "storage-specific\ncommitments?", BLUE),
    ("1H27", "Wafer adds land", "Dalian 2, Xi'an 286L,\nYMTC Fab 3", BLUE),
    ("2H27", "Supply/demand\ncrossover", "TrendForce, Yole, Kioxia,\nSamsung; exit window", RED),
]
n = len(cats)
ax.axhline(0, color=INK, lw=1.2, zorder=2)
for i, (d, head, sub, c) in enumerate(cats):
    ax.plot(i, 0, "o", ms=10, color=c, mec=SURF, mew=1.6, zorder=5)
    up = (i % 2 == 0)
    ax.plot([i, i], [0, 0.32 if up else -0.32], color=c, lw=0.9, zorder=3)
    y = 0.4 if up else -0.4
    ax.text(i, y, f"{d}\n{head}", ha="center", va="bottom" if up else "top", fontsize=6.9, color=INK, fontweight="bold", linespacing=1.15)
    ax.text(i, y + (0.95 if up else -0.95), sub, ha="center", va="bottom" if up else "top", fontsize=6.3, color=INK2, linespacing=1.15)
ax.axvspan(0.5, 2.5, color=GOLD, alpha=0.12, lw=0, zorder=1)
ax.text(1.5, -2.2, "entry window: half after 30 Sep, half on the first flat-to-down print", fontsize=6.4, color=INK2, ha="center", va="bottom")
ax.axvline(2.5, color=INK, lw=0.8, ls=(0, (2, 2)))
ax.text(2.55, 2.15, "final 15 Oct", fontsize=6.6, color=INK, ha="left", va="top")
ax.set_ylim(-2.3, 2.3)
ax.set_xlim(-0.7, n - 0.3)
ax.set_yticks([])
ax.set_xticks([])
ax.grid(visible=False)
for sp in ("left", "bottom"):
    ax.spines[sp].set_visible(False)
save(fig, "catalyst_timeline")

# ============================================ 16. margin cycle history (annual GM, SNDK vs MU)
def gm(t):
    inc = pd.read_csv(DATA / t / "income_annual.csv", index_col=0)
    s = (inc.loc["Gross Profit"] / inc.loc["Total Revenue"]).dropna().astype(float)
    s.index = [int(c[:4]) for c in s.index]
    return s.sort_index()

sndk_gm, mu_gm = gm("SNDK"), gm("MU")
fig, ax = plt.subplots(figsize=(4.8, 3.3))
ax.plot(mu_gm.index, mu_gm.values * 100, "-s", color=BLUE, lw=2, ms=6, mec=SURF, mew=1.4, label="Micron (FY Aug, DRAM+NAND)")
ax.plot(sndk_gm.index, sndk_gm.values * 100, "-o", color=RED, lw=2, ms=6, mec=SURF, mew=1.4, label="SanDisk (FY Jun)")
for x_, y_ in zip(sndk_gm.index, sndk_gm.values * 100):
    ax.text(x_ + (0.12 if x_ == 2024 else 0), y_ + (-9 if x_ == 2024 else 5), f"{y_:.0f}%", ha="center", fontsize=7.6, color=INK)
ax.axhline(0, color="#C3C6CC", lw=0.8)
ax.axhline(47, color=MUTED, lw=1.0, ls=(0, (3, 2)))
ax.text(2022.05, 49, "SanDisk standalone peak GM 47% (FY2010)", fontsize=7, color=INK2)
ax.set_xticks(sorted(set(sndk_gm.index) | set(mu_gm.index)))
ax.set_ylim(-15, 90)
ax.set_ylabel("Gross margin, %")
ax.legend(fontsize=7, loc="upper left")
ax.grid(axis="x", visible=False)
save(fig, "margin_cycle")
NUM["gm_hist"] = dict(sndk={int(k): float(v) for k, v in sndk_gm.items()}, mu={int(k): float(v) for k, v in mu_gm.items()})

# ============================================ 17. sensitivity heatmaps
gm_rows = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
bg_cols = [0.10, 0.15, 0.20, 0.25, 0.30]
w_cols = [0.10, 0.11, 0.12, 0.13]
grid_bg = np.array([[engine.sop(g, bit_growth=b) for b in bg_cols] for g in gm_rows])
grid_w = np.array([[engine.sop(g, wacc=w) for w in w_cols] for g in gm_rows])
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
cmap = LinearSegmentedColormap.from_list("div", [RED, "#F1F1F1", BLUE])
norm = TwoSlopeNorm(vmin=300, vcenter=S, vmax=3300)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.9), gridspec_kw=dict(width_ratios=[5, 4], wspace=0.35))
for ax, grid, cols_lbl, xl in ((a1, grid_bg, [f"{b:.0%}" for b in bg_cols], "Bit growth, FY27–36"),
                                (a2, grid_w, [f"{w:.0%}" for w in w_cols], "WACC")):
    ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid[i, j]
            ax.text(j, i, f"${v:,.0f}", ha="center", va="center", fontsize=7.6,
                    color=SURF if (v < 700 or v > 2700) else INK, fontweight="bold" if v > S else "normal")
    ax.set_xticks(range(grid.shape[1]))
    ax.set_xticklabels(cols_lbl, fontsize=7.6)
    ax.set_yticks(range(len(gm_rows)))
    ax.set_yticklabels([f"{g:.0%}" for g in gm_rows], fontsize=7.6)
    ax.set_xlabel(xl)
    ax.set_ylabel("Post-contract gross margin, permanent")
    ax.grid(visible=False)
    for sp in ax.spines.values():
        sp.set_visible(False)
a1.set_title(f"Value/share: red below ${S:,.0f}, blue above (bold)", loc="left", fontsize=8.4)
a2.set_title("Value/share vs discount rate", loc="left", fontsize=8.4)
save(fig, "sensitivity")
NUM["grid_bg"] = dict(rows=gm_rows, cols=bg_cols, vals=grid_bg.round(0).tolist())
NUM["grid_w"] = dict(rows=gm_rows, cols=w_cols, vals=grid_w.round(0).tolist())

# ============================================ 18. MC inputs + tornado
attr = cdcf["D_mc"]["attribution"]
names = {"mid_gm": "Post-contract GM  N(45%, 15%)", "bitg": "Bit growth  N(18%, 7%)", "costd": "Cost/bit decline  N(12%, 4%)",
         "boom": "FY27–28 vs consensus  N(100%, 12%)", "floor": "Floor renegotiation  20% × U(60–90%)", "wacc": "WACC  tri(10, 11.5, 13%)"}
keys = sorted(attr, key=lambda k: -abs(attr[k]))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.7), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.55))
ys = np.arange(len(keys))[::-1]
for y, k in zip(ys, keys):
    v = attr[k]
    a1.barh(y, v, height=0.55, color=BLUE if v > 0 else RED, lw=0, zorder=3)
    a1.text(v + (0.02 if v > 0 else -0.02), y, f"{v:+.2f}", va="center", ha="left" if v > 0 else "right", fontsize=7.8, color=INK)
a1.set_yticks(ys)
a1.set_yticklabels([names[k] for k in keys], fontsize=7.2)
a1.set_xlim(-0.6, 0.95)
a1.axvline(0, color="#C3C6CC", lw=0.8)
a1.set_xlabel("Spearman rank correlation with value/share")
a1.grid(axis="y", visible=False)
a1.set_title("What drives the spread", loc="left", fontsize=8.4)
a2.hist(vals[vals < 2600], bins=60, color=RED, alpha=0.85, lw=0)
a2.axvline(S, color=INK, lw=1.2)
a2.text(S + 30, a2.get_ylim()[1] * 0.9, f"price\n{pct:.0f}th pct", fontsize=7.4, color=INK)
a2.axvline(med_mc, color=INK, lw=0.9, ls=(0, (3, 2)))
a2.text(med_mc + 30, a2.get_ylim()[1] * 0.62, f"median ${med_mc:,.0f}", fontsize=7.4, color=INK)
a2.set_yticks([])
a2.set_xlabel("Value per share, $ (20,000 paths)")
a2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
a2.grid(axis="y", visible=False)
a2.set_title(f"p5 ${cdcf['D_mc']['p5']:,.0f} · p95 ${cdcf['D_mc']['p95']:,.0f} · P(value > price) {cdcf['D_mc']['p_above']:.1%}", loc="left", fontsize=8.4)
save(fig, "mc_tornado")

# ============================================ 19. beta scatter vs SMH
try:
    import yfinance as yf
    bench = yf.download(["SMH"], period="18mo", auto_adjust=True, progress=False)["Close"]
    bench = bench.iloc[:, 0] if isinstance(bench, pd.DataFrame) else bench
    bench.index = pd.to_datetime(bench.index).normalize()
    rets = pd.concat([close.pct_change().rename("SNDK"), bench.pct_change().rename("SMH")], axis=1).dropna()
    rets = rets[rets.index >= pd.Timestamp("2025-03-15")]
    b = report["beta"]["SMH"]
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.scatter(rets.SMH * 100, rets.SNDK * 100, s=10, color=BLUE, alpha=0.5, lw=0, zorder=3)
    xx = np.linspace(rets.SMH.min(), rets.SMH.max(), 10) * 100
    slope, icpt = np.polyfit(rets.SMH * 100, rets.SNDK * 100, 1)
    ax.plot(xx, icpt + slope * xx, color=RED, lw=2)
    ax.set_xlabel("SMH daily return, %")
    ax.set_ylabel("SNDK daily return, %")
    ax.set_title(f"β {b['beta']:.2f} · R² {b['r2']:.0%} · idio vol {b['idio_vol']:.0%} ann.", loc="left", fontsize=8.4)
    save(fig, "beta_scatter")
    NUM["beta"] = b
except Exception as e:  # network optional
    print("beta scatter skipped:", e)
    NUM["beta"] = report["beta"]["SMH"]

# ============================================ 20. DCF cash-flow build (appendix table data)
val40, ev40, dfc = engine.sop(0.40, verbose=True)
NUM["dcf_table"] = [dict(fy=int(r.fy), rev=r.rev / 1e9, gm=(None if pd.isna(r.gm) else float(r.gm)), cogs=r.cogs / 1e9,
                         opex=r.opex / 1e9, nopat=r.nopat / 1e9, fcf=r.fcf / 1e9) for r in dfc.itertuples()]
NUM["dcf_meta"] = dict(val40=val40, ev40=ev40 / 1e9, wacc=engine.WACC, infl=engine.INFL, tax=engine.TAX,
                       opex27=engine.OPEX_FY27 / 1e9, cogs26=engine.FY26_COGS / 1e9, shares=engine.SHARES / 1e6,
                       debt=engine.DEBT / 1e9, cash=engine.CASH / 1e9, mktcap=cdcf["mktcap"] / 1e9,
                       pay2_pct=cdcf["A_pay2"]["pv"] / cdcf["ev"], pay5_pv=cdcf["B_pay5"]["pv"] / 1e9,
                       pay5_pct=cdcf["B_pay5"]["pv"] / cdcf["ev"], pay5_resid=cdcf["B_pay5"]["residual"] / 1e9,
                       pay2_resid=cdcf["A_pay2"]["residual"] / 1e9)
# WACC band for A
NUM["perp2_by_wacc"] = {}
for w in (0.10, 0.11, 0.12, 0.13):
    p2 = sum(engine.pv(engine.CONS_NI[y], y - 26, w) for y in (27, 28))
    NUM["perp2_by_wacc"][f"{w:.2f}"] = (cdcf["ev"] - p2) * (1 + w) ** 2 * (w - engine.INFL) / (1 + engine.INFL) / 1e9


# ============================================ 21. consensus path (revenue bars, actual vs consensus)
fig, ax = plt.subplots(figsize=(4.4, 2.6))
yrs = ["FY23", "FY24", "FY25", "FY26", "FY27E", "FY28E"]
revs = [6.086, 6.663, 7.355, 20.248, fl["fy27"] if isinstance(fl, dict) and "fy27" in fl else cons["rev"]["27"] / 1e9, cons["rev"]["28"] / 1e9]
revs = [6.086, 6.663, 7.355, 20.248, cons["rev"]["27"] / 1e9, cons["rev"]["28"] / 1e9]
for i, v in enumerate(revs):
    rounded_bar(ax, i, v, w=0.58, color=MUTED if i < 3 else (RED if i == 3 else BLUE))
    ax.text(i, v + 1.2, f"${v:,.1f}bn", ha="center", fontsize=7.8, color=INK, fontweight="bold" if i >= 3 else "normal")
ax.plot([4 + 0.36] * 2, [fy27_lo, fy27_hi], color=BLUE, lw=1.1)
ax.plot([5 + 0.36] * 2, [fy28_lo, fy28_hi], color=BLUE, lw=1.1)
ax.text(5.42, fy28_hi, "range", fontsize=6.6, color=INK2, va="center")
ax.set_xticks(range(6))
ax.set_xticklabels(yrs, fontsize=7.8)
ax.set_ylim(0, 95)
ax.set_ylabel("Revenue, $bn")
ax.grid(axis="x", visible=False)
ax.set_xlim(-0.6, 5.9)
for i, g in ((3, "+175%"), (4, "+142%"), (5, "+18%")):
    ax.text(i, revs[i] + 7.5, g, ha="center", fontsize=7.4, color=INK2)
ax.set_title("Consensus revenue: three flat years, then 8× in three (bits +15% a year)", loc="left", fontsize=8.4)
save(fig, "consensus_path")

# ============================================ 22. sell-side targets (lollipop)
fig, ax = plt.subplots(figsize=(4.4, 2.9))
pts = [("Street high", 3600, MUTED), ("Bernstein bull", 3000, BLUE), ("Citi, 9× consensus FY28", 2382, BLUE),
       ("Goldman, 20× normalised $110", 2200, BLUE), ("Street mean (23 analysts)", 2125, BLUE),
       ("Morgan Stanley, 23× through-cycle $76", 1748, BLUE), ("Street low", 1000, MUTED), ("Our base target", 927, RED)]
for i, (lbl, v, c) in enumerate(pts):
    y = len(pts) - i
    ax.plot([0, v], [y, y], color=GRID, lw=1.2, zorder=2)
    ax.plot(v, y, "o", ms=8, color=c, mec=SURF, mew=1.5, zorder=4)
    ax.text(v + 60, y, f"${v:,.0f}", va="center", fontsize=7.4, color=INK, fontweight="bold" if c == RED else "normal")
ax.axvline(S, color=INK, lw=1.1, zorder=3)
ax.text(S + 30, len(pts) + 0.65, f"price ${S:,.0f}", fontsize=7, color=INK, va="bottom")
ax.set_yticks(range(1, len(pts) + 1))
ax.set_yticklabels([p[0] for p in pts][::-1], fontsize=7.2)
ax.set_xlim(0, 4300)
ax.set_ylim(0.3, len(pts) + 1.2)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
ax.tick_params(axis="x", labelsize=7)
ax.grid(axis="y", visible=False)
save(fig, "targets_strip")

# ============================================ 23. guarantees: headline vs cash on balance sheet
fig, ax = plt.subplots(figsize=(4.6, 2.3))
rows_g = [("Headline customer guarantees", 16.5, BLUE_L), ("Third-party collateral, released toward contract end", 13.8, GREY_L),
          ("Cash on SanDisk's balance sheet (10-K)", 2.74, RED)]
for i, (lbl, v, c) in enumerate(rows_g):
    y = 2 - i
    ax.barh(y, v, height=0.55, color=c, lw=0, zorder=3)
    ax.text(v + 0.3, y, f"${v:,.1f}bn", va="center", fontsize=8, color=INK, fontweight="bold" if c == RED else "normal")
ax.set_yticks([2, 1, 0])
ax.set_yticklabels([r[0] for r in rows_g], fontsize=7.2)
ax.set_xlim(0, 21)
ax.set_xticks([])
ax.grid(visible=False)
ax.spines["bottom"].set_visible(False)
ax.text(0, -0.75, "cash = contract liabilities $1.24bn + refundable customer deposits $1.50bn", fontsize=6.8, color=INK2, va="top")
ax.set_ylim(-1.2, 2.6)
save(fig, "guarantees")

# ============================================ 24. price vs volume decomposition
fig, ax = plt.subplots(figsize=(4.4, 3.0))
per = ["FY26\nvs FY25", "FQ4-26\nvs FQ3", "FY27E\nvs FY26", "FY28E\nvs FY27E"]
bits = [15, 17, 15, 15]
price = [160, 34, 127, 3]
for i in range(4):
    ax.bar(i, bits[i], 0.56, color=MUTED, lw=0, zorder=3)
    ax.bar(i, price[i], 0.56, bottom=bits[i] + 1.5, color=RED if i < 2 else BLUE, lw=0, zorder=3)
    tot = bits[i] + price[i]
    ax.text(i, tot + 5, f"+{tot}%", ha="center", fontsize=8, color=INK, fontweight="bold")
    ax.text(i, bits[i] / 2, f"{bits[i]}", ha="center", va="center", fontsize=7, color=SURF, fontweight="bold")
    if price[i] > 12:
        ax.text(i, bits[i] + 1.5 + price[i] / 2, f"{price[i]}", ha="center", va="center", fontsize=7, color=SURF, fontweight="bold")
ax.set_xticks(range(4))
ax.set_xticklabels(per, fontsize=7.6)
ax.set_ylabel("Revenue growth, %")
ax.set_ylim(0, 205)
ax.grid(axis="x", visible=False)
handles = [plt.Rectangle((0, 0), 1, 1, color=c, lw=0) for c in (MUTED, RED, BLUE)]
ax.legend(handles, ["bits (guide: mid-teens)", "price and mix, reported", "price and mix, implied by consensus"], loc="upper right", fontsize=6.8, handlelength=1.0)
ax.set_title("Revenue growth split: bits vs price (price = residual)", loc="left", fontsize=8.4)
save(fig, "price_volume")

# ============================================ 25. risk matrix
fig, ax = plt.subplots(figsize=(4.4, 3.2))
from matplotlib.colors import LinearSegmentedColormap
cm = LinearSegmentedColormap.from_list("rm", ["#F7F7F7", RED_L, RED])
xx, yy = np.meshgrid(np.linspace(0, 1, 50), np.linspace(0, 1, 50))
ax.imshow((xx * yy) ** 0.7, extent=(0, 1, 0, 1), origin="lower", cmap=cm, alpha=0.85, aspect="auto")
risks = [(1, 0.86, 0.55, "Prices rise\nthrough CY27", "right", "bottom", -0.06, 0.05),
         (2, 0.42, 0.62, "Floors hold,\nnarrative persists", "right", "center", -0.06, 0.0),
         (3, 0.55, 0.86, "Flows, momentum,\nbuyback", "left", "center", 0.06, 0.0),
         (4, 0.86, 0.16, "Structural: HBF,\nAI-storage TAM", "right", "center", -0.06, 0.0),
         (5, 0.20, 0.15, "Squeeze / borrow", "left", "center", 0.06, 0.0),
         (6, 0.60, 0.38, "Timing off by\ntwo quarters", "right", "center", -0.06, 0.0)]
for n, x, y, lbl, ha, va, dx, dy in risks:
    ax.plot(x, y, "o", ms=15, color=INK, mec=SURF, mew=1.5, zorder=4)
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8, color=SURF, fontweight="bold", zorder=5)
    ax.text(x + dx, y + dy, lbl, fontsize=6.4, color=INK, ha=ha, va=va, linespacing=1.1)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xticks([0.15, 0.85])
ax.set_xticklabels(["low", "high"], fontsize=7)
ax.set_yticks([0.15, 0.85])
ax.set_yticklabels(["low", "high"], fontsize=7, rotation=90, va="center")
ax.set_xlabel("Impact on the thesis")
ax.set_ylabel("Probability")
ax.grid(visible=False)
save(fig, "risk_matrix")

# ============================================ 26. cash through the cycle
fig, ax = plt.subplots(figsize=(4.2, 2.3))
fcf = [-0.932, -0.475, -0.120, 11.494]
for i, v in enumerate(fcf):
    ax.bar(i, v, 0.56, color=RED if v > 0 else MUTED, lw=0, zorder=3)
    ax.text(i, v + (0.4 if v > 0 else -0.5), f"${v:,.1f}bn", ha="center", va="bottom" if v > 0 else "top", fontsize=7.8, color=INK)
ax.axhline(0, color="#C3C6CC", lw=0.8)
ax.set_xticks(range(4))
ax.set_xticklabels(["FY23", "FY24", "FY25", "FY26"], fontsize=7.8)
ax.set_ylim(-3, 14)
ax.set_ylabel("Free cash flow, $bn")
ax.grid(axis="x", visible=False)
ax.set_title("Three years of cash burn, then $11.5bn", loc="left", fontsize=8.4)
save(fig, "cash_cycle")

# ---- MC re-centred: post-contract GM N(60%, 15%), everything else unchanged (claim check)
rng = np.random.default_rng(11)
n_ = 5000
mid_gm = np.clip(rng.normal(0.60, 0.15, n_), 0.05, 0.85)
bitg = np.clip(rng.normal(0.18, 0.07, n_), 0.0, 0.40)
costd = np.clip(rng.normal(0.12, 0.04, n_), 0.0, 0.25)
wacc = rng.triangular(0.10, 0.115, 0.13, n_)
boom = np.clip(rng.normal(1.0, 0.12, n_), 0.5, 1.5)
floor = np.where(rng.random(n_) < 0.80, 1.0, rng.uniform(0.6, 0.9, n_))
v60 = np.array([engine.sop(mid_gm[i], bitg[i], costd[i], wacc[i], floor[i], boom[i]) for i in range(n_)])
NUM["mc60"] = dict(median=float(np.median(v60)), pct=float((v60 < S).mean() * 100), p_above=float((v60 > S).mean()),
                   p90=float(np.percentile(v60, 90)))
print("MC re-centred at 60% GM:", NUM["mc60"])
q_all = np.percentile(vals, [5, 10, 25, 50, 75, 90, 95])
NUM["mc_pctiles"] = dict(zip(["p5", "p10", "p25", "p50", "p75", "p90", "p95"], map(float, q_all)))
# IV cone for sizing
NUM["iv_cone"] = {m: float(atm_iv * np.sqrt(m / 12)) for m in (1, 3, 6)}
(FIG / "numbers.json").write_text(json.dumps(NUM, indent=1, default=float))
print("numbers.json written;", len(list(FIG.glob("*.png"))), "figures")
