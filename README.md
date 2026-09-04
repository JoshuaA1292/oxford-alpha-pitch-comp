# Oxford Alpha Pitch Comp 2026 — Short SanDisk (SNDK)

Team repo for the Oxford Alpha Fund **Varsity Pitch Competition 2026** (finals 15 Oct 2026, London — judges from Point72, Fidelity, and Citadel).

**The pitch: SHORT SanDisk (NASDAQ: SNDK).** Even paying the Street's own FY27–28 boom estimates in full, the residual enterprise value demands $17.4bn of NOPAT per year in perpetuity — 34× the best year this business has ever had. Base target $960 (−37%), probability-weighted expected short return +23%, R/R ≈ 3.5:1.

## Documents

| Doc | What it is |
|---|---|
| [docs/CASE_SANDISK_SHORT.md](docs/CASE_SANDISK_SHORT.md) | **The full case + 10-slide deck plan** — thesis pillars, model results, scenarios, event path, Q&A prep |
| [docs/PLAYBOOK.md](docs/PLAYBOOK.md) | The strategy playbook — competition intel, analytics stack, selection funnel, workplan |

## Analysis engine

Everything quantitative is reproducible from [`analysis/`](analysis/):

```
analysis/
├── quant/
│   ├── dcf.py            # 7-driver Rappaport/Mauboussin FCFF engine + reverse solvers
│   ├── montecarlo.py     # correlated Monte Carlo over the DCF (Cholesky, rejection rules)
│   └── bl_density.py     # Breeden–Litzenberger option-implied density (own IVs, vol-space spline)
├── tests/test_engine.py  # 13 verification tests (closed-form checks) — all passing
├── pull_data.py          # fundamentals / estimates / prices / short interest for all candidates
├── pull_options.py       # SNDK option chains (Dec-26, Jan-27, Mar-27)
├── screen_reverse_dcf.py # the screen that picked SNDK and killed DGE.L / HUM
├── sndk_exhibits.py      # B-L density, Monte Carlo, margins, beta — full run with printouts
├── make_charts.py        # deck-grade charts
├── data/                 # pulled snapshots (as of 2 Sep 2026)
└── outputs/              # charts + sndk_report.json
```

### Reproduce

```bash
python3 -m venv analysis/.venv
analysis/.venv/bin/pip install yfinance numpy pandas scipy matplotlib pytest statsmodels
analysis/.venv/bin/python -m pytest analysis/tests -q     # 13 passed
analysis/.venv/bin/python analysis/pull_data.py           # refresh data snapshots
analysis/.venv/bin/python analysis/pull_options.py
analysis/.venv/bin/python analysis/screen_reverse_dcf.py  # the candidate screen
analysis/.venv/bin/python analysis/sndk_exhibits.py       # all SNDK model runs
analysis/.venv/bin/python analysis/make_charts.py         # regenerate charts
```

Data sources: company filings via Yahoo Finance, CBOE option quotes, FINRA short interest, ^IRX/^TNX risk-free. **Prices move — refresh every exhibit the week of submission and again before finals.**

## Key exhibits

![Centerpiece](analysis/outputs/centerpiece_mc_vs_market.png)

![What's priced in](analysis/outputs/priced_in_waterfall.png)

![Margin cycle](analysis/outputs/margin_cycle.png)
