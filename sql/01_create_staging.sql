-- Run after creating database fmcg_supply_chain in pgAdmin.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS staging.warehouse_raw (
  "Ware_house_ID" TEXT,
  "WH_Manager_ID" TEXT,
  "Location_type" TEXT,
  "WH_capacity_size" TEXT,
  "zone" TEXT,
  "WH_regional_zone" TEXT,
  "num_refill_req_l3m" INTEGER,
  "transport_issue_l1y" INTEGER,
  "Competitor_in_mkt" INTEGER,
  "retail_shop_num" INTEGER,
  "wh_owner_type" TEXT,
  "distributor_num" INTEGER,
  "flood_impacted" INTEGER,
  "flood_proof" INTEGER,
  "electric_supply" INTEGER,
  "dist_from_hub" INTEGER,
  "workers_num" INTEGER,
  "wh_est_year" INTEGER,
  "storage_issue_reported_l3m" INTEGER,
  "temp_reg_mach" INTEGER,
  "approved_wh_govt_certificate" TEXT,
  "wh_breakdown_l3m" INTEGER,
  "govt_check_l3m" INTEGER,
  "product_wg_ton" INTEGER,
  "wh_est_year_missing" INTEGER,
  "workers_num_missing" INTEGER,
  "approved_wh_govt_certificate_missing" INTEGER,
  "retailers_per_distributor" DOUBLE PRECISION,
  "distributors_per_1000_retailers" DOUBLE PRECISION,
  "hub_distance_band" TEXT,
  "has_competition" INTEGER,
  CONSTRAINT pk_staging_warehouse PRIMARY KEY ("Ware_house_ID"),
  CONSTRAINT ck_staging_weight CHECK ("product_wg_ton" >= 0)
);

