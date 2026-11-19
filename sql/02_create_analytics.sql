CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS analytics.dim_geography (
 geography_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 zone TEXT NOT NULL,
 regional_zone TEXT NOT NULL,
 UNIQUE(zone, regional_zone)
);
CREATE TABLE IF NOT EXISTS analytics.dim_infrastructure (
 infrastructure_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 flood_impacted INTEGER NOT NULL CHECK(flood_impacted IN (0,1)),
 flood_proof INTEGER NOT NULL CHECK(flood_proof IN (0,1)),
 electric_supply INTEGER NOT NULL CHECK(electric_supply IN (0,1)),
 temp_reg_mach INTEGER NOT NULL CHECK(temp_reg_mach IN (0,1)),
 govt_certificate TEXT NOT NULL,
 UNIQUE(flood_impacted,flood_proof,electric_supply,temp_reg_mach,govt_certificate)
);
CREATE TABLE IF NOT EXISTS analytics.dim_warehouse (
 warehouse_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 warehouse_id TEXT NOT NULL UNIQUE,
 manager_id TEXT,
 location_type TEXT,
 capacity_size TEXT,
 owner_type TEXT,
 workers_num INTEGER CHECK(workers_num IS NULL OR workers_num >= 0),
 established_year INTEGER,
 established_year_missing INTEGER NOT NULL CHECK(established_year_missing IN (0,1)),
 workers_num_missing INTEGER NOT NULL CHECK(workers_num_missing IN (0,1)),
 distance_from_hub_km INTEGER CHECK(distance_from_hub_km >= 0),
 hub_distance_band TEXT
);
CREATE TABLE IF NOT EXISTS analytics.fact_warehouse_shipments (
 warehouse_key BIGINT PRIMARY KEY REFERENCES analytics.dim_warehouse(warehouse_key),
 geography_key BIGINT NOT NULL REFERENCES analytics.dim_geography(geography_key),
 infrastructure_key BIGINT NOT NULL REFERENCES analytics.dim_infrastructure(infrastructure_key),
 shipment_weight_ton NUMERIC(16,3) NOT NULL CHECK(shipment_weight_ton >= 0),
 refill_requests_l3m INTEGER NOT NULL CHECK(refill_requests_l3m >= 0),
 transport_issues_l1y INTEGER NOT NULL CHECK(transport_issues_l1y >= 0),
 competitor_count INTEGER NOT NULL CHECK(competitor_count >= 0),
 retail_shop_count INTEGER NOT NULL CHECK(retail_shop_count >= 0),
 distributor_count INTEGER NOT NULL CHECK(distributor_count >= 0),
 storage_issues_l3m INTEGER NOT NULL CHECK(storage_issues_l3m >= 0),
 breakdowns_l3m INTEGER NOT NULL CHECK(breakdowns_l3m >= 0),
 govt_checks_l3m INTEGER NOT NULL CHECK(govt_checks_l3m >= 0),
 retailers_per_distributor DOUBLE PRECISION,
 distributors_per_1000_retailers DOUBLE PRECISION,
 has_competition INTEGER NOT NULL CHECK(has_competition IN (0,1)),
 certificate_missing INTEGER NOT NULL CHECK(certificate_missing IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_fact_geo ON analytics.fact_warehouse_shipments(geography_key);
CREATE INDEX IF NOT EXISTS idx_fact_infra ON analytics.fact_warehouse_shipments(infrastructure_key);

