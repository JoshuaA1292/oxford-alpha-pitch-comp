"""Breeden-Litzenberger risk-neutral density from an option chain.

f(K) = e^{rT} * d2C/dK2.  Pipeline (per the plan, with the Q&A traps handled):
  1. filter quotes: bid > 0, open interest >= min_oi, use mid prices
  2. compute our own implied vols from mids (Black-Scholes, brentq) - never
     trust vendor IV columns
  3. fit a smoothing spline to IV vs log-moneyness (smooth in vol space)
  4. reprice calls on a dense strike grid, second-difference for the density
  5. validate: density >= 0, integrates to ~1, mean ~ forward
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import brentq
from scipy.stats import norm


def bs_call(S, K, T, r, sigma, q=0.0):
    if sigma <= 0 or T <= 0:
        return max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def bs_put(S, K, T, r, sigma, q=0.0):
    return bs_call(S, K, T, r, sigma, q) - S * np.exp(-q * T) + K * np.exp(-r * T)


def implied_vol(price, S, K, T, r, q=0.0, kind="call"):
    fn = bs_call if kind == "call" else bs_put
    intrinsic = fn(S, K, T, r, 1e-9, q)
    if price <= intrinsic + 1e-12:
        return np.nan
    try:
        return brentq(lambda s: fn(S, K, T, r, s, q) - price, 1e-4, 8.0, xtol=1e-8)
    except ValueError:
        return np.nan


def fit_smile(strikes, ivs, S, smooth_factor=None):
    """Smoothing spline of IV vs log-moneyness; returns callable sigma(K)."""
    x = np.log(np.asarray(strikes, float) / S)
    y = np.asarray(ivs, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    order = np.argsort(x)
    x, y = x[order], y[order]
    if smooth_factor is None:
        smooth_factor = len(x) * (0.02 ** 2)  # ~2 vol pts tolerance
    spl = UnivariateSpline(x, y, s=smooth_factor, k=3)
    lo, hi = x.min(), x.max()

    def sigma(K):
        xx = np.clip(np.log(np.asarray(K, float) / S), lo, hi)  # flat extrapolation
        return np.maximum(spl(xx), 1e-3)

    return sigma, (S * np.exp(lo), S * np.exp(hi))


def rn_density(S, T, r, sigma_fn, k_lo, k_hi, n=2001, q=0.0):
    """Risk-neutral pdf on [k_lo, k_hi] via second difference of repriced calls."""
    K = np.linspace(k_lo, k_hi, n)
    C = np.array([bs_call(S, k, T, r, float(sigma_fn(k)), q) for k in K])
    h = K[1] - K[0]
    f = np.exp(r * T) * (C[2:] - 2 * C[1:-1] + C[:-2]) / h ** 2
    return K[1:-1], np.maximum(f, 0.0)


def density_stats(K, f, thresholds=()):
    """Integral, mean, and P(S_T > x) for each x in thresholds."""
    total = np.trapezoid(f, K)
    mean = np.trapezoid(K * f, K) / total if total > 0 else np.nan
    probs = {}
    for x in thresholds:
        mask = K >= x
        probs[x] = (np.trapezoid(f[mask], K[mask]) / total) if mask.any() else 0.0
    return {"integral": total, "mean": mean, "probs": probs}
