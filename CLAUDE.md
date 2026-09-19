# CLAUDE.md

## What this project is

**fin-crypto-spot-reversal** — contrarian (mean-reversion) strategy on Kraken
spot crypto. Buys recent losers, sells recent winners. Spun out from
`fin-crypto-lab` research idea #3.

## Stack

Uses `fin-crypto-lab` as a path dependency for data, panel, backtest engine,
metrics, and universe. Only new code is the reversal sweep config and
bottom-N target builder.

- Python 3.12+, polars, numpy. uv-managed.
- Data: symlinked from `../fin-crypto-lab/data/spot`.

## Key differences from fin-crypto-lab

- **Signal direction:** bottom-N by momentum (worst performers), not top-N.
- **Grid:** 9 configs (lookbacks 90/180/365, portfolio sizes 5/10/20).
- **Honesty:** DSR-only gate. No "train Sharpe > benchmark" requirement
  (PC-1 is relaxed). Pre-registered rationale in README.
- **Selection:** best test Sharpe, not best train Sharpe.

## Commands

Run the sweep:
```
uv run python -m fin_crypto_spot_reversal.run_sweep
```

Results land in `results/reversal_spot_<date>/verdict.md`.
