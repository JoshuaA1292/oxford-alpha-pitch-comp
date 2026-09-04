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
r = 0.0377

INK, ACC, SHORT, MUT = "#182230", "#1B3A6B", "#9E3B32", "#7B8494"
plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.22, "axes.spines.top": False,
                     "axes.spines.right": False, "font.family": "Avenir Next"})

# ---------- B-L density, domain restricted to quoted-strike range ----------
T = (pd.Timestamp("2027-01-15") - pd.Timestamp("2026-09-02")).days / 365
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

# ---------- Monte Carlo (same params as sndk_exhibits) ----------
sales0 = info["totalRevenue"]
cons = [48.960e9, 57.787e9]
TAX, INC_F, INC_W, INFL = 0.13, 0.10, 0.05, 0.02
rng = np.random.default_rng(42)
N = 20000
rho, g_mu, g_sd, m_mu, m_sd = 0.7, -0.05, 0.12, 0.20, 0.07
L = np.linalg.cholesky(np.array([[g_sd**2, rho*g_sd*m_sd], [rho*g_sd*m_sd, m_sd**2]]))
vals = np.empty(N)
for i in range(N):
    g_post, m_mid = np.array([g_mu, m_mu]) + L @ rng.standard_normal(2)
    m_mid = float(np.clip(m_mid, 0.03, 0.45))
    g_post = float(np.clip(g_post, -0.30, 0.25))
    wacc = rng.triangular(0.10, 0.115, 0.13)
    growth = [cons[0]/sales0 - 1, cons[1]/cons[0] - 1] + [g_post]*3 + [0.04]*5
    margins = [0.62, 0.62] + list(np.linspace(0.62, m_mid, 4))[1:] + [m_mid]*5
    ev = enterprise_value(sales0, growth, margins, TAX, INC_F, INC_W, wacc, INFL, 10)
    vals[i] = max((ev - debt + cash) / shares, 0)
med = np.median(vals)

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
        label="What we think it's worth — Monte Carlo DCF, 20,000 paths")
ymax = max(f.max(), (hist * scale).max()) * 1.18
ax.set_ylim(0, ymax)
ax.axvline(S, color=INK, lw=1.5, ls="--")
ax.annotate(f"price ${S:,.0f}\n92nd pctile of\nour value dist.", (S, ymax * 0.86),
            xytext=(S + 90, ymax * 0.82), fontsize=8.5, color=INK)
ax.axvline(med, color=SHORT, lw=1.2, ls=":")
ax.annotate(f"our median\n${med:,.0f}  (−39%)", (med, ymax * 0.60),
            xytext=(med - 420, ymax * 0.62), fontsize=8.5, color=SHORT)
ax.axvline(2125, color=MUT, lw=1.2, ls=":")
ax.annotate("sell-side mean target $2,125\noptions price P(reach) = 14%",
            (2125, ymax * 0.40), xytext=(2180, ymax * 0.44), fontsize=8.5, color=MUT)
ax.set_yticks([])
ax.set_xlabel("SNDK share price ($)")
ax.set_title("SanDisk: our intrinsic-value distribution vs. the market's implied distribution",
             fontsize=12.5, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.text(0.01, 0.01, "Sources: CBOE via Yahoo (2 Sep 2026, OI≥50, mid quotes, own IVs, spline in vol space, central region shown); own 7-driver DCF. Densities independently normalized.",
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
ax.axhspan(10, 35, color=MUT, alpha=0.10)
ax.text(2022.05, 30.5, "range containing every pre-2026 cycle peak", fontsize=8, color=MUT)
ax.set_ylabel("Gross margin, %")
ax.set_xticks(sorted(set(sndk_gm.index) | set(mu_gm.index)))
ax.set_ylim(-15, 82)
ax.set_title("Memory gross margins: gross losses to 70%+ within three fiscal years",
             fontsize=12.5, loc="left", pad=10)
ax.legend(frameon=False, fontsize=9, loc="upper left")
fig.text(0.01, 0.01, "Source: company 10-K filings via Yahoo Finance. SanDisk FY23–25 as carve-out/standalone; FY26 includes the price-spike second half.",
         fontsize=6.8, color=MUT)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT / "margin_cycle.png"); plt.close(fig)

# ---------- Chart 3: what the price forces you to believe (waterfall) ----------
fig, ax = plt.subplots(figsize=(9.2, 4.6))
labels = ["Enterprise value\n$220bn", "PV of consensus\nFY27–28 profits\n(paid in full)",
          "Residual:\nwhat's left to earn", "= perpetual NOPAT\nrequired from FY29,\nforever"]
ev_bn, pv_bn = 219.9, 59.7
vals_bar = [ev_bn, -pv_bn, ev_bn - pv_bn, 0]
starts = [0, ev_bn - pv_bn, 0, 0]
ax.bar(0, ev_bn, 0.55, color=ACC, alpha=0.85)
ax.bar(1, pv_bn, 0.55, bottom=ev_bn - pv_bn, color=MUT, alpha=0.7)
ax.bar(2, ev_bn - pv_bn, 0.55, color=SHORT, alpha=0.85)
ax.text(0, ev_bn + 4, "$220bn", ha="center", fontweight="bold", fontsize=10)
ax.text(1, ev_bn - pv_bn / 2, "−$60bn", ha="center", fontsize=9.5, color="white", fontweight="bold")
ax.text(2, ev_bn - pv_bn + 4, "$160bn", ha="center", fontweight="bold", fontsize=10, color=SHORT)
ax.annotate("requires $17.4bn NOPAT / yr in perpetuity\n= 34× SanDisk's best pre-boom year ever\n(FY25 operating income: $0.51bn)",
            (2, 100), xytext=(2.45, 120), fontsize=9.5, color=SHORT,
            arrowprops=dict(arrowstyle="->", color=SHORT))
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(labels[:3], fontsize=9)
ax.set_xlim(-0.5, 4.4)
ax.set_ylabel("$bn")
ax.set_title("What $220bn of enterprise value forces you to believe — using the Street's own estimates",
             fontsize=12.5, loc="left", pad=10)
fig.text(0.01, 0.01, "Consensus FY27/FY28 net income $31.3bn/$38.8bn (Yahoo consensus, 2 Sep 2026) discounted at 11% WACC; residual as perpetuity with 2% inflation. Sensitivity: $15.1–19.8bn at 10–12% WACC.",
         fontsize=6.8, color=MUT)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT / "priced_in_waterfall.png"); plt.close(fig)
print("charts saved")
