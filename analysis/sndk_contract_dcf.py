"""Contract-aware valuation of SanDisk: pay the Street's boom years AND the
full New-Business-Model (NBM) contract floor, then ask what the residual
price requires after the contracts expire.

Facts hard-coded here come from the FQ4-FY26 earnings release / call
(5 Aug 2026, sec.gov 0001628280-26-053346) and Yahoo/LSEG consensus in
analysis/data/SNDK (pulled 9 Sep 2026). Update `ASOF` block when refreshed.

Run:  analysis/.venv/bin/python analysis/sndk_contract_dcf.py
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

DATA = Path(__file__).parent / "data" / "SNDK"
OUT = Path(__file__).parent / "outputs"
OUT.mkdir(exist_ok=True)
info = json.loads((DATA / "info.json").read_text())
est = pd.read_csv(DATA / "earnings_estimate.csv").set_index("period")
rev_est = pd.read_csv(DATA / "revenue_estimate.csv").set_index("period")

# ----------------------------------------------------------------- inputs
ASOF = "2026-09-09"
S = info["currentPrice"]
SHARES = info["sharesOutstanding"]              # 146.4m (Yahoo); company diluted ~155m
DEBT, CASH = info["totalDebt"], info["totalCash"]
MKTCAP = S * SHARES
EV = MKTCAP + DEBT - CASH

# Street: FY27/FY28 (Jun year-end) revenue and EPS consensus
CONS_REV = {27: rev_est.loc["0y", "avg"], 28: rev_est.loc["+1y", "avg"]}
CONS_EPS = {27: est.loc["0y", "avg"], 28: est.loc["+1y", "avg"]}
CONS_NI = {y: CONS_EPS[y] * SHARES for y in (27, 28)}

# Company disclosures (FQ4-FY26 call, 5 Aug 2026)
NBM_FLOOR_TOTAL = 93.9e9      # "minimum of $93.9bn ... assuming floor pricing"
NBM_YEARS = (27, 28, 29, 30, 31)   # "up to 5 years, weighted avg > 4 years"
NBM_FLOOR_PER_YEAR = NBM_FLOOR_TOTAL / len(NBM_YEARS)   # ~$18.8bn/yr
NBM_GM_AT_FLOOR = 0.80        # "expect to be around 80% ... even at floor pricing"
NBM_BIT_SHARE = {27: 0.50, 28: 0.67, 29: 0.67, 30: 0.67, 31: 0.67}
FY26_REV, FY26_GM = 20.248e9, 0.715
FY26_COGS = FY26_REV * (1 - FY26_GM)          # $5.8bn cash cost base for FY26 bits
OPEX_FY27 = 0.530e9 * 4                       # guide $520-540m/qtr non-GAAP
OPEX_GROWTH = 0.05
TAX = 0.15                                    # guided non-GAAP tax rate
WACC, INFL = 0.11, 0.02                       # base; 10-13% band shown
BIT_GROWTH = 0.15                             # "mid-teens" sellable bit growth
COST_PER_BIT_DECLINE = 0.12                   # nodal-transition productivity
INC_CAPITAL = 0.15                            # (fixed + WC) per $ of revenue growth
SNDK_FY2014_OPINC = 1.56e9                    # standalone SanDisk peak: FY2014 op income $1.56bn on $6.63bn (10-K)
NBM_DURATION_YRS = 4.5                        # "weighted average duration of over 4 years"


def pv(cf, year_index, wacc=WACC):
    """PV to today of cash flow received at fiscal year `year_index` (1 = FY27)."""
    return cf / (1 + wacc) ** year_index


def nopat(revenue, gm, opex, tax=TAX):
    return (revenue * gm - opex) * (1 - tax)


# ------------------------------------------------ A. pay 2 boom years
pv_boom2 = sum(pv(CONS_NI[y], y - 26) for y in (27, 28))
resid2 = EV - pv_boom2
# residual = NOPAT_perp*(1+i)/(w-i) discounted 2 years
perp2 = resid2 * (1 + WACC) ** 2 * (WACC - INFL) / (1 + INFL)

# ------------------------------------------------ B. pay full contract life at peak
ni_path_B = {27: CONS_NI[27], 28: CONS_NI[28], 29: CONS_NI[28], 30: CONS_NI[28], 31: CONS_NI[28]}
pv_boom5 = sum(pv(v, y - 26) for y, v in ni_path_B.items())
resid5 = EV - pv_boom5
perp5 = resid5 * (1 + WACC) ** 5 * (WACC - INFL) / (1 + INFL)

# ------------------------------------------------ C. sum-of-parts with contract floor
def sop(mid_gm, bit_growth=BIT_GROWTH, cost_decline=COST_PER_BIT_DECLINE,
        wacc=WACC, floor_haircut=1.0, boom_mult=1.0, verbose=False):
    """Value/share when:
       FY27-28  = consensus in full (x boom_mult)
       FY29-31  = NBM floor revenue (x floor_haircut) at 80% GM  +  non-NBM bits at mid_gm
       FY32+    = everything at mid-cycle: revenue = cash cost base / (1 - mid_gm)
    Cost base grows with bits and shrinks with cost-per-bit declines."""
    rows = []
    ev = 0.0
    opex = OPEX_FY27
    cogs = FY26_COGS
    for y in range(27, 37):
        t = y - 26
        cogs *= (1 + bit_growth) * (1 - cost_decline)
        if y in (27, 28):
            rev = CONS_REV[y] * boom_mult
            n = CONS_NI[y] * boom_mult
            gm = np.nan
        elif y in (29, 30, 31):
            nbm_rev = NBM_FLOOR_PER_YEAR * floor_haircut
            # non-NBM bits: (1-share)/share of NBM bits, priced at mid-cycle economics
            nbm_cogs = cogs * NBM_BIT_SHARE[y]
            non_cogs = cogs * (1 - NBM_BIT_SHARE[y])
            non_rev = non_cogs / (1 - mid_gm)
            rev = nbm_rev + non_rev
            gp = (nbm_rev - nbm_cogs) + (non_rev - non_cogs)
            gm = gp / rev
            n = (gp - opex) * (1 - TAX)
        else:
            rev = cogs / (1 - mid_gm)
            gm = mid_gm
            n = (rev * gm - opex) * (1 - TAX)
        prev_rev = rows[-1]["rev"] if rows else FY26_REV
        fcf = n - INC_CAPITAL * max(rev - prev_rev, 0)
        ev += pv(fcf, t, wacc)
        rows.append(dict(fy=y, rev=rev, gm=gm, nopat=n, fcf=fcf, cogs=cogs, opex=opex))
        opex *= 1 + OPEX_GROWTH
    tv = rows[-1]["nopat"] * (1 + INFL) / (wacc - INFL)
    ev += pv(tv, 10, wacc)
    val = (ev - DEBT + CASH) / SHARES
    if verbose:
        return val, ev, pd.DataFrame(rows)
    return val


def required_post_contract(wacc=WACC, mid_gm_for_noncontract=0.40):
    """After paying consensus FY27-28 and the FY29-31 floor years, what
    perpetual NOPAT (and gross margin on the projected cost base) must the
    post-contract business earn to justify EV?"""
    _, _, df = sop(mid_gm_for_noncontract, wacc=wacc, verbose=True)
    pv_paid = sum(pv(r.fcf, r.fy - 26, wacc) for r in df.itertuples() if r.fy <= 31)
    resid = EV - pv_paid
    nopat_req = resid * (1 + wacc) ** 5 * (wacc - INFL) / (1 + INFL)
    cogs32, opex32 = df.loc[df.fy == 32, "cogs"].item(), df.loc[df.fy == 32, "opex"].item()
    ebita_req = nopat_req / (1 - TAX)
    rev_req = ebita_req + opex32 + cogs32
    gm_req = 1 - cogs32 / rev_req
    return dict(pv_paid=pv_paid, residual=resid, nopat_req=nopat_req, gm_req=gm_req,
                rev_req=rev_req, cogs32=cogs32)


# ------------------------------------------------ D. Monte Carlo on the contract structure
def monte_carlo(n=20000, seed=11):
    rng = np.random.default_rng(seed)
    vals = np.empty(n)
    draws = {}
    # Deliberately generous to the bull case so the price is reachable:
    # post-contract GM centred at 45% (NAND history 25-40%; 2026 peak 85%),
    # bit growth centred at 18% (company: mid-teens; AI-storage bulls: 25-30%).
    mid_gm = np.clip(rng.normal(0.45, 0.15, n), 0.05, 0.85)
    bitg = np.clip(rng.normal(0.18, 0.07, n), 0.0, 0.40)
    costd = np.clip(rng.normal(0.12, 0.04, n), 0.0, 0.25)
    wacc = rng.triangular(0.10, 0.115, 0.13, n)
    boom = np.clip(rng.normal(1.0, 0.12, n), 0.5, 1.5)            # consensus hit/miss
    floor = np.where(rng.random(n) < 0.80, 1.0, rng.uniform(0.6, 0.9, n))  # 20% renegotiation risk
    for i in range(n):
        vals[i] = sop(mid_gm[i], bitg[i], costd[i], wacc[i], floor[i], boom[i])
    vals = np.maximum(vals, 0)
    draws = dict(mid_gm=mid_gm, bitg=bitg, costd=costd, wacc=wacc, boom=boom, floor=floor)
    return vals, draws


if __name__ == "__main__":
    print(f"SNDK {ASOF}: price ${S:,.0f} | mkt cap ${MKTCAP/1e9:,.1f}bn | EV ${EV/1e9:,.1f}bn | shares {SHARES/1e6:.1f}m")
    print(f"Consensus FY27 rev ${CONS_REV[27]/1e9:.1f}bn EPS ${CONS_EPS[27]:.0f} -> NI ${CONS_NI[27]/1e9:.1f}bn | "
          f"FY28 rev ${CONS_REV[28]/1e9:.1f}bn EPS ${CONS_EPS[28]:.0f} -> NI ${CONS_NI[28]/1e9:.1f}bn")
    print(f"NBM floor ${NBM_FLOOR_TOTAL/1e9:.1f}bn over FY27-31 = ${NBM_FLOOR_PER_YEAR/1e9:.1f}bn/yr at {NBM_GM_AT_FLOOR:.0%} GM")

    print("\n[A] Pay the Street's two boom years in full (consensus net income, discounted at 11%)")
    print(f"    PV FY27-28 = ${pv_boom2/1e9:.1f}bn ({pv_boom2/EV:.0%} of EV) | residual ${resid2/1e9:.1f}bn")
    print(f"    -> requires perpetual NOPAT of ${perp2/1e9:.1f}bn/yr from FY29, forever")
    for w in (0.10, 0.12, 0.13):
        p2 = sum(pv(CONS_NI[y], y - 26, w) for y in (27, 28))
        print(f"       WACC {w:.0%}: ${(EV-p2)*(1+w)**2*(w-INFL)/(1+INFL)/1e9:.1f}bn/yr")

    print("\n[B] Pay FIVE boom years (the whole contract life) at FY28 consensus, forever after that?")
    print(f"    PV FY27-31 = ${pv_boom5/1e9:.1f}bn ({pv_boom5/EV:.0%} of EV) | residual ${resid5/1e9:.1f}bn")
    print(f"    -> still requires perpetual NOPAT of ${perp5/1e9:.1f}bn/yr from FY32, forever")

    print("\n[C] Sum-of-parts: consensus FY27-28 + contract floor FY29-31 + post-contract mid-cycle")
    base_val, base_ev, df = sop(0.40, verbose=True)
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
    show = df.assign(rev=df.rev/1e9, nopat=df.nopat/1e9, fcf=df.fcf/1e9, cogs=df.cogs/1e9, opex=df.opex/1e9)
    print(show[["fy", "rev", "gm", "cogs", "opex", "nopat", "fcf"]].to_string(index=False))
    print(f"    mid-cycle GM 40%: EV ${base_ev/1e9:.1f}bn -> ${base_val:,.0f}/share ({base_val/S-1:+.0%})")
    print("    Value/share by post-contract mid-cycle gross margin (bit growth 15%, cost/bit -12%):")
    for gm in (0.30, 0.40, 0.50, 0.60, 0.70, 0.80):
        v = sop(gm)
        print(f"       GM {gm:.0%}: ${v:,.0f}  ({v/S-1:+.0%})")
    print("    Sensitivity: value/share, mid-cycle GM (rows) x bit growth (cols)")
    grid = pd.DataFrame({f"{bg:.0%}": [sop(gm, bit_growth=bg) for gm in (0.3, 0.4, 0.5, 0.6, 0.7)]
                         for bg in (0.10, 0.15, 0.20, 0.25, 0.30)},
                        index=[f"GM {gm:.0%}" for gm in (0.3, 0.4, 0.5, 0.6, 0.7)])
    print(grid.round(0).to_string())
    print("    Sensitivity: value/share, mid-cycle GM (rows) x WACC (cols)")
    grid_w = pd.DataFrame({f"{w:.0%}": [sop(gm, wacc=w) for gm in (0.3, 0.4, 0.5, 0.6, 0.7)]
                           for w in (0.10, 0.11, 0.12, 0.13)},
                          index=[f"GM {gm:.0%}" for gm in (0.3, 0.4, 0.5, 0.6, 0.7)])
    print(grid_w.round(0).to_string())

    print("\n[C'] What the price requires AFTER paying consensus FY27-28 and the contract-floor years:")
    req = required_post_contract()
    print(f"    PV of everything through FY31 = ${req['pv_paid']/1e9:.1f}bn | residual ${req['residual']/1e9:.1f}bn")
    print(f"    -> post-contract perpetual NOPAT ${req['nopat_req']/1e9:.1f}bn/yr on a ${req['cogs32']/1e9:.1f}bn cost base")
    print(f"    -> implied PERMANENT gross margin {req['gm_req']:.0%} (revenue ${req['rev_req']/1e9:.1f}bn/yr) after the contracts expire")
    for bg in (0.20, 0.30):
        # faster bit growth => bigger cost base => lower required GM; show it
        _, _, d2 = sop(0.40, bit_growth=bg, verbose=True)
        pv_paid = sum(pv(r.fcf, r.fy - 26) for r in d2.itertuples() if r.fy <= 31)
        nreq = (EV - pv_paid) * (1 + WACC) ** 5 * (WACC - INFL) / (1 + INFL)
        c32, o32 = d2.loc[d2.fy == 32, "cogs"].item(), d2.loc[d2.fy == 32, "opex"].item()
        gmr = 1 - c32 / (nreq / (1 - TAX) + o32 + c32)
        print(f"       with {bg:.0%} bit growth: required permanent GM {gmr:.0%}")

    print("\n[E] Floor arithmetic and the corrected 'best year' base")
    floor_run_rate = NBM_FLOOR_TOTAL / NBM_DURATION_YRS
    floor_all_bits = floor_run_rate / NBM_BIT_SHARE[28]
    print(f"    $93.9bn over {NBM_DURATION_YRS} yrs = ${floor_run_rate/1e9:.1f}bn/yr for ~{NBM_BIT_SHARE[28]:.0%} of FY28 bits")
    print(f"    -> floor pricing applied to ALL bits ~ ${floor_all_bits/1e9:.1f}bn/yr = {floor_all_bits/CONS_REV[28]-1:+.0%} vs FY28 consensus ${CONS_REV[28]/1e9:.1f}bn")
    print(f"    Required perpetual NOPAT vs SanDisk's best standalone year (FY2014 op income $1.56bn):")
    print(f"       after 2 boom years: {perp2/SNDK_FY2014_OPINC:.0f}x | after 5 boom years: {perp5/SNDK_FY2014_OPINC:.0f}x | post-contract: {req['nopat_req']/SNDK_FY2014_OPINC:.0f}x")
    print("\n[F] 12-month scenario targets (what the market pays once the terminal narrative breaks)")
    # Targets are multiple x FY28 EPS under each scenario; every input is stated so it can be attacked.
    # Precedent: MU traded 4-6x forward EPS through the 2018-19 rollover; SNDK itself fell 47% peak-to-trough Jun-Aug 2026.
    SCEN12 = {
        # name: (weight, FY28 revenue, FY28 op margin, multiple, note)
        "Base: contract prices flat by 1Q27, down from 2Q27": (0.50, 38e9, 0.60, 7.0, "consensus FY28 rev cut ~35%, OM 60% (floors cushion), 7x = cyclical at rollover"),
        "Deep bust: bullwhip + China supply, floors renegotiated": (0.20, 30e9, 0.45, 8.0, "revenue back to ~FQ4-26 run-rate, OM 45%, 8x on trough-ish EPS"),
        "Against us: prices rise through CY27, FY28 consensus holds": (0.30, CONS_REV[28], 0.75, 9.0, "consensus $57.8bn at mgmt 75% OM, Citi's 9x 'mature cyclical' multiple"),
    }
    ev_ret, up, dn = 0.0, 0.0, 0.0
    scen_rows = {}
    for name, (w, rev, om, mult, note) in SCEN12.items():
        eps = rev * om * (1 - TAX) / SHARES
        tgt = eps * mult
        ret = (S - tgt) / S
        ev_ret += w * ret
        up += w * max(ret, 0); dn += w * max(-ret, 0)
        scen_rows[name] = dict(weight=w, fy28_rev=rev, fy28_om=om, fy28_eps=eps, multiple=mult, target=tgt, short_return=ret)
        print(f"    {name:<58} w={w:.0%}  FY28 EPS ${eps:,.0f} x {mult:.0f} = ${tgt:,.0f}  ({tgt/S-1:+.0%})  short {ret:+.0%}")
        print(f"        {note}")
    print(f"    Probability-weighted 12-month short return {ev_ret:+.1%} | reward/risk {up/dn:.1f}:1 (weights 50/20/30)")
    # what the bulls' own 'through-cycle' frameworks imply at the current price
    print("\n[G] The Street's own normalised-earnings maths at today's price")
    for who, eps_n, mult_n in (("Morgan Stanley through-cycle EPS", 76.0, 23.0), ("Goldman normalised EPS", 110.0, 20.0),
                               ("Bernstein FY30 floor-stress EPS", 214.0, None)):
        ni = eps_n * SHARES
        line = f"    {who:<36} ${eps_n:>4.0f}/sh = ${ni/1e9:5.1f}bn NI | price is {S/eps_n:4.1f}x it"
        if mult_n:
            line += f" | their multiple {mult_n:.0f}x -> ${eps_n*mult_n:,.0f}"
        print(line)
    print(f"    vs. perpetual NOPAT the price needs after 5 peak years: ${perp5/1e9:.1f}bn/yr; after 2 peak years: ${perp2/1e9:.1f}bn/yr")

    print("\n[D] Monte Carlo on the contract structure (20k paths)")
    vals, draws = monte_carlo()
    q = np.percentile(vals, [5, 10, 25, 50, 75, 90, 95])
    print(f"    p5 ${q[0]:,.0f} p10 ${q[1]:,.0f} p25 ${q[2]:,.0f} MEDIAN ${q[3]:,.0f} p75 ${q[4]:,.0f} p90 ${q[5]:,.0f} p95 ${q[6]:,.0f}")
    print(f"    P(value > price ${S:,.0f}) = {(vals > S).mean():.1%} | price at {(vals < S).mean()*100:.0f}th percentile")
    # variance attribution (rank correlation with value)
    from scipy.stats import spearmanr
    attr = {k: spearmanr(v, vals).correlation for k, v in draws.items()}
    print("    Spearman(input, value):", {k: f"{v:+.2f}" for k, v in attr.items()})

    # -------- chart: EV bridge
    INK, ACC, SHORT = "#182230", "#1B3A6B", "#9E3B32"
    plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.grid": False,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(9, 4.6))
    parts = [("PV Street FY27-28\n(paid in full)", pv_boom2 / 1e9, ACC),
             ("PV contract-floor\nyears FY29-31", (req["pv_paid"] - pv_boom2) / 1e9, ACC),
             ("Residual: post-contract\nperpetuity", req["residual"] / 1e9, SHORT)]
    bottom = 0
    for lbl, v, c in parts:
        ax.bar(lbl, v, bottom=bottom, color=c, alpha=0.85 if c == SHORT else 0.6, width=0.55)
        ax.text(lbl, bottom + v / 2, f"\\${v:,.0f}bn", ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        bottom += v
    ax.bar("Enterprise value\ntoday", EV / 1e9, color=INK, width=0.55, alpha=0.9)
    ax.text("Enterprise value\ntoday", EV / 1e9 / 2, f"\\${EV/1e9:,.0f}bn", ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    ax.set_ylabel("$bn")
    ax.set_title(f"After paying the boom AND the contracts, \\${req['residual']/1e9:,.0f}bn still needs "
                 f"\\${req['nopat_req']/1e9:,.0f}bn/yr forever = {req['gm_req']:.0%} gross margin, permanently",
                 fontsize=10.5, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "contract_bridge.png"); plt.close(fig)

    # -------- chart: value vs mid-cycle GM
    fig, ax = plt.subplots(figsize=(9, 4.2))
    gms = np.linspace(0.20, 0.85, 40)
    ax.plot(gms * 100, [sop(g) for g in gms], color=SHORT, lw=2.2, label="Value/share (15% bit growth)")
    ax.plot(gms * 100, [sop(g, bit_growth=0.25) for g in gms], color=ACC, lw=1.6, ls="--", label="Value/share (25% bit growth)")
    ax.axhline(S, color=INK, ls=":", lw=1.4); ax.text(21, S * 1.03, f"price \\${S:,.0f}", fontsize=9)
    ax.axvspan(25, 40, color="#BBBBBB", alpha=0.35); ax.text(26, ax.get_ylim()[1] * 0.9, "NAND history:\nmid-cycle GM 25-40%", fontsize=8.5)
    ax.set_xlabel("Post-contract (FY32+) gross margin, permanent (%)"); ax.set_ylabel("$/share")
    ax.set_title("Paying consensus FY27-28 and the contract floor in full, the price needs today's margins forever", fontsize=10.5, loc="left")
    ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(OUT / "value_vs_midcycle_gm.png"); plt.close(fig)

    out = dict(asof=ASOF, price=S, ev=EV, mktcap=MKTCAP, shares=SHARES,
               consensus=dict(rev=CONS_REV, eps=CONS_EPS, ni=CONS_NI),
               A_pay2=dict(pv=pv_boom2, residual=resid2, perp_nopat=perp2),
               B_pay5=dict(pv=pv_boom5, residual=resid5, perp_nopat=perp5),
               C_sop_by_gm={f"{g:.2f}": sop(g) for g in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8)},
               C_required=req,
               E_floor=dict(run_rate=floor_run_rate, all_bits=floor_all_bits,
                            vs_fy28_consensus=floor_all_bits / CONS_REV[28] - 1,
                            x_fy2014=dict(pay2=perp2 / SNDK_FY2014_OPINC, pay5=perp5 / SNDK_FY2014_OPINC,
                                          post_contract=req["nopat_req"] / SNDK_FY2014_OPINC)),
               F_12m=dict(scenarios=scen_rows, expected_short_return=ev_ret, reward_risk=up / dn),
               D_mc=dict(p5=q[0], p10=q[1], p25=q[2], median=q[3], p75=q[4], p90=q[5], p95=q[6],
                         p_above=float((vals > S).mean()), attribution=attr))
    (OUT / "contract_dcf.json").write_text(json.dumps(out, indent=2, default=float))
    np.save(OUT / "mc_contract_vals.npy", vals)
    print("\nsaved outputs/contract_dcf.json, contract_bridge.png, value_vs_midcycle_gm.png, mc_contract_vals.npy")
