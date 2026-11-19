# Step 2 data-quality report

- Records retained: 25,000 / 25,000
- Missing establishment year: 11,881
- Missing workers: 990
- Missing certificate: 908
- Unique warehouse IDs: 25,000
- Missing targets: 0
- Full-dataset imputation: **not performed**
- Outliers: flagged, not deleted or capped
- Leakage-risk features: num_refill_req_l3m, storage_issue_reported_l3m, wh_breakdown_l3m, govt_check_l3m, transport_issue_l1y

## Interpretation
The target measures historical shipped weight, not observed demand. No temporal or demand forecast is justified without further data. All categorical encoding and numeric imputation must be fitted on training data only.
