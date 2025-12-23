CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles JSON NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TYPE dataset_source AS ENUM ('acs', 'hud');
CREATE TABLE IF NOT EXISTS datasets (
    id VARCHAR(64) PRIMARY KEY,
    source dataset_source NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    schema JSON,
    sample JSON,
    last_updated TIMESTAMP
);

CREATE TYPE ingest_type AS ENUM ('acs', 'hud');
CREATE TYPE ingest_status AS ENUM ('queued', 'running', 'succeeded', 'failed');
CREATE TABLE IF NOT EXISTS ingest_jobs (
    id UUID PRIMARY KEY,
    type ingest_type NOT NULL,
    status ingest_status NOT NULL DEFAULT 'queued',
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    message TEXT,
    output_uri TEXT,
    params JSON
);

CREATE TYPE region_type AS ENUM ('county', 'state', 'msa');
CREATE TABLE IF NOT EXISTS regions (
    region_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type region_type NOT NULL,
    state_fips VARCHAR(2) NOT NULL,
    county_fips VARCHAR(3),
    CONSTRAINT uix_state_county UNIQUE (state_fips, county_fips)
);

CREATE TABLE IF NOT EXISTS metrics_cache (
    id UUID PRIMARY KEY,
    region_id VARCHAR(32) NOT NULL,
    year INT NOT NULL,
    median_household_income FLOAT,
    median_gross_rent FLOAT,
    rent_to_income_ratio FLOAT,
    vacancy_rate FLOAT,
    hud_fmr_2br FLOAT,
    population INT,
    sources JSON NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uix_region_year UNIQUE (region_id, year)
);

