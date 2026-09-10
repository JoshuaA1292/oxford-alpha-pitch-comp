# Oxford Alpha Pitch Comp 2026 — Short SanDisk (SNDK)

Team repo for the Oxford Alpha Fund **Varsity Pitch Competition 2026** (finals 15 Oct 2026, London — judges from Point72, Fidelity, and Citadel).

**The pitch: SHORT SanDisk (NASDAQ: SNDK) at $1,764 (9 Sep 2026).** Pay the Street's FY27–28 in full, pay the $93.9bn contract floor in full through FY31, and the residual $176bn of enterprise value still requires an 84% gross margin in perpetuity after the contracts expire. NAND's best three-year run in 30 documented company-years is a 24% operating margin. Base target $900 (−49%), probability-weighted expected short return +28%, R/R ≈ 3.3:1. Cycle-agnostic cross-check: parity with Kioxia (same fabs) implies $940–1,080.

## Documents
| Doc | What it is |
|---|---|
| [docs/CASE_SANDISK_SHORT.md](docs/CASE_SANDISK_SHORT.md) | **The full case + 10-slide deck plan** (rebuilt 9 Sep) — variant perception, pillars, model results, scenarios, event path, trade construction, Q&A prep |
| [docs/REDTEAM_2026-09-09.md](docs/REDTEAM_2026-09-09.md) | The red-team review — verdict, what broke in the 2 Sep case, what was rebuilt, open items |
| [docs/PLAYBOOK.md](docs/PLAYBOOK.md) | The strategy playbook — competition intel, analytics stack, selection funnel, workplan |
| [docs/REDTEAM_2026-09-09.md](docs/REDTEAM_2026-09-09.md) | **Red-team verdict** — what broke in the 2 Sep case, what was rebuilt, the twelve hardest questions |

## The deck (built 9 Sep 2026)

**[`deck/SNDK_short_deck.pdf`](deck/SNDK_short_deck.pdf)** — title page + 9 content slides (10 main, per the rules) + 5 appendix, 16:9, every number injected from the engine.

```
deck/
├── build_deck.py          # HTML template (numbers injected from figures/numbers.json) -> PDF via headless Chrome
├── figures/               # 26 themed charts + numbers.json, all produced by analysis/deck_figures.py
├── SNDK_short_deck.html   # the rendered slides (open in a browser to inspect)
└── SNDK_short_deck.pdf    # the deliverable
```

Rebuild after refreshing data (order matters):

```
analysis/.venv/bin/python analysis/sndk_contract_dcf.py   # engine -> outputs/contract_dcf.json, mc_contract_vals.npy
analysis/.venv/bin/python analysis/sndk_exhibits.py       # options density, beta -> outputs/sndk_report.json
analysis/.venv/bin/python analysis/deck_figures.py        # charts + numbers.json  (also re-checks the MC re-centred at 60% GM)
analysis/.venv/bin/python deck/build_deck.py              # HTML -> PDF -> deck/preview/*.png
```

Theme: navy ink, oxblood for our view / the short, blue for the market / consensus, gold for dated catalysts, grey for history. Palette validated for colour-vision safety. The title page carries the SanDisk logo (`deck/assets/sandisk_logo.svg`) and no team line.

## Analysis engine

Everything quantitative is reproducible from [`analysis/`](analysis/):

```
analysis/
├── quant/
│   ├── dcf.py            # 7-driver Rappaport/Mauboussin FCFF engine + reverse solvers
│   ├── montecarlo.py     # correlated Monte Carlo over the DCF (Cholesky, rejection rules)
│   └── bl_density.py     # Breeden–Litzenberger option-implied density (own IVs, vol-space spline)
├── tests/test_engine.py  # 17 verification tests (closed-form + residual-algebra checks) — all passing
├── pull_data.py          # fundamentals / estimates / prices / short interest for all candidates
├── pull_options.py       # SNDK option chains (Dec-26, Jan-27, Mar-27)
├── screen_reverse_dcf.py # the week-1 screen that picked SNDK and killed DGE.L / HUM (legacy framing)
├── sndk_contract_dcf.py  # THE valuation engine: consensus FY27-28 + contract floor FY29-31 + post-contract residual; MC; floor arithmetic
├── sndk_exhibits.py      # B-L density, margins, beta (+ legacy margin-fade MC as a robustness check)
├── make_charts.py        # deck-grade charts (reads contract_dcf.json + mc_contract_vals.npy)
├── data/                 # pulled snapshots (as of 9 Sep 2026)
└── outputs/              # charts, contract_dcf.json, sndk_report.json
```

### Reproduce

```bash
python3 -m venv analysis/.venv
analysis/.venv/bin/pip install yfinance numpy pandas scipy matplotlib pytest statsmodels
analysis/.venv/bin/python -m pytest analysis/tests -q     # 17 passed
analysis/.venv/bin/python analysis/pull_data.py           # refresh data snapshots
analysis/.venv/bin/python analysis/pull_options.py
analysis/.venv/bin/python analysis/sndk_contract_dcf.py   # valuation engine + Monte Carlo (update ASOF first)
analysis/.venv/bin/python analysis/sndk_exhibits.py       # B-L density, margins, beta (update ASOF first)
analysis/.venv/bin/python analysis/make_charts.py         # regenerate charts (update ASOF first)
```

Data sources: company filings via Yahoo Finance and EDGAR, CBOE option quotes, FINRA short interest, IBKR borrow, ^IRX/^TNX risk-free. Company disclosures (NBM floor, coverage, guarantees, guidance) are hard-coded in `sndk_contract_dcf.py` with their source. **Prices move — refresh every exhibit the week of submission and again before finals.**

## Key exhibits

![Centerpiece](analysis/outputs/centerpiece_mc_vs_market.png)

![What's priced in — after paying the Street and the contracts](analysis/outputs/priced_in_waterfall.png)

![Value vs post-contract margin](analysis/outputs/value_vs_midcycle_gm.png)

![Value vs post-contract margin](analysis/outputs/value_vs_midcycle_gm.png)

![Margin cycle](analysis/outputs/margin_cycle.png)
