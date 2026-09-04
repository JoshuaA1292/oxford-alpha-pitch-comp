"""Pull fundamental + market data for pitch candidates into analysis/data/.

Run:  analysis/.venv/bin/python analysis/pull_data.py
"""
import json
import sys
import warnings
from pathlib import Path

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

CANDIDATES = ["DGE.L", "SNDK", "MU", "WDC", "HUM", "ELV", "PSN.L", "UNH"]

INFO_KEYS = [
    "longName", "currency", "financialCurrency", "marketCap", "sharesOutstanding",
    "currentPrice", "totalDebt", "totalCash", "beta",
    "trailingPE", "forwardPE", "enterpriseValue", "enterpriseToEbitda",
    "enterpriseToRevenue", "priceToBook", "ebitda", "totalRevenue",
    "revenueGrowth", "operatingMargins", "grossMargins", "profitMargins",
    "sharesShort", "sharesShortPriorMonth", "shortRatio", "shortPercentOfFloat",
    "heldPercentInstitutions", "floatShares", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
    "targetMeanPrice", "targetHighPrice", "targetLowPrice", "numberOfAnalystOpinions",
    "recommendationKey", "dividendYield", "trailingEps", "forwardEps",
]


def safe(fn, label):
    try:
        return fn()
    except Exception as e:
        print(f"    !! {label}: {e}", file=sys.stderr)
        return None


def pull(ticker: str):
    print(f"== {ticker}")
    t = yf.Ticker(ticker)
    out = DATA / ticker.replace(".", "_")
    out.mkdir(exist_ok=True)

    info = safe(lambda: t.info, "info") or {}
    slim = {k: info.get(k) for k in INFO_KEYS}
    (out / "info.json").write_text(json.dumps(slim, indent=2, default=str))

    for name, fn in {
        "income_annual": lambda: t.income_stmt,
        "income_quarterly": lambda: t.quarterly_income_stmt,
        "balance_annual": lambda: t.balance_sheet,
        "cashflow_annual": lambda: t.cashflow,
        "cashflow_quarterly": lambda: t.quarterly_cashflow,
    }.items():
        df = safe(fn, name)
        if df is not None and not df.empty:
            df.to_csv(out / f"{name}.csv")

    px = safe(lambda: t.history(period="3y", auto_adjust=True), "prices")
    if px is not None and not px.empty:
        px.to_csv(out / "prices.csv")

    for name, fn in {
        "eps_trend": lambda: t.eps_trend,
        "eps_revisions": lambda: t.eps_revisions,
        "earnings_estimate": lambda: t.earnings_estimate,
        "revenue_estimate": lambda: t.revenue_estimate,
        "growth_estimates": lambda: t.growth_estimates,
        "analyst_price_targets": lambda: pd.DataFrame([t.analyst_price_targets]),
        "recommendations": lambda: t.recommendations_summary,
    }.items():
        df = safe(fn, name)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            df.to_csv(out / f"{name}.csv")

    exps = safe(lambda: t.options, "options") or []
    (out / "option_expiries.json").write_text(json.dumps(list(exps)))
    print(f"   mktcap={slim.get('marketCap')}, opts={len(exps)} expiries")


if __name__ == "__main__":
    for tk in CANDIDATES:
        pull(tk)
    # risk-free: US 10y and 13w from Yahoo indices
    for rf in ["^TNX", "^IRX"]:
        h = yf.Ticker(rf).history(period="1mo")
        if not h.empty:
            h.to_csv(DATA / f"{rf.strip('^')}.csv")
            print(f"{rf} latest: {h['Close'].iloc[-1]:.2f}")
    print("done")
