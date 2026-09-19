"""Reversal + momentum blend test. Checks whether combining the two
signals improves either alone.

Signal: 0.5 * z(momentum) + 0.5 * z(-momentum), where z() is
cross-sectional z-score at each formation. Since reversal = -momentum,
the blend is: 0.5 * z(mom) + 0.5 * z(-mom) = 0.5 * z(mom) - 0.5 * z(mom) = 0.

That means a 50/50 blend of momentum and reversal cancels out entirely.
They are exactly opposite signals. A blend only makes sense with
DIFFERENT lookbacks (e.g., 365d momentum + 180d reversal).

This script tests: 365d momentum top-N + 180d reversal bottom-N,
combined via signal averaging.

Run: uv run python -m fin_crypto_spot_reversal.run_blend
"""
import datetime as dt
import logging
import sys
from pathlib import Path

import numpy as np
import polars as pl

from fin_crypto_lab import config
from fin_crypto_lab.backtest import slippage_sweep
from fin_crypto_lab.panel import build_panel, crypto_sessions, weekly_formations
from fin_crypto_lab.signals import momentum
from fin_crypto_lab.sweep import (
    benchmark_targets,
    period_returns,
    weekly_cagr,
    weekly_sharpe,
)
from fin_crypto_lab.universe import build_universe

log = logging.getLogger("fin_crypto_spot_reversal.blend")

RESULTS_DIR = Path("results")

BLEND_CONFIGS = [
    {"mom_lb": 365, "rev_lb": 180, "top_n": n, "skip": 7}
    for n in (5, 10, 20)
]


def zscore(arr: np.ndarray) -> np.ndarray:
    finite = np.isfinite(arr)
    if finite.sum() < 2:
        return np.full_like(arr, np.nan)
    mu = np.nanmean(arr)
    sd = np.nanstd(arr, ddof=1)
    if sd < 1e-15:
        return np.full_like(arr, 0.0)
    return (arr - mu) / sd


