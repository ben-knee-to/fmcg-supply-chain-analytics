# Step 1: FMCG Data Profiling Report

- Rows: 25,000
- Columns: 24
- Missing cells: 13,779
- Duplicate rows: 0
- Unique warehouse IDs: 25,000
- Missing expected columns: []
- Unexpected columns: []

## Target: product_wg_ton

- Mean: 22,102.63
- Median: 22,101.00
- Standard deviation: 11,607.76
- Minimum: 2,065
- Maximum: 55,151

## Missing data

                      column  missing_count  missing_pct
                 workers_num            990        3.960
                 wh_est_year          11881       47.524
approved_wh_govt_certificate            908        3.632

## Interpretation

The target measures historical shipments in the prior three months, not demand. Without stockouts, sales, inventory, dates and costs, optimal allocation cannot be established. Do not drop or impute missing values in Step 1. Verify target units and dataset grain with the data owner.
