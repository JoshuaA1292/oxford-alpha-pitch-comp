"""Reverse-DCF screen: what does the current price force you to believe?

Candidates: SNDK (short case), DGE.L (long case), MU (cross-check).
Run:  analysis/.venv/bin/python analysis/screen_reverse_dcf.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from quant.dcf import (enterprise_value, implied_growth, implied_margin,
                       implied_terminal_nopat)

DATA = Path(__file__).parent / "data"


def load(t):
    d = t.replace(".", "_")
    info = json.loads((DATA / d / "info.json").read_text())
    return d, info


def fx_gbpusd():
    import yfinance as yf
    h = yf.Ticker("GBPUSD=X").history(period="5d")
    return float(h["Close"].iloc[-1])


def capex_history(d):
    try:
        cf = pd.read_csv(DATA / d / "cashflow_annual.csv", index_col=0)
        row = cf.reindex(["Capital Expenditure"]).dropna(how="all")
        return (row / 1e9).round(2)
    except Exception:
        return None


print("=" * 70)
print("REVERSE DCF SCREEN  —  what the price forces you to believe")
print("=" * 70)

# ---------------- SNDK ----------------
d, info = load("SNDK")
shares = info["sharesOutstanding"]
price = info["currentPrice"]
mktcap = price * shares
debt, cash = info["totalDebt"], info["totalCash"]
ev = mktcap + debt - cash
sales0 = info["totalRevenue"]          # FY26 (Jun-26): 20.25bn
print(f"\nSNDK  price ${price:,.0f}  mktcap ${mktcap/1e9:,.1f}bn  EV ${ev/1e9:,.1f}bn")
print(f"      FY26 revenue ${sales0/1e9:.2f}bn, TTM EBITA margin ~{info['operatingMargins']*.999:.0%}")

WACC = 0.11   # rf 4.8% + beta~1.8-2.2 x ERP 4.5% -> 11-13%; use conservative low end
TAX = 0.13    # FY26 effective (NI 11.43 / OpInc 12.47 with other items); favors bulls
INC_F, INC_W = 0.10, 0.05
INFL = 0.02

# Consensus path: FY27 $48.96bn (+142%), FY28 $57.79bn (+18%)
cons = [48.960e9, 57.787e9]

# Exhibit 1: run consensus 2 boom years at CURRENT margins, then solve the
# perpetual NOPAT the residual EV demands.
boom_margin = 0.62  # FY26 EBITDA margin ~62%; EBITA slightly less. Generous.
fcfs = []
prev = sales0
for s in cons:
    ebita = s * boom_margin
    nopat = ebita * (1 - TAX)
    fcf = nopat - (INC_F + INC_W) * (s - prev)
    fcfs.append(fcf)
    prev = s
pv_boom = sum(f / (1 + WACC) ** (t + 1) for t, f in enumerate(fcfs))
nopat_perp = implied_terminal_nopat(ev, fcfs, WACC, INFL)
print(f"\n  [E1] Pay for the boom: PV of consensus FY27-28 FCF at 62% margins = ${pv_boom/1e9:,.1f}bn ({pv_boom/ev:.0%} of EV)")
print(f"       Residual EV ${ (ev-pv_boom)/1e9:,.1f}bn requires PERPETUAL NOPAT of ${nopat_perp/1e9:,.1f}bn/yr from FY29 forever")
print(f"       vs SNDK actual op income:  FY23 -$1.30bn | FY24 -$0.44bn | FY25 +$0.51bn | FY26 +$12.47bn")
print(f"       => market demands {nopat_perp/0.51e9:,.0f}x SNDK's best pre-boom year, forever, AFTER paying for the boom")

# Sensitivity on WACC
for w in (0.10, 0.12, 0.13):
    n = implied_terminal_nopat(ev, fcfs, w, INFL)
    print(f"       WACC {w:.0%}: perpetual NOPAT needed ${n/1e9:,.1f}bn/yr")

# Exhibit 2: implied constant margin if revenue follows consensus then +5%/yr
growth_path = [cons[0] / sales0 - 1, cons[1] / cons[0] - 1] + [0.05] * 8
m_imp = implied_margin(ev, sales0, growth_path, TAX, INC_F, INC_W, WACC, INFL, 10)
print(f"\n  [E2] If revenue = consensus then +5%/yr, price implies a CONSTANT EBITA margin of {m_imp:.1%} for 10 years + terminal")
print(f"       vs own history: FY23 gross margin 7%, FY24 16%, FY25 30%; NAND long-run avg EBITA margin ~10-15%, prior peaks ~25-35%")

# Exhibit 3: margin fade scenarios -> value per share
def value_fade(mid_cycle_margin, fade_years=3, boom_m=0.62):
    margins = list(np.linspace(boom_m, mid_cycle_margin, fade_years + 1))[1:]
    margins += [mid_cycle_margin] * (10 - fade_years)
    g = growth_path
    evv = enterprise_value(sales0, g, margins, TAX, INC_F, INC_W, WACC, INFL, 10)
    return (evv - debt + cash) / shares

print("\n  [E3] Value per share if margins fade over 3yrs from 62% to mid-cycle X, revenue holds at consensus levels +5%:")
for m in (0.35, 0.25, 0.15, 0.10):
    v = value_fade(m)
    print(f"       mid-cycle EBITA {m:.0%}:  ${v:,.0f}/sh   ({v/price-1:+.0%} vs price ${price:,.0f})")

cap = capex_history(d)
if cap is not None:
    print("\n  capex history ($bn):"); print("   " + cap.to_string().replace("\n", "\n   "))

# ---------------- MU cross-check ----------------
d, info = load("MU")
shares, price = info["sharesOutstanding"], info["currentPrice"]
ev_mu = price * shares + info["totalDebt"] - info["totalCash"]
sales_mu = info["totalRevenue"]  # TTM ~90bn
cons_mu = [129.736e9, 241.081e9]
fcfs_mu = []
prev = sales_mu
for s in cons_mu:
    fcf = s * 0.65 * (1 - TAX) - 0.35 * (s - prev)  # 65% EBITA margin, heavy capex 35% of dSales
    fcfs_mu.append(fcf)
    prev = s
n_mu = implied_terminal_nopat(ev_mu, fcfs_mu, WACC, INFL)
print(f"\nMU    EV ${ev_mu/1e9:,.0f}bn | consensus FY27 rev $130bn, FY28 $241bn (!)")
print(f"      After paying for those two years, residual demands perpetual NOPAT ${n_mu/1e9:,.1f}bn/yr")
print(f"      vs MU actual net income: FY23 -$5.8bn | FY24 +$0.8bn | FY25 +$8.5bn")

# ---------------- DGE.L ----------------
d, info = load("DGE.L")
fx = fx_gbpusd()
shares = info["sharesOutstanding"]
price_gbp = info["currentPrice"] / 100.0
mktcap_usd = price_gbp * shares * fx
ev_dge = mktcap_usd + info["totalDebt"] - info["totalCash"]  # debt/cash in USD
sales_dge = info["totalRevenue"]
m_dge = 0.27   # current EBITA margin
TAX_D = 0.24
g_imp = implied_growth(ev_dge, sales_dge, m_dge, TAX_D, 0.30, 0.10, 0.08, INFL, 10)
print(f"\nDGE.L GBPUSD {fx:.3f} | mktcap ${mktcap_usd/1e9:.1f}bn | EV ${ev_dge/1e9:.1f}bn | rev ${sales_dge/1e9:.1f}bn")
print(f"      At 27% margins, WACC 8%: price implies {g_imp:+.1%}/yr sales growth for 10 yrs")
for w, m in [(0.075, 0.27), (0.085, 0.27), (0.08, 0.24), (0.08, 0.30)]:
    g = implied_growth(ev_dge, sales_dge, m, TAX_D, 0.30, 0.10, w, INFL, 10)
    print(f"      WACC {w:.1%}, margin {m:.0%}: implied growth {g:+.1%}")
print(f"      Actual: revenue growth -1.7% y/y; guidance ~flat; sell-side already Buy (target +18%)")
print("\ndone")