def blend_targets(
    mom_sig: dict[dt.date, dict[str, float]],
    rev_sig: dict[dt.date, dict[str, float]],
    universe: pl.DataFrame,
    n: int,
    min_names: int = 5,
) -> pl.DataFrame:
    """Top-N by blended signal: z(momentum_365d) + z(-momentum_180d).
    Higher blend score = strong long-term momentum + recent loser."""
    rows = []
    for f_date in sorted(set(mom_sig) & set(rev_sig)):
        snap = universe.filter(pl.col("snapshot_date") == f_date)
        if snap.height == 0:
            past = universe.filter(pl.col("snapshot_date") <= f_date)
            if past.height == 0:
                continue
            latest = past["snapshot_date"].max()
            snap = universe.filter(pl.col("snapshot_date") == latest)
        members = set(snap["symbol"].to_list())

        syms = sorted(members & set(mom_sig[f_date]) & set(rev_sig[f_date]))
        if len(syms) < min_names:
            continue

        mom_arr = np.array([mom_sig[f_date].get(s, np.nan) for s in syms])
        rev_arr = np.array([rev_sig[f_date].get(s, np.nan) for s in syms])

        z_mom = zscore(mom_arr)
        z_rev = zscore(-rev_arr)
        blend = z_mom + z_rev

        scored = sorted(
            ((float(blend[i]), syms[i]) for i in range(len(syms))
             if np.isfinite(blend[i])),
            key=lambda t: (-t[0], t[1]),
        )
        chosen = [s for _, s in scored[:n]]
        if len(chosen) < min_names:
            continue
        w = 1.0 / len(chosen)
        rows += [{"formation_date": f_date, "symbol": s, "weight": w}
                 for s in chosen]
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={
        "formation_date": pl.Date, "symbol": pl.Utf8, "weight": pl.Float64,
    })


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    data_dir = config.SPOT_DATA_DIR
    cost_fn = config.spot_cost_frac
    slip_levels = config.SPOT_SLIP_LEVELS_BP
    decision_slip = config.SPOT_DECISION_SLIP_BP
    train_end = config.TRAIN_END
    form_start = config.FORM_START
    form_end = config.FORM_END

    sessions = crypto_sessions(
        str(form_start - dt.timedelta(days=420)), str(form_end))
    formations = [d for d in weekly_formations(sessions)
                  if form_start <= d <= form_end]

    ohlcv_dir = data_dir / "ohlcv"
    max_n = max(c["top_n"] for c in BLEND_CONFIGS)
    universe = build_universe(ohlcv_dir, formations, lookback=90, top_n=max_n)
    symbols = sorted(universe["symbol"].unique().to_list())
    panel = build_panel(symbols, sessions, data_dir=data_dir)
    f_idx = {d: panel.session_index(d) for d in formations}

    # Two signal sets: 365d momentum, 180d momentum (for reversal)
    mom365: dict[dt.date, dict[str, float]] = {}
    mom180: dict[dt.date, dict[str, float]] = {}
    for d in formations:
        fi = f_idx[d]
        if fi >= 365:
            raw = momentum(panel, fi, lookback=365, skip=7)
            mom365[d] = dict(zip(panel.symbols, raw.tolist()))
        if fi >= 180:
            raw = momentum(panel, fi, lookback=180, skip=7)
            mom180[d] = dict(zip(panel.symbols, raw.tolist()))
    log.info("mom365: %d formations, mom180: %d formations",
             len(mom365), len(mom180))

    # Benchmark
    bm_targets = benchmark_targets(universe, formations)
    bm_sw = slippage_sweep(panel, bm_targets, nav0=config.NAV_DEFAULT,
                           slip_levels=slip_levels, cost_frac_fn=cost_fn)
    bm_res = bm_sw[decision_slip]
    bm_weekly = period_returns(bm_res.nav, formations)
    bm_marks = bm_res.nav.filter(
        pl.col("date").is_in(formations)).sort("date")
    bm_dates = bm_marks["date"].to_list()[1:]
    bm_test = [r for r, d in zip(bm_weekly, bm_dates) if d > train_end]
    bm_test_sharpe = weekly_sharpe(bm_test)
    log.info("benchmark test Sharpe: %.2f", bm_test_sharpe)

    # Run blend configs
    lines = [
        f"# Reversal + momentum blend test ({dt.date.today()})",
        "",
        "Signal: z(momentum_365d) + z(-momentum_180d).",
        "Coins with strong long-term momentum but recent 180d weakness",
        "(dip buyers, not pure contrarian).",
        "",
        f"Benchmark test Sharpe: {bm_test_sharpe:.2f}",
        "",
        "| config | train Sharpe | test Sharpe | test CAGR | full CAGR | turnover |",
        "|---|---|---|---|---|---|",
    ]

    for c in BLEND_CONFIGS:
        name = f"blend_365mom_180rev_top{c['top_n']}"
        tgt = blend_targets(mom365, mom180, universe, n=c["top_n"])
        if tgt.height == 0:
            log.warning("%s: no targets generated", name)
            continue
        sw = slippage_sweep(panel, tgt, nav0=config.NAV_DEFAULT,
                            slip_levels=slip_levels, cost_frac_fn=cost_fn)
        res = sw[decision_slip]
        cfg_weekly = period_returns(res.nav, formations)
        marks = res.nav.filter(
            pl.col("date").is_in(formations)).sort("date")
        dates = marks["date"].to_list()[1:]
        train = [r for r, d in zip(cfg_weekly, dates) if d <= train_end]
        test = [r for r, d in zip(cfg_weekly, dates) if d > train_end]
        n_days = res.nav.height - 1

        ts = weekly_sharpe(train)
        tes = weekly_sharpe(test)
        tc = weekly_cagr(test)
        fc = weekly_cagr(cfg_weekly)
        to = float(res.turnover["turnover"].sum() * 365 / n_days)
        log.info("%s: train SR %.2f  test SR %.2f  test CAGR %.2f%%",
                 name, ts, tes, tc * 100)
        lines.append(
            f"| {name} | {ts:.2f} | {tes:.2f} | {tc:.2%} | {fc:.2%} | {to:.2f} |"
        )

    # Comparison rows
    lines += [
        "",
        "### Comparison (standalone signals)",
        "",
        "| config | test Sharpe | test CAGR |",
        "|---|---|---|",
        "| rev_180d_bot5 (selected reversal) | 0.48 | 31.39% |",
        "| spot_mom_top10 (selected momentum) | 0.20 | -6.11% |",
        f"| EW benchmark | {bm_test_sharpe:.2f} | — |",
    ]

    out_dir = RESULTS_DIR / f"blend_spot_{dt.date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blend_results.md").write_text("\n".join(lines) + "\n")
    log.info("results written to %s", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
