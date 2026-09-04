"""Verification suite: every model is checked against a closed-form case
before any pitch conclusion rests on it."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from quant.dcf import (enterprise_value, equity_per_share, implied_growth,
                       implied_margin, implied_terminal_nopat,
                       market_implied_forecast_period)
from quant.bl_density import (bs_call, bs_put, implied_vol, fit_smile,
                              rn_density, density_stats)
from quant.montecarlo import run_mc, summarize


# ---------- DCF engine ----------

def test_zero_growth_matches_perpetuity():
    """g=0, i=0: FCF = NOPAT every year; EV must equal NOPAT/WACC exactly."""
    sales0, m, tax, wacc = 100.0, 0.20, 0.25, 0.10
    nopat = sales0 * m * (1 - tax)
    ev = enterprise_value(sales0, 0.0, m, tax, 0.1, 0.05, wacc,
                          inflation=0.0, years=10)
    assert ev == pytest.approx(nopat / wacc, rel=1e-9)


def test_growth_with_zero_reinvestment_gt_perpetuity():
    ev_g = enterprise_value(100, 0.05, 0.2, 0.25, 0.0, 0.0, 0.10, 0.0, 10)
    ev_0 = enterprise_value(100, 0.00, 0.2, 0.25, 0.0, 0.0, 0.10, 0.0, 10)
    assert ev_g > ev_0


def test_reverse_solvers_round_trip():
    """implied_growth/implied_margin must recover the growth/margin that
    generated a given EV."""
    args = dict(sales0=500.0, tax=0.22, inc_fixed=0.12, inc_wc=0.04,
                wacc=0.095, inflation=0.02, years=10)
    ev = enterprise_value(growth=0.07, margin=0.18, **args)
    g = implied_growth(ev, args["sales0"], 0.18, args["tax"], args["inc_fixed"],
                       args["inc_wc"], args["wacc"], args["inflation"], 10)
    assert g == pytest.approx(0.07, abs=1e-6)
    m = implied_margin(ev, args["sales0"], 0.07, args["tax"], args["inc_fixed"],
                       args["inc_wc"], args["wacc"], args["inflation"], 10)
    assert m == pytest.approx(0.18, abs=1e-8)


def test_implied_terminal_nopat_round_trip():
    """Constructed EV = PV(explicit FCFs) + PV(perpetuity) must return the
    perpetual NOPAT used to construct it."""
    wacc, infl = 0.10, 0.02
    fcfs = [50.0, 60.0, 40.0]
    nopat_term = 30.0
    ev = sum(f / (1 + wacc) ** (t + 1) for t, f in enumerate(fcfs))
    ev += (nopat_term * (1 + infl) / (wacc - infl)) / (1 + wacc) ** 3
    got = implied_terminal_nopat(ev, fcfs, wacc, infl)
    assert got == pytest.approx(nopat_term, rel=1e-9)


def test_mifp_monotone():
    """A higher price must never imply a shorter market-implied forecast
    period."""
    common = dict(sales0=100, growth=0.06, margin=0.2, tax=0.25,
                  inc_fixed=0.1, inc_wc=0.05, wacc=0.09, nonop_assets=5,
                  debt=20, shares=10)
    t_low = market_implied_forecast_period(price_per_share=15, **common)
    t_high = market_implied_forecast_period(price_per_share=25, **common)
    assert t_low is not None and t_high is not None and t_high >= t_low


# ---------- Black-Scholes / implied vol ----------

def test_put_call_parity():
    S, K, T, r, sig = 100, 95, 0.5, 0.04, 0.35
    c, p = bs_call(S, K, T, r, sig), bs_put(S, K, T, r, sig)
    assert c - p == pytest.approx(S - K * np.exp(-r * T), abs=1e-10)


def test_implied_vol_round_trip():
    S, K, T, r = 100, 120, 0.4, 0.045
    price = bs_call(S, K, T, r, 0.55)
    assert implied_vol(price, S, K, T, r) == pytest.approx(0.55, abs=1e-6)


def test_iv_below_intrinsic_is_nan():
    assert np.isnan(implied_vol(0.5, 100, 90, 0.5, 0.04))  # < intrinsic ~10


# ---------- Breeden-Litzenberger ----------

def test_bl_recovers_lognormal():
    """Flat smile => density must be the Black-Scholes lognormal: integral ~1,
    mean ~ forward, and P(S_T > K) ~ N(d2)."""
    S, T, r, sig = 100.0, 0.5, 0.04, 0.40
    sigma_fn = lambda K: sig
    K, f = rn_density(S, T, r, sigma_fn, 20, 400, n=8001)
    st = density_stats(K, f, thresholds=(120.0,))
    fwd = S * np.exp(r * T)
    assert st["integral"] == pytest.approx(1.0, abs=0.01)
    assert st["mean"] == pytest.approx(fwd, rel=0.005)
    d2 = (np.log(S / 120) + (r - 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    from scipy.stats import norm
    assert st["probs"][120.0] == pytest.approx(norm.cdf(d2), abs=0.01)


def test_smile_fit_recovers_flat_vol_from_noisy_quotes():
    rng = np.random.default_rng(0)
    S = 100.0
    strikes = np.linspace(60, 160, 25)
    ivs = 0.5 + rng.normal(0, 0.01, len(strikes))
    sigma_fn, (klo, khi) = fit_smile(strikes, ivs, S)
    grid = np.linspace(70, 150, 50)
    assert np.abs(sigma_fn(grid) - 0.5).max() < 0.03


# ---------- Monte Carlo ----------

def test_mc_degenerate_matches_deterministic():
    """Zero-variance draws must reproduce the deterministic DCF value."""
    det_ev = enterprise_value(100, 0.05, 0.2, 0.25, 0.1, 0.05, 0.09, 0.02, 10)
    det_ps = equity_per_share(det_ev, 5, 20, 10)
    vals, _ = run_mc(100, 5, 20, 10, wacc_dist=(0.09, 0.09, 0.09000001),
                     growth_dist=(0.05, 1e-12), margin_dist=(0.2, 1e-12),
                     tax=0.25, inc_fixed=0.1, inc_wc=0.05, n=200)
    assert vals.mean() == pytest.approx(det_ps, rel=1e-4)


def test_mc_correlation_sign():
    """With rho>0, high-growth draws pair with high margins => wider value
    spread than rho<0."""
    kw = dict(sales0=100, nonop_assets=5, debt=20, shares=10,
              wacc_dist=(0.08, 0.09, 0.10), growth_dist=(0.05, 0.03),
              margin_dist=(0.2, 0.05), tax=0.25, inc_fixed=0.1, inc_wc=0.05,
              n=4000, seed=11)
    v_pos, _ = run_mc(rho_gm=0.8, **kw)
    v_neg, _ = run_mc(rho_gm=-0.8, **kw)
    assert v_pos.std() > v_neg.std()


def test_summarize_percentile():
    vals = np.linspace(1, 100, 1000)
    s = summarize(vals, price=50.0)
    assert s["prob_above_price"] == pytest.approx(0.5, abs=0.01)
    assert s["p5"] < s["median"] < s["p95"]
