# FMCG Step 5B robustness audit

All results below use the original 20,000-row training partition only. The 5,000-row holdout is not read or rescored.

## Cross-validation ablations

| scenario                    |   cv_mae |   cv_mae_sd |   cv_rmse |   cv_r2 |
|:----------------------------|---------:|------------:|----------:|--------:|
| full_conservative           |  6451.54 |      38.46  |   8396.58 |   0.477 |
| without_est_year            |  8758.43 |      31.321 |  10778.5  |   0.139 |
| without_year_or_flag        |  8930.08 |      18.824 |  10954.6  |   0.111 |
| without_year_or_missingness |  9334.3  |       3.914 |  11271.1  |   0.058 |
| stable_operational          |  9541.21 |      16.362 |  11534.1  |   0.014 |
| without_year_or_certificate |  9541.73 |      15.829 |  11534.7  |   0.014 |
| mean_baseline               |  9596.49 |      16.354 |  11620.1  |  -0.001 |

## Interpretation

High correlation is not proof of synthetic generation, causality or leakage. Timing, missingness mechanism and source provenance require independent verification.

No new deployment-ready model is designated by this audit. The original Step 5 model is preserved.

Do not use predicted historical shipments as measured demand or optimal inventory quantities.