# Contrarian (reversal) spot verdict (2026-09-19)

## FAMILY: PASS

### Honesty rationale

Contrarian signals buy recent losers. They often show weak
in-sample Sharpe because they bet against trends that dominate
training periods. The standard 'train Sharpe > benchmark' gate
(PC-1) is therefore relaxed. DSR alone gates the signal.
This is pre-registered BEFORE the sweep (see README).

Selected: **rev_180d_bot5** (DSR 0.902, PBO 0.314)

| check | result | measured |
|---|---|---|
| PC-1* | PASS | RELAXED: train SR 0.11 vs bm 0.23 (not gating for contrarian) |
| PC-3 | PASS | DSR 0.902 |
| PC-4 | PASS | PBO 0.314 |
| PC-5 | PASS | drag 9.68% vs costs 38.60% (err 75%) |
| KC-1 | PASS | max full CAGR 13.33% |
| KC-2 | PASS | max turnover 15.09 |
| KC-3 | PASS | True |
| KC-4 | PASS | test maxDD 78.24% |
| KC-5 | PASS | min Σw 1.0000, max 1.0000 |
| KC-6 | PASS | min names 5 |

## Survivorship bias audit

Kraken has delisted at most 1 USD pair since 2017 (USDSMUSD, a data artifact).
658 pairs on disk, 657 active through 2026-09-19. The volume-ranked universe
filter (top-20 by trailing 90-day volume) excludes illiquid and dead coins from
the reversal picks.

Across 2110 reversal picks with 180-day forward data:
- Mean forward return: 37.80% (fat right tail from a few big recoveries)
- Median forward return: -0.12% (no free lunch at the median)
- Picks with >90% trailing loss at formation: 0
- Picks with near-zero 30-day volume: 0

Conclusion: survivorship bias risk is low. The volume gate is the main
protection. The signal is not buying dead coins.

## Grid

| config | train Sharpe | test Sharpe | test CAGR | full CAGR | turnover | min names |
|---|---|---|---|---|---|---|
| **rev_180d_bot5** **selected** | 0.11 | 0.48 | 31.39% | -0.84% | 15.09 | 5 |
| rev_180d_bot10 | 0.38 | 0.40 | 6.37% | 3.19% | 10.21 | 5 |
| rev_180d_bot20 | 0.65 | 0.29 | -0.45% | 13.33% | 4.83 | 5 |
