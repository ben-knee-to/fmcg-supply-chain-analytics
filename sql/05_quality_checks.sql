-- Zero is expected for every failed_* check; counts and totals should match CSV.
SELECT (SELECT COUNT(*) FROM staging.warehouse_raw) AS staging_count,
 (SELECT COUNT(*) FROM analytics.dim_warehouse) AS warehouse_dim_count,
 (SELECT COUNT(*) FROM analytics.fact_warehouse_shipments) AS fact_count;
SELECT (SELECT SUM("product_wg_ton") FROM staging.warehouse_raw) AS staging_weight,
 (SELECT SUM(shipment_weight_ton) FROM analytics.fact_warehouse_shipments) AS fact_weight;
SELECT COUNT(*) AS failed_orphan_fact_rows FROM analytics.fact_warehouse_shipments f
LEFT JOIN analytics.dim_warehouse w ON f.warehouse_key=w.warehouse_key
LEFT JOIN analytics.dim_geography g ON f.geography_key=g.geography_key
LEFT JOIN analytics.dim_infrastructure i ON f.infrastructure_key=i.infrastructure_key
WHERE w.warehouse_key IS NULL OR g.geography_key IS NULL OR i.infrastructure_key IS NULL;
SELECT COUNT(*) AS failed_duplicate_warehouse_ids FROM
 (SELECT warehouse_id FROM analytics.dim_warehouse GROUP BY warehouse_id HAVING COUNT(*)>1) d;
SELECT COUNT(*) AS failed_detail_count_difference FROM
 (SELECT (SELECT COUNT(*) FROM analytics.vw_warehouse_detail) <> (SELECT COUNT(*) FROM staging.warehouse_raw) AS bad) x WHERE bad;
SELECT COUNT(*) AS failed_negative_or_null_weights FROM analytics.fact_warehouse_shipments WHERE shipment_weight_ton IS NULL OR shipment_weight_ton<0;

