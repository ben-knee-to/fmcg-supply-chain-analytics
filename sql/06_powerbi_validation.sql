-- Run in pgAdmin on fmcg_supply_chain after Step 4 scripts have been executed.
-- This script is read-only and does not change the warehouse.
SELECT COUNT(*) AS rows, COUNT(DISTINCT warehouse_id) AS distinct_warehouses,
 SUM(shipment_weight_ton) AS total_shipment,
 ROUND(AVG(shipment_weight_ton),2) AS avg_shipment,
 COUNT(*) FILTER (WHERE established_year_missing = 1) AS missing_est_year
FROM analytics.vw_warehouse_detail;

SELECT zone, COUNT(*) AS warehouse_count,
 ROUND(AVG(shipment_weight_ton),2) AS mean_shipment
FROM analytics.vw_warehouse_detail GROUP BY zone ORDER BY zone;

SELECT location_type, COUNT(*) AS warehouse_count,
 ROUND(AVG(shipment_weight_ton),2) AS mean_shipment
FROM analytics.vw_warehouse_detail GROUP BY location_type ORDER BY location_type;

SELECT COUNT(*) AS fact_rows,
 COUNT(*) FILTER (WHERE warehouse_key IS NULL OR geography_key IS NULL OR infrastructure_key IS NULL) AS null_fk_rows
FROM analytics.fact_warehouse_shipments;

SELECT COUNT(*) AS unmatched_warehouse_keys
FROM analytics.fact_warehouse_shipments f
LEFT JOIN analytics.dim_warehouse w USING (warehouse_key)
WHERE w.warehouse_key IS NULL;

-- Avoid summing vw_zone_summary together with vw_warehouse_detail in the same model.

