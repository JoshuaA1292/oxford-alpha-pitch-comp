"""Polished deck-grade charts for the SNDK short pitch."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from quant.bl_density import implied_vol, fit_smile, rn_density
from quant.dcf import enterprise_value

DATA = Path(__file__).parent / "data" / "SNDK"
OUT = Path(__file__).parent / "outputs"
info = json.loads((DATA / "info.json").read_text())
S = info["currentPrice"]
shares, debt, cash = info["sharesOutstanding"], info["totalDebt"], info["totalCash"]
ASOF = "2026-09-09"
r = 0.0380

INK, ACC, SHORT, MUT = "#182230", "#1B3A6B", "#9E3B32", "#7B8494"
plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.22, "axes.spines.top": False,
                     "axes.spines.right": False, "font.family": "Avenir Next"})

# ---------- B-L density, domain restricted to quoted-strike range ----------
T = (pd.Timestamp("2027-01-15") - pd.Timestamp(ASOF)).days / 365
ivs, strikes = [], []
for f_, kind in (("calls", "call"), ("puts", "put")):
    df = pd.read_csv(DATA / f"{f_}_2027-01-15.csv")
    df = df[(df.bid > 0) & (df.ask > 0) & (df.openInterest.fillna(0) >= 50)]
    for _, row in df.iterrows():
        K = row.strike
        if (kind == "call") != (K >= S):
            continue
        iv = implied_vol(0.5 * (row.bid + row.ask), S, K, T, r, kind=kind)
        if np.isfinite(iv) and 0.05 < iv < 4:
            ivs.append(iv), strikes.append(K)
sfn, (klo, khi) = fit_smile(strikes, ivs, S)
# central region only: inside the quoted strikes, away from extrapolated wings
k_lo, k_hi = max(min(strikes) * 1.15, 400), min(max(strikes) * 0.95, 3600)
K, f = rn_density(S, T, r, sfn, k_lo, k_hi, n=4001)
f = f / np.trapezoid(f, K)

# ---------- Monte Carlo: contract-aware model (analysis/sndk_contract_dcf.py) ----------
cdcf = json.loads((OUT / "contract_dcf.json").read_text())
vals = np.load(OUT / "mc_contract_vals.npy")
med = float(np.median(vals))
pct = float((vals < S).mean() * 100)
bl = json.loads((OUT / "sndk_report.json").read_text())["bl"]["jan27"]["probs"]
p_target = bl.get("2125.0", np.nan)

# ---------- Chart 1: centerpiece ----------
fig, ax = plt.subplots(figsize=(9.2, 4.8))
ax.fill_between(K, f, alpha=0.30, color=ACC, lw=0)
ax.plot(K, f, color=ACC, lw=1.4,
        label="What the market prices in — option-implied density, Jan-2027")
hist, edges = np.histogram(vals[(vals > k_lo) & (vals < k_hi)], bins=80, density=True)
centers = 0.5 * (edges[1:] + edges[:-1])
scale = f.max() / hist.max()  # visual comparability; both are densities
ax.fill_between(centers, hist * scale, alpha=0.40, color=SHORT, lw=0)
ax.plot(centers, hist * scale, color=SHORT, lw=1.4,
        label="What we think it's worth — contract-aware Monte Carlo DCF, 20,000 paths")
ymax = max(f.max(), (hist * scale).max()) * 1.18
ax.set_ylim(0, ymax)
ax.axvline(S, color=INK, lw=1.5, ls="--")
ax.annotate(f"price ${S:,.0f}\n{pct:.0f}th pctile of\nour value dist.", (S, ymax * 0.70),
            xytext=(S + 60, ymax * 0.66), fontsize=8.5, color=INK)
ax.axvline(med, color=SHORT, lw=1.2, ls=":")
ax.annotate(f"our median\n${med:,.0f}  ({med/S-1:+.0%})", (med, ymax * 0.50),
            xytext=(med + 60, ymax * 0.50), fontsize=8.5, color=SHORT)
ax.axvline(2125, color=MUT, lw=1.2, ls=":")
ax.annotate(f"sell-side mean target $2,125\noptions price P(reach) = {p_target:.0%}",
            (2125, ymax * 0.30), xytext=(2180, ymax * 0.30), fontsize=8.5, color=MUT)
ax.set_yticks([])
ax.set_xlabel("SNDK share price ($)")
ax.set_title("SanDisk: our intrinsic-value distribution vs. the market's implied distribution",
             fontsize=12.5, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.text(0.01, 0.01, f"Sources: CBOE via Yahoo ({ASOF}, OI≥50, mid quotes, own IVs, spline in vol space, central region shown); own contract-aware DCF (consensus FY27-28 + NBM floor FY29-31 + post-contract mid-cycle). Densities independently normalized.",
         fontsize=6.8, color=MUT)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT / "centerpiece_mc_vs_market.png"); plt.close(fig)

# ---------- Chart 2: margin cycle (fixed axis) ----------
def gm(t):
    inc = pd.read_csv(Path(__file__).parent / "data" / t / "income_annual.csv", index_col=0)
    s = (inc.loc["Gross Profit"] / inc.loc["Total Revenue"]).dropna().astype(float)
    s.index = [int(c[:4]) for c in s.index]
    return s.sort_index()

sndk_gm, mu_gm = gm("SNDK"), gm("MU")
fig, ax = plt.subplots(figsize=(9.2, 4.4))
ax.plot(mu_gm.index, mu_gm.values * 100, "s-", color=ACC, lw=1.8, ms=6,
        label="Micron (FY ends Aug)")
ax.plot(sndk_gm.index, sndk_gm.values * 100, "o-", color=SHORT, lw=1.8, ms=6,
        label="SanDisk (FY ends Jun)")
for x, y in zip(sndk_gm.index, sndk_gm.values * 100):
    ax.annotate(f"{y:.0f}%", (x, y), xytext=(0, 8), textcoords="offset points",
                ha="center", fontsize=8.5, color=SHORT, fontweight="bold")
for x, y in zip(mu_gm.index, mu_gm.values * 100):
    ax.annotate(f"{y:.0f}%", (x, y), xytext=(0, -14), textcoords="offset points",
                ha="center", fontsize=8.5, color=ACC)
ax.axhline(0, color=INK, lw=0.8)
for lvl, lbl in ((46.9, "SanDisk standalone peak GM 47% (2010)"), (59.0, "Micron peak GM 59% (FY2018, DRAM+NAND)")):
    ax.axhline(lvl, color=MUT, lw=1.0, ls="--", alpha=0.8)
    ax.text(2022.05, lvl + 1.2, lbl, fontsize=8, color=MUT)
ax.text(2025.08, 6, "NAND pure-play median operating margin 2005–25: 9%\n(33 company-years; 30% of them loss-making)", fontsize=8, color=MUT)
ax.set_ylabel("Gross margin, %")
ax.set_xticks(sorted(set(sndk_gm.index) | set(mu_gm.index)))
ax.set_ylim(-15, 90)
ax.set_title("Memory gross margins: gross losses to 71% (FQ4: 85%) within three fiscal years",
             fontsize=12.5, loc="left", pad=10)
ax.legend(frameon=False, fontsize=9, loc="upper left")
fig.text(0.01, 0.01, "Source: company 10-K filings via Yahoo Finance. SanDisk FY23–25 as carve-out/standalone; FY26 includes the price-spike second half.",
         fontsize=6.8, color=MUT)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT / "margin_cycle.png"); plt.close(fig)

# ---------- Chart 3: what the price forces you to believe (contract bridge) ----------
req = cdcf["C_required"]; ev_bn = cdcf["ev"] / 1e9
pv2 = cdcf["A_pay2"]["pv"] / 1e9
pv_floor = (req["pv_paid"] - cdcf["A_pay2"]["pv"]) / 1e9
resid = req["residual"] / 1e9
fig, ax = plt.subplots(figsize=(9.2, 4.8))
ax.bar(0, ev_bn, 0.55, color=ACC, alpha=0.85)
ax.bar(1, pv2, 0.55, bottom=ev_bn - pv2, color=MUT, alpha=0.75)
ax.bar(2, pv_floor, 0.55, bottom=ev_bn - pv2 - pv_floor, color=MUT, alpha=0.55)
ax.bar(3, resid, 0.55, color=SHORT, alpha=0.85)
ax.text(0, ev_bn + 5, f"${ev_bn:,.0f}bn", ha="center", fontweight="bold", fontsize=10)
ax.text(1, ev_bn - pv2 / 2, f"−${pv2:,.0f}bn", ha="center", va="center", fontsize=9.5, color="white", fontweight="bold")
ax.text(2, ev_bn - pv2 - pv_floor / 2, f"−${pv_floor:,.0f}bn", ha="center", va="center", fontsize=9.5, color="white", fontweight="bold")
ax.text(3, resid + 5, f"${resid:,.0f}bn", ha="center", fontweight="bold", fontsize=10, color=SHORT)
ax.annotate(f"requires ${req['nopat_req']/1e9:,.0f}bn NOPAT / yr in perpetuity\nfrom FY32, after the contracts expire\n= a permanent {req['gm_req']:.0%} gross margin\n(NAND mid-cycle history: 25–40%)",
            (3, resid * 0.55), xytext=(3.5, resid * 0.75), fontsize=9.5, color=SHORT,
            arrowprops=dict(arrowstyle="->", color=SHORT))
ax.set_xticks([0, 1, 2, 3])
ax.set_xticklabels(["Enterprise value\ntoday", "PV of consensus\nFY27–28 profits\n(paid in full)",
                    "PV of contract-floor\nyears FY29–31\n(80% GM, paid in full)", "Residual:\nthe post-contract\nperpetuity"], fontsize=9)
ax.set_xlim(-0.5, 5.6)
ax.set_ylabel("$bn")
ax.set_title("What the price forces you to believe — after paying the Street AND the contracts",
             fontsize=12.5, loc="left", pad=10)
fig.text(0.01, 0.01, f"Consensus FY27/FY28 net income ${cdcf['consensus']['ni']['27']/1e9:.1f}bn/${cdcf['consensus']['ni']['28']/1e9:.1f}bn (Yahoo/LSEG, {ASOF}); NBM floor $93.9bn over FY27–31 at 80% GM (FQ4 call, 5 Aug 2026); 11% WACC; 2% terminal inflation.",
         fontsize=6.8, color=MUT)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT / "priced_in_waterfall.png"); plt.close(fig)
print("charts saved")
