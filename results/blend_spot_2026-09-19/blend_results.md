# Reversal + momentum blend test (2026-09-19)

Signal: z(momentum_365d) + z(-momentum_180d).
Coins with strong long-term momentum but recent 180d weakness
(dip buyers, not pure contrarian).

Benchmark test Sharpe: 0.23

| config | train Sharpe | test Sharpe | test CAGR | full CAGR | turnover |
|---|---|---|---|---|---|
| blend_365mom_180rev_top5 | 0.16 | -0.08 | -20.92% | -18.20% | 13.46 |
| blend_365mom_180rev_top10 | 0.29 | -0.06 | -17.10% | -9.18% | 9.22 |
| blend_365mom_180rev_top20 | 0.52 | 0.19 | -4.51% | 5.65% | 4.14 |

### Comparison (standalone signals)

| config | test Sharpe | test CAGR |
|---|---|---|
| rev_180d_bot5 (selected reversal) | 0.48 | 31.39% |
| spot_mom_top10 (selected momentum) | 0.20 | -6.11% |
| EW benchmark | 0.23 | — |
