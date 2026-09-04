"""Rappaport/Mauboussin 7-driver FCFF valuation engine + reverse solvers.

Value drivers (Expectations Investing, rev. 2021):
    sales growth g_t, EBITA margin m_t, cash tax rate tau,
    incremental fixed-capital rate f, incremental working-capital rate w,
    WACC, terminal inflation i (perpetuity-with-inflation continuing value).

FCF_t   = NOPAT_t - (f + w) * dSales_t
CV_T    = NOPAT_T * (1 + i) / (WACC - i)      [value-neutral reinvestment after T]
EV      = sum PV(FCF_t) + PV(CV_T)
Equity  = EV + nonoperating assets - debt
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq


def enterprise_value(sales0, growth, margin, tax, inc_fixed, inc_wc, wacc,
                     inflation=0.02, years=None):
    """PV of FCFF + continuing value. `growth`/`margin` may be scalars or
    per-year arrays (margin array => margin path). Returns EV."""
    growth = np.atleast_1d(np.asarray(growth, dtype=float))
    if years is None:
        years = len(growth)
    if len(growth) == 1:
        growth = np.full(years, growth[0])
    assert len(growth) == years, "growth path length must equal years"
    margin = np.atleast_1d(np.asarray(margin, dtype=float))
    if len(margin) == 1:
        margin = np.full(years, margin[0])
    assert len(margin) == years

    sales_prev = sales0
    ev = 0.0
    nopat = 0.0
    for t in range(1, years + 1):
        sales = sales_prev * (1 + growth[t - 1])
        d_sales = sales - sales_prev
        ebita = sales * margin[t - 1]
        nopat = ebita * (1 - tax)
        fcf = nopat - (inc_fixed + inc_wc) * d_sales
        ev += fcf / (1 + wacc) ** t
        sales_prev = sales
    if wacc <= inflation:
        raise ValueError("WACC must exceed terminal inflation")
    cv = nopat * (1 + inflation) / (wacc - inflation)
    ev += cv / (1 + wacc) ** years
    return ev


def equity_per_share(ev, nonop_assets, debt, shares):
    return (ev + nonop_assets - debt) / shares


def implied_growth(target_ev, sales0, margin, tax, inc_fixed, inc_wc, wacc,
                   inflation=0.02, years=10, lo=-0.5, hi=3.0):
    """Constant annual sales growth over `years` that makes EV = target_ev."""
    f = lambda g: enterprise_value(sales0, g, margin, tax, inc_fixed, inc_wc,
                                   wacc, inflation, years) - target_ev
    return brentq(f, lo, hi, xtol=1e-8)


def implied_margin(target_ev, sales0, growth, tax, inc_fixed, inc_wc, wacc,
                   inflation=0.02, years=10, lo=1e-4, hi=0.98):
    """Constant EBITA margin that makes EV = target_ev, given a growth path."""
    f = lambda m: enterprise_value(sales0, growth, m, tax, inc_fixed, inc_wc,
                                   wacc, inflation, years) - target_ev
    return brentq(f, lo, hi, xtol=1e-10)


def implied_terminal_nopat(target_ev, fcf_path, wacc, inflation=0.02):
    """Given explicit near-year FCFs, the perpetual NOPAT (from year len+1 on)
    required to make EV = target_ev. Answers: 'after the boom years the market
    pays for, what must this business earn forever?'"""
    T = len(fcf_path)
    pv_explicit = sum(f / (1 + wacc) ** (t + 1) for t, f in enumerate(fcf_path))
    residual = target_ev - pv_explicit
    # residual = NOPAT*(1+i)/(wacc-i) / (1+wacc)^T
    return residual * (1 + wacc) ** T * (wacc - inflation) / (1 + inflation)


def market_implied_forecast_period(price_per_share, sales0, growth, margin, tax,
                                   inc_fixed, inc_wc, wacc, nonop_assets, debt,
                                   shares, inflation=0.02, max_years=40):
    """Smallest forecast horizon T at which per-share value >= price
    (Mauboussin's MIFP), holding consensus drivers fixed. None if never."""
    for T in range(1, max_years + 1):
        g = np.full(T, growth) if np.isscalar(growth) else np.asarray(growth[:T])
        ev = enterprise_value(sales0, g, margin, tax, inc_fixed, inc_wc,
                              wacc, inflation, T)
        if equity_per_share(ev, nonop_assets, debt, shares) >= price_per_share:
            return T
    return None
