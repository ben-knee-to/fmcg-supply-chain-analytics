CREATE OR REPLACE VIEW analytics.vw_warehouse_detail AS
SELECT w.warehouse_id,w.manager_id,w.location_type,w.capacity_size,w.owner_type,
 w.workers_num,w.established_year,w.established_year_missing,w.workers_num_missing,
 w.distance_from_hub_km,w.hub_distance_band,g.zone,g.regional_zone,
 i.flood_impacted,i.flood_proof,i.electric_supply,i.temp_reg_mach,i.govt_certificate,
 f.shipment_weight_ton,f.refill_requests_l3m,f.transport_issues_l1y,
 f.competitor_count,f.retail_shop_count,f.distributor_count,f.storage_issues_l3m,
 f.breakdowns_l3m,f.govt_checks_l3m,f.retailers_per_distributor,
 f.distributors_per_1000_retailers,f.has_competition,f.certificate_missing
FROM analytics.fact_warehouse_shipments f
JOIN analytics.dim_warehouse w USING(warehouse_key)
JOIN analytics.dim_geography g USING(geography_key)
JOIN analytics.dim_infrastructure i USING(infrastructure_key);
CREATE OR REPLACE VIEW analytics.vw_executive_kpis AS
SELECT COUNT(*) AS warehouse_count,SUM(shipment_weight_ton) AS total_recorded_shipment_ton,
 ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton,
 ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY shipment_weight_ton))::numeric,2) AS median_recorded_shipment_ton,
 COUNT(*) FILTER (WHERE established_year_missing=1) AS missing_establishment_year_count
FROM analytics.vw_warehouse_detail;
CREATE OR REPLACE VIEW analytics.vw_zone_summary AS
SELECT zone,COUNT(*) AS warehouse_count,SUM(shipment_weight_ton) AS total_recorded_shipment_ton,
 ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton,
 ROUND(AVG(retail_shop_count),2) AS avg_retail_shops,
 ROUND(AVG(distributor_count),2) AS avg_distributors
FROM analytics.vw_warehouse_detail GROUP BY zone;
CREATE OR REPLACE VIEW analytics.vw_regional_summary AS
SELECT zone,regional_zone,COUNT(*) AS warehouse_count,
 SUM(shipment_weight_ton) AS total_recorded_shipment_ton,
 ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton
FROM analytics.vw_warehouse_detail GROUP BY zone,regional_zone;
CREATE OR REPLACE VIEW analytics.vw_capacity_location AS
SELECT zone,location_type,capacity_size,COUNT(*) AS warehouse_count,
 SUM(shipment_weight_ton) AS total_recorded_shipment_ton,
 ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton
FROM analytics.vw_warehouse_detail GROUP BY zone,location_type,capacity_size;
CREATE OR REPLACE VIEW analytics.vw_operational_summary AS
SELECT zone,COUNT(*) AS warehouse_count,
 ROUND(AVG(refill_requests_l3m),2) AS avg_refills_l3m,
 ROUND(AVG(storage_issues_l3m),2) AS avg_storage_issues_l3m,
 ROUND(AVG(breakdowns_l3m),2) AS avg_breakdowns_l3m,
 ROUND(AVG(transport_issues_l1y),2) AS avg_transport_issues_l1y,
 ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton
FROM analytics.vw_warehouse_detail GROUP BY zone;
CREATE OR REPLACE VIEW analytics.vw_infrastructure_summary AS
SELECT electric_supply,flood_proof,temp_reg_mach,govt_certificate,
 COUNT(*) AS warehouse_count,ROUND(AVG(shipment_weight_ton),2) AS avg_recorded_shipment_ton,
 SUM(shipment_weight_ton) AS total_recorded_shipment_ton
FROM analytics.vw_warehouse_detail
GROUP BY electric_supply,flood_proof,temp_reg_mach,govt_certificate;

