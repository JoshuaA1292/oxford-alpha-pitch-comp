"""Monte Carlo over the 7-driver DCF with correlated inputs (Damodaran,
'Probabilistic Approaches'). Growth and margin drawn jointly via Cholesky;
paths with terminal constraint violations are rejected and counted."""
from __future__ import annotations

import numpy as np

from .dcf import enterprise_value, equity_per_share


def run_mc(sales0, nonop_assets, debt, shares, wacc_dist, growth_dist,
           margin_dist, tax, inc_fixed, inc_wc, rho_gm=0.5, inflation=0.02,
           years=10, n=20000, seed=7, margin_path_fn=None):
    """Each *_dist is (mean, sd) for normal draws (growth, margin) or
    (low, mode, high) triangular for wacc. margin_path_fn optionally maps a
    drawn terminal margin to a per-year path (e.g. fade from current levels).
    Returns array of per-share values and diagnostics."""
    rng = np.random.default_rng(seed)
    g_mu, g_sd = growth_dist
    m_mu, m_sd = margin_dist
    cov = np.array([[g_sd ** 2, rho_gm * g_sd * m_sd],
                    [rho_gm * g_sd * m_sd, m_sd ** 2]])
    L = np.linalg.cholesky(cov)

    vals, rejected = [], 0
    while len(vals) < n:
        z = rng.standard_normal(2)
        g, m = np.array([g_mu, m_mu]) + L @ z
        w = rng.triangular(*wacc_dist)
        if w <= inflation + 0.005 or m <= 0.0:
            rejected += 1
            continue
        margin = margin_path_fn(m) if margin_path_fn else m
        ev = enterprise_value(sales0, g, margin, tax, inc_fixed, inc_wc, w,
                              inflation, years)
        vals.append(equity_per_share(ev, nonop_assets, debt, shares))
    vals = np.array(vals)
    return vals, {"rejected": rejected, "n": n}


def summarize(vals, price):
    q = np.percentile(vals, [5, 25, 50, 75, 95])
    return {
        "p5": q[0], "p25": q[1], "median": q[2], "p75": q[3], "p95": q[4],
        "mean": vals.mean(),
        "prob_above_price": float((vals > price).mean()),
        "price_percentile": float((vals < price).mean() * 100),
    }
