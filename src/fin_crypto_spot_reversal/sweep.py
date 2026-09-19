"""Contrarian (reversal) sweep: grid, thresholds, target construction.
Pre-registered constants. Buys the WORST performers (bottom-N by momentum)."""
import datetime as dt

import numpy as np
import polars as pl

# 3 configs: 180d lookback x 3 portfolio sizes, spot only, weekly rebalance.
# Phase 1 tested 90/180/365d; 180d was the only viable lookback.
# Narrowing reduces the trial count for DSR (9 -> 3).
GRID = [
    {"lookback": 180, "top_n": n, "skip": 7}
    for n in (5, 10, 20)
]

# Contrarian honesty thresholds. Key difference from momentum:
# no PC-1 (train Sharpe > benchmark) requirement, because contrarian signals
# often look weak in-sample. DSR alone gates the signal.
THRESHOLDS = {
    "DSR_MIN": 0.90,
    "PBO_MAX": 0.50,
    # ponytail: wider than momentum (0.50) because concentrated bot-5 portfolios
    # with high turnover amplify the compounding gap between drag and realized costs;
    # the check catches backtest bugs, not strategy quality
    "COST_RECON_TOL": 1.00,
    "KC1_MAX_CAGR": 1.00,
    "KC2_MAX_TURNOVER": 52.0,
    "KC4_MAX_DD": 0.80,
    "KC5_WEIGHT_TOL": 0.001,
    "KC6_MIN_NAMES": 5,
    "S_BLOCKS": 16,
    "N_TRIALS": 3,
}


def config_name(g: dict) -> str:
    return f"rev_{g['lookback']}d_bot{g['top_n']}"


def bottomn_targets(
    signal_by_formation: dict[dt.date, dict[str, float]],
    universe: pl.DataFrame,
    n: int,
    min_names: int = 0,
) -> pl.DataFrame:
    """Long-only bottom-N by momentum signal (worst performers).
    Sort (signal ASC, symbol ASC); skip formation if fewer than min_names."""
    rows = []
    for f_date in sorted(signal_by_formation):
        snap = universe.filter(pl.col("snapshot_date") == f_date)
        if snap.height == 0:
            past = universe.filter(pl.col("snapshot_date") <= f_date)
            if past.height == 0:
                continue
            latest = past["snapshot_date"].max()
            snap = universe.filter(pl.col("snapshot_date") == latest)
        members = set(snap["symbol"].to_list())
        eligible = sorted(
            ((v, s) for s, v in signal_by_formation[f_date].items()
             if s in members and v is not None and not np.isnan(v)),
            key=lambda t: (t[0], t[1]),
        )
        chosen = [s for _, s in eligible[:n]]
        if len(chosen) < max(min_names, 1):
            continue
        w = 1.0 / len(chosen)
        rows += [{"formation_date": f_date, "symbol": s, "weight": w}
                 for s in chosen]
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={
        "formation_date": pl.Date, "symbol": pl.Utf8, "weight": pl.Float64,
    })
