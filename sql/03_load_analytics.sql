-- Rerunnable load: staging is source of truth, fact/dim tables rebuilt in one transaction.
BEGIN;
TRUNCATE analytics.fact_warehouse_shipments, analytics.dim_warehouse,
 analytics.dim_geography, analytics.dim_infrastructure RESTART IDENTITY CASCADE;
INSERT INTO analytics.dim_geography(zone,regional_zone)
SELECT DISTINCT "zone", "WH_regional_zone" FROM staging.warehouse_raw;
INSERT INTO analytics.dim_infrastructure(flood_impacted,flood_proof,electric_supply,temp_reg_mach,govt_certificate)
SELECT DISTINCT "flood_impacted","flood_proof","electric_supply","temp_reg_mach",
 COALESCE("approved_wh_govt_certificate",'Missing') FROM staging.warehouse_raw;
INSERT INTO analytics.dim_warehouse(warehouse_id,manager_id,location_type,capacity_size,owner_type,workers_num,established_year,established_year_missing,workers_num_missing,distance_from_hub_km,hub_distance_band)
SELECT "Ware_house_ID","WH_Manager_ID","Location_type","WH_capacity_size","wh_owner_type",
 "workers_num","wh_est_year","wh_est_year_missing","workers_num_missing","dist_from_hub","hub_distance_band"
FROM staging.warehouse_raw;
INSERT INTO analytics.fact_warehouse_shipments(warehouse_key,geography_key,infrastructure_key,shipment_weight_ton,refill_requests_l3m,transport_issues_l1y,competitor_count,retail_shop_count,distributor_count,storage_issues_l3m,breakdowns_l3m,govt_checks_l3m,retailers_per_distributor,distributors_per_1000_retailers,has_competition,certificate_missing)
SELECT w.warehouse_key,g.geography_key,i.infrastructure_key,s."product_wg_ton",s."num_refill_req_l3m",s."transport_issue_l1y",s."Competitor_in_mkt",s."retail_shop_num",s."distributor_num",s."storage_issue_reported_l3m",s."wh_breakdown_l3m",s."govt_check_l3m",s."retailers_per_distributor",s."distributors_per_1000_retailers",s."has_competition",s."approved_wh_govt_certificate_missing"
FROM staging.warehouse_raw s
JOIN analytics.dim_warehouse w ON w.warehouse_id=s."Ware_house_ID"
JOIN analytics.dim_geography g ON g.zone=s."zone" AND g.regional_zone=s."WH_regional_zone"
JOIN analytics.dim_infrastructure i ON i.flood_impacted=s."flood_impacted" AND i.flood_proof=s."flood_proof" AND i.electric_supply=s."electric_supply" AND i.temp_reg_mach=s."temp_reg_mach" AND i.govt_certificate=COALESCE(s."approved_wh_govt_certificate",'Missing');
COMMIT;


