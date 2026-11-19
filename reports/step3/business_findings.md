# Step 3 EDA — business findings

- Warehouse records: **25,000**
- Total recorded shipped weight: **552,565,823** (source-stated tons, unit not independently verified)
- Average shipped weight: **22,102.63**
- Median shipped weight: **22,101.00**
- Zone with highest aggregate recorded shipment weight: **North**, 228,165,823, from 10,278 warehouses.

## Interpretation boundaries
- Shipment volume is not demand, sales, stockouts, service level or profitability.
- Comparisons are observational and not causal.
- Recent operational measures may be contemporaneous with shipments; do not use them as pre-decision model predictors without timing verification.
- Each warehouse appears once; no time-series trends or forecasting are justified.
- Aggregate shipment sums assume each row is a distinct nonoverlapping warehouse observation.
- Large regional totals reflect both record counts and per-warehouse shipment volumes.
- Source states tons; confirm business units before operational use.

## Further analysis
- Review warehouse counts and confidence intervals alongside mean differences.
- Investigate missing establishment years before any age-related claims.
- Obtain demand, inventory, costs, lead times and dates to support true supply optimisation.
