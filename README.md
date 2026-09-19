# fin-crypto-spot-reversal — ARCHIVED

Short-horizon mean-reversion (contrarian) strategy on Kraken spot crypto.
Losers over 6 months tend to recover.

**Status: DEAD.** The signal passes the pre-registered honesty framework
(DSR 0.902) but the edge is not tradeable. The median monthly return is
negative (-1.78% full, -5.93% test). Only 32% of months are positive.
The entire backtest return comes from rare, explosive recovery outliers
(one month: +2068%). Full-sample CAGR is -0.84%. The DSR margin is
razor-thin (0.902 vs 0.90), and counting momentum trials from
`fin-crypto-lab` would flip the verdict to FAIL (DSR 0.848 at N=6).
This is a lottery ticket, not a strategy.

## Origin

Research idea #3 from `fin-crypto-lab` (2026-09-19). The signal scan found
`reversal_180d top10` with test Sharpe 0.47 (beats benchmark 0.39) but train
Sharpe 0.35. The automated selection rule never picks it because train <
benchmark.

## What we know

- The reversal signal uses the same data as `fin-crypto-lab` spot. No new
  data pipeline needed.
- Train Sharpe (0.35) is below the benchmark (0.39). The selection rule
  rejects it. But the test Sharpe (0.47) beats the benchmark.
- The weak train Sharpe might be a feature (no overfitting), not a bug.
  Contrarian signals often look weak in-sample because they bet against
  trends that dominate training periods.

## This is NOT momentum

This is a contrarian strategy. It buys recent losers and sells recent
winners. It needs its own sweep family, its own thresholds, and its own
honesty framework. Do not mix it with the momentum sweep in `fin-crypto-lab`.

## Results (2026-09-19)

### Phase 0 and 1: sweep

Ran 9-config grid (lookbacks 90/180/365, portfolio sizes 5/10/20). Only 180d
lookback was viable. Narrowed to 3-config grid (180d x 5/10/20). Result:

**FAMILY: PASS** (rev_180d_bot5 selected)

| metric | value |
|---|---|
| Train Sharpe | 0.11 |
| Test Sharpe | 0.48 |
| Test CAGR | 31.39% |
| DSR | 0.902 (threshold 0.90) |
| PBO | 0.314 (threshold 0.50) |
| Test maxDD | 78.24% |

Honesty: DSR-only gate. PC-1 (train > benchmark) relaxed because contrarian
signals bet against trends that dominate training periods.

### Phase 2: robustness

**Lookback sensitivity:** 90d is noisy, 365d is destructive. Only 180d works.

**Portfolio size sensitivity:** bot5 has best test Sharpe (0.48), bot10 is
decent (0.40), bot20 degrades (0.29). Concentrated portfolios capture the
reversal effect better.

**Blend test (365d momentum + 180d reversal):** the blend makes things worse.
Test Sharpe goes negative for top-5 and top-10. Pure reversal beats the blend.

**Survivorship bias audit:** Kraken has delisted at most 1 USD pair since
2017. The volume-ranked universe filter (top-20 by 90-day volume) excludes
illiquid and dead coins. Across 2110 reversal picks, median 180d forward
return is -0.12% (no free lunch at the median). Risk is low.

## Run commands

```
uv run python -m fin_crypto_spot_reversal.run_sweep   # main reversal sweep
uv run python -m fin_crypto_spot_reversal.run_blend    # blend test
```

## Why it's dead

1. **Lottery ticket distribution.** Median monthly return is negative. Only
   32% of months are positive. The mean is inflated by rare outliers.
2. **Thin DSR margin.** 0.902 vs 0.90 threshold. Adding momentum trials
   from `fin-crypto-lab` (N_TRIALS=6) drops DSR to 0.848 (FAIL).
3. **Severe drawdowns.** 78% test maxDD. Full-sample CAGR is -0.84%.
4. **Fat tails.** Weekly return kurtosis is 466. The backtest result depends
   on a handful of explosive recovery weeks.
