"""SNDK short-thesis exhibits: B-L option-implied density, Monte Carlo DCF,
positioning/skew, margin-cycle history, beta. Saves charts to analysis/outputs.

Run:  analysis/.venv/bin/python analysis/sndk_exhibits.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from quant.bl_density import implied_vol, fit_smile, rn_density, density_stats, bs_call
from quant.dcf import enterprise_value

DATA = Path(__file__).parent / "data" / "SNDK"
OUT = Path(__file__).parent / "outputs"
OUT.mkdir(exist_ok=True)

info = json.loads((DATA / "info.json").read_text())
S = info["currentPrice"]
shares, debt, cash = info["sharesOutstanding"], info["totalDebt"], info["totalCash"]
r = 0.0377  # 13w T-bill (^IRX) 3.77%
report = {}

plt.rcParams.update({"figure.dpi": 140, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False})

# ---------- 1. Breeden-Litzenberger ----------
def bl_for(expiry, T_years, min_oi=50):
    calls = pd.read_csv(DATA / f"calls_{expiry}.csv")
    puts = pd.read_csv(DATA / f"puts_{expiry}.csv")
    ivs, strikes, used = [], [], {"calls": 0, "puts": 0}
    for df, kind in ((calls, "call"), (puts, "put")):
        df = df[(df.bid > 0) & (df.ask > 0) & (df.openInterest.fillna(0) >= min_oi)]
        for _, row in df.iterrows():
            K = row.strike
            otm = (K >= S) if kind == "call" else (K <= S)
            if not otm:
                continue
            mid = 0.5 * (row.bid + row.ask)
            iv = implied_vol(mid, S, K, T_years, r, kind=kind)
            if np.isfinite(iv) and 0.05 < iv < 4.0:
                ivs.append(iv); strikes.append(K); used[kind + "s"] += 1
    sigma_fn, (klo, khi) = fit_smile(strikes, ivs, S)
    K, f = rn_density(S, T_years, r, sigma_fn, max(klo, 100), min(khi, 6000), n=4001)
    raw_integral = float(np.trapezoid(f, K))
    f = f / raw_integral  # renormalize over observed strike range (truncation disclosed)
    st = density_stats(K, f, thresholds=(S, 1161.0, 756.0, 2354.0, 1000.0))
    st["integral"] = raw_integral
    # model-free cross-check: P(S_T > K) = -e^{rT} dC/dK via tight call spread
    def digital(Kx, h=5.0):
        c1 = bs_call(S, Kx - h, T_years, r, float(sigma_fn(Kx - h)))
        c2 = bs_call(S, Kx + h, T_years, r, float(sigma_fn(Kx + h)))
        return np.exp(r * T_years) * (c1 - c2) / (2 * h)
    st["digital_check"] = {k: digital(k) for k in (S, 1161.0, 756.0)}
    atm_iv = float(sigma_fn(S))
    # 25-delta risk reversal from fitted smile
    from scipy.stats import norm
    def delta_call(K):
        sig = float(sigma_fn(K))
        d1 = (np.log(S/K) + (r + 0.5*sig**2)*T_years)/(sig*np.sqrt(T_years))
        return norm.cdf(d1)
    from scipy.optimize import brentq
    k25c = brentq(lambda K: delta_call(K) - 0.25, S, khi)
    k25p = brentq(lambda K: delta_call(K) - 0.75, klo, S)
    rr25 = float(sigma_fn(k25c)) - float(sigma_fn(k25p))
    return dict(K=K, f=f, stats=st, atm_iv=atm_iv, rr25=rr25,
                n_quotes=used, k25c=k25c, k25p=k25p)

res_jan = bl_for("2027-01-15", (pd.Timestamp("2027-01-15") - pd.Timestamp("2026-09-02")).days / 365)
res_mar = bl_for("2027-03-19", (pd.Timestamp("2027-03-19") - pd.Timestamp("2026-09-02")).days / 365)

for label, res in (("Jan-2027", res_jan), ("Mar-2027", res_mar)):
    st = res["stats"]
    print(f"[B-L {label}] quotes used {res['n_quotes']}, ATM IV {res['atm_iv']:.0%}, "
          f"25d RR {res['rr25']:+.1%}")
    print(f"   pre-norm integral {st['integral']:.3f} | RN mean {st['mean']:,.0f} (fwd {S*np.exp(r* (0.37 if label=='Jan-2027' else 0.54)):,.0f})")
    for k, p in st["probs"].items():
        chk = st["digital_check"].get(k)
        extra = f"  [call-spread check: {chk:.1%}]" if chk is not None else ""
        print(f"   P(S_T > {k:,.0f}) = {p:.1%}{extra}")
report["bl"] = {lbl: {"atm_iv": res["atm_iv"], "rr25": res["rr25"],
                       "probs": {str(k): v for k, v in res["stats"]["probs"].items()},
                       "integral": res["stats"]["integral"]}
                for lbl, res in (("jan27", res_jan), ("mar27", res_mar))}

# ---------- 2. Monte Carlo DCF ----------
# FY27-28: consensus revenue; boom margin 62% fading over 3 yrs to drawn
# mid-cycle margin; post-FY28 growth drawn, correlated with margin (busts
# hit price->revenue AND margin together).
sales0 = info["totalRevenue"]
cons = [48.960e9, 57.787e9]
TAX, INC_F, INC_W, INFL = 0.13, 0.10, 0.05, 0.02
rng = np.random.default_rng(42)
N = 20000
rho = 0.7
g_mu, g_sd = -0.05, 0.12      # post-boom annual growth, FY29-31
m_mu, m_sd = 0.20, 0.07       # mid-cycle EBITA margin
cov = np.array([[g_sd**2, rho*g_sd*m_sd], [rho*g_sd*m_sd, m_sd**2]])
L = np.linalg.cholesky(cov)
vals = np.empty(N)
i = 0
rej = 0
while i < N:
    z = rng.standard_normal(2)
    g_post, m_mid = np.array([g_mu, m_mu]) + L @ z
    m_mid = float(np.clip(m_mid, 0.03, 0.45))
    g_post = float(np.clip(g_post, -0.30, 0.25))
    wacc = rng.triangular(0.10, 0.115, 0.13)
    growth = [cons[0]/sales0 - 1, cons[1]/cons[0] - 1] + [g_post]*3 + [0.04]*5
    margins = [0.62, 0.62] + list(np.linspace(0.62, m_mid, 4))[1:] + [m_mid]*5
    ev = enterprise_value(sales0, growth, margins, TAX, INC_F, INC_W, wacc, INFL, 10)
    vals[i] = (ev - debt + cash) / shares
    i += 1
vals = np.maximum(vals, 0)
q = np.percentile(vals, [5, 25, 50, 75, 95])
p_above = float((vals > S).mean())
print(f"\n[MC] n={N}: p5 ${q[0]:,.0f} p25 ${q[1]:,.0f} MEDIAN ${q[2]:,.0f} p75 ${q[3]:,.0f} p95 ${q[4]:,.0f}")
print(f"     P(intrinsic > price ${S:,.0f}) = {p_above:.1%} | price sits at {float((vals<S).mean())*100:.0f}th percentile of intrinsic value")
report["mc"] = {"p5": q[0], "p25": q[1], "median": q[2], "p75": q[3], "p95": q[4],
                "prob_above_price": p_above}

# ---------- 3. Margin cycle history ----------
def gm_series(t):
    inc = pd.read_csv(Path(__file__).parent / "data" / t / "income_annual.csv", index_col=0)
    rev = inc.loc["Total Revenue"]; gp = inc.loc["Gross Profit"]
    gm = (gp / rev).dropna()
    gm.index = [c[:4] for c in gm.index]
    return gm.astype(float).iloc[::-1]

sndk_gm, mu_gm = gm_series("SNDK"), gm_series("MU")
sndk_q = pd.read_csv(DATA / "income_quarterly.csv", index_col=0)
q_gm = (sndk_q.loc["Gross Profit"] / sndk_q.loc["Total Revenue"]).dropna().astype(float).iloc[::-1]
print("\n[margins] SNDK annual GM:", {k: f"{v:.0%}" for k, v in sndk_gm.items()})
print("          SNDK quarterly GM:", {k[:7]: f"{v:.0%}" for k, v in q_gm.items()})
print("          MU annual GM:", {k: f"{v:.0%}" for k, v in mu_gm.items()})
report["margins"] = {"sndk_annual": sndk_gm.to_dict(), "mu_annual": mu_gm.to_dict(),
                     "sndk_quarterly": {k[:10]: v for k, v in q_gm.items()}}

# ---------- 4. Beta vs SMH / QQQ ----------
import yfinance as yf
px = pd.read_csv(DATA / "prices.csv", index_col=0)
px.index = pd.to_datetime(px.index, utc=True)
bench = yf.download(["SMH", "QQQ"], period="18mo", auto_adjust=True, progress=False)["Close"]
bench.index = bench.index.tz_localize("UTC") if bench.index.tz is None else bench.index
sndk_ret = px["Close"].pct_change().rename("SNDK")
sndk_ret.index = sndk_ret.index.date
bench_ret = bench.pct_change()
bench_ret.index = pd.to_datetime(bench_ret.index).date
rets = pd.concat([sndk_ret, bench_ret], axis=1, sort=False).dropna()
import statsmodels.api as sm  # noqa
for b in ("SMH", "QQQ"):
    X = sm.add_constant(rets[b]); y = rets["SNDK"]
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    print(f"[beta] SNDK vs {b}: beta {fit.params[b]:.2f} (t={fit.tvalues[b]:.1f}), R2 {fit.rsquared:.0%}, ann.idio vol {np.std(fit.resid)*np.sqrt(252):.0%}")
    report.setdefault("beta", {})[b] = {"beta": fit.params[b], "r2": fit.rsquared,
                                        "idio_vol": float(np.std(fit.resid)*np.sqrt(252))}

# ---------- 5. Charts ----------
INK, ACC, LONG, SHORT = "#182230", "#1B3A6B", "#1E6E4E", "#9E3B32"

# 5a. Centerpiece: MC intrinsic distribution vs B-L market-implied density
fig, ax = plt.subplots(figsize=(9, 4.6))
Kj, fj = res_jan["K"], res_jan["f"]
ax.fill_between(Kj, fj / np.trapezoid(fj, Kj), alpha=0.35, color=ACC,
                label="Market prices in (option-implied density, Jan-27)")
hist, edges = np.histogram(vals[vals < 4000], bins=90, density=True)
centers = 0.5 * (edges[1:] + edges[:-1])
ax.fill_between(centers, hist, alpha=0.45, color=SHORT,
                label="Our intrinsic value (Monte Carlo DCF, 20k paths)")
ax.axvline(S, color=INK, lw=1.6, ls="--")
ax.text(S * 1.02, ax.get_ylim()[1] * 0.92, f"price ${S:,.0f}", fontsize=9)
for x, lbl in [(q[2], f"MC median ${q[2]:,.0f}")]:
    ax.axvline(x, color=SHORT, lw=1.2, ls=":")
    ax.text(x * 0.98, ax.get_ylim()[1] * 0.78, lbl, fontsize=8.5, ha="right", color=SHORT)
ax.set_xlim(0, 4000); ax.set_yticks([])
ax.set_xlabel("SNDK share price ($)")
ax.set_title("What we think it's worth vs. what the market prices in", fontsize=12, loc="left")
ax.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "centerpiece_mc_vs_market.png"); plt.close(fig)

# 5b. Margin cycle
fig, ax = plt.subplots(figsize=(9, 4.2))
years_all = sorted(set(sndk_gm.index) | set(mu_gm.index))
ax.plot(sndk_gm.index, sndk_gm.values * 100, "o-", color=SHORT, label="SanDisk GM% (FY Jun)")
ax.plot(mu_gm.index, mu_gm.values * 100, "s-", color=ACC, label="Micron GM% (FY Aug)")
ax.axhline(0, color=INK, lw=0.8)
ax.set_ylabel("Gross margin %")
ax.set_title("Memory gross margins: from gross losses to 70%+ in three years", fontsize=12, loc="left")
ax.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "margin_cycle.png"); plt.close(fig)

(OUT / "sndk_report.json").write_text(json.dumps(report, indent=2, default=float))
print("\ncharts + report saved to analysis/outputs/")
