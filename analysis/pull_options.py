"""Pull SNDK option chains for B-L density + skew analysis."""
import json
from pathlib import Path

import pandas as pd
import yfinance as yf

DATA = Path(__file__).parent / "data" / "SNDK"
t = yf.Ticker("SNDK")
exps = t.options
print("expiries:", exps)

# want ~4-7 months out: Jan/Mar 2027 monthlies
targets = [e for e in exps if e[:7] in ("2027-01", "2027-03", "2026-12")]
for e in targets:
    ch = t.option_chain(e)
    ch.calls.to_csv(DATA / f"calls_{e}.csv", index=False)
    ch.puts.to_csv(DATA / f"puts_{e}.csv", index=False)
    print(e, "calls", len(ch.calls), "puts", len(ch.puts),
          "| call OI", int(ch.calls.openInterest.fillna(0).sum()),
          "| put OI", int(ch.puts.openInterest.fillna(0).sum()))
