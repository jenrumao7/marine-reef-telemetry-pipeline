# Marine Reef Telemetry Intelligence Pipeline
Design and implement a medallion-architecture-based telemetry intelligence pipeline simulating distributed marine reef monitoring stations. The system ingests high-frequency sensor events, performs data validation and cleaning, computes reef bleaching risk metrics, and produces daily regional summaries. The pipeline will be built locally (pandas + SQLite) and later refactored to PySpark to simulate scalable lakehouse processing.

## System Scale Assumptions:
* 100 reef stations
* 4 sensors per station
* Telemetry every 10 minutes
* ~57,600 events per day
* Simulate 30 days initially (~1.7M events)


## Raw Telemetry Event Schema
**Fields:**
* event_id (string, unique)
* station_id (string)
* sensor_id (string)
* event_timestamp (datetime, UTC)
* ingestion_timestamp (datetime, UTC)
* water_temperature_c (float)
* salinity_psu (float)
* ph_level (float)
* dissolved_oxygen_mg_l (float)
* battery_level_pct (float)
* device_status (string: active/offline/error)

## Simulated Data Quality Conditions
We will simulate:
* 2–5% missing telemetry
* 1% duplicate events
* Out-of-order event arrival
* Random device outages
* Occasional extreme temperature spikes
These justify Bronze vs Silver.

## Architecture

**Bronze :**
Raw events stored exactly as received. No filtering.

**Silver**
* Deduplicated
* Validated
* Null checks
* Schema enforced
* Invalid records quarantined

**Gold**
* Daily station-level aggregates
* Regional summaries
* Reef bleaching risk score
* Device uptime metrics

Telemetry Events
      ↓
Bronze (raw store)
      ↓
Silver (clean + validated)
      ↓
Gold (aggregated risk metrics)

## Target Analytical Data Model

Fact tables:
* fact_telemetry
* fact_daily_risk

Dimension tables:
* dim_station
* dim_sensor
* dim_region
* dim_date

