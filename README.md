# fin-crypto-spot-reversal (archived)

A contrarian (mean-reversion) strategy on Kraken spot crypto. It buys recent losers and sells recent winners.

**Status: dead.** The signal passes the pre-registered honesty framework (DSR 0.902), but the edge is not tradeable. The median monthly return is negative (-1.78% full, -5.93% test). Only 32% of months are positive. The entire backtest return comes from rare recovery outliers (one month: +2068%). The full-sample CAGR is -0.84%. If you count the momentum trials from `fin-crypto-lab` (N_TRIALS=6), the DSR drops to 0.848, which is a FAIL.

## Origin

Research idea #3 from `fin-crypto-lab` (2026-09-19). The signal scan found `reversal_180d top10` with a test Sharpe of 0.47 (above the benchmark of 0.39), but a train Sharpe of only 0.35. The automated selection rule rejected it because the train Sharpe was below the benchmark.

## Signal properties

- The reversal signal uses the same data as `fin-crypto-lab` spot. No new data pipeline is necessary.
- The train Sharpe (0.35) is below the benchmark (0.39). The test Sharpe (0.47) is above it.
- Contrarian signals often look weak in-sample because they bet against trends that dominate training periods. The weak train Sharpe does not show that the model is overfit.

## This is not momentum

This strategy buys recent losers. It is not a momentum strategy. Do not mix it with the momentum sweep in `fin-crypto-lab`. It must have a separate sweep, separate thresholds, and a separate honesty framework.

## Results (2026-09-19)

### Phase 1: sweep

The sweep ran a 9-config grid (lookbacks 90/180/365 days, portfolio sizes 5/10/20). Only the 180-day lookback worked. The grid narrowed to 3 configs (180d x 5/10/20). Result: **FAMILY: PASS** (rev_180d_bot5 selected).

| Metric | Value |
|---|---|
| Train Sharpe | 0.11 |
| Test Sharpe | 0.48 |
| Test CAGR | 31.39% |
| DSR | 0.902 (threshold 0.90) |
| PBO | 0.314 (threshold 0.50) |
| Test maxDD | 78.24% |

The honesty framework uses a DSR-only gate. For contrarian signals, the framework does not apply the PC-1 rule (train Sharpe must exceed the benchmark).

### Phase 2: robustness

Lookback sensitivity: the 90-day lookback is noisy, and the 365-day lookback is destructive. Only the 180-day lookback works.

Portfolio size sensitivity: bot5 has the best test Sharpe (0.48). bot10 gives a test Sharpe of 0.40. bot20 gives a test Sharpe of 0.29. Smaller portfolios capture the reversal effect better.

Blend test (365-day momentum + 180-day reversal): the blend is worse than pure reversal. Test Sharpe goes negative for top-5 and top-10.

Survivorship bias audit: Kraken has delisted at most one USD pair since 2017. The universe filter (top 20 pairs by 90-day volume) excludes illiquid and dead coins. Across 2110 reversal picks, the median 180-day forward return is -0.12%. Survivorship bias risk is low.

## Run commands

```
uv run python -m fin_crypto_spot_reversal.run_sweep   # main reversal sweep
uv run python -m fin_crypto_spot_reversal.run_blend    # blend test
```

## Why the strategy is dead

1. Lottery ticket distribution: the median monthly return is negative. Only 32% of months are positive. The mean is inflated by rare outliers.
2. Thin DSR margin: 0.902 vs. the 0.90 threshold. Adding momentum trials from `fin-crypto-lab` (N_TRIALS=6) drops DSR to 0.848, which is a FAIL.
3. Severe drawdowns: 78% test maxDD. Full-sample CAGR is -0.84%.
4. Fat tails: weekly return kurtosis is 466. The backtest result depends on a small number of explosive recovery weeks.
