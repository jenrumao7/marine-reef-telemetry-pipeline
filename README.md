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

## Time Semantics

In a distributed telemetry system, it is critical to distinguish between when an event actually occurred and when it was received by the system. These two timestamps serve different purposes and must not be conflated.

*event_timestamp* represents the exact time a sensor generated the reading. This timestamp drives all analytical correctness in the system. It determines:

* The logical date of the event
* The partition key (event_date derived from event_timestamp)
* Aggregation windows
* Daily risk scoring calculations

All analytical queries, aggregations, and reporting logic are based strictly on event_timestamp to ensure historical accuracy.

*ingestion_timestamp* represents the time the event was received and recorded by the pipeline. This timestamp is used for operational and monitoring purposes, including:

* Measuring ingestion latency (ingestion_timestamp - event_timestamp)
* Monitoring SLA compliance
* Detecting late-arriving data
* Supporting backfill and replay logic

Late-arriving data occurs when an event is received after its expected processing window. 
For example, if an event generated on January 1 arrives on January 3, it must still be written to the January 1 partition based on event_timestamp. Historical aggregates for that partition may need to be updated to preserve analytical correctness. This is a controlled update of historical partitions, not repartitioning.

Late data should not be confused with stale data. Late data arrives after its expected window but remains valid for processing. Stale data refers to events that are too old or outside acceptable processing bounds and may be excluded based on system policy.

Separating event time from ingestion time ensures both analytical correctness and operational observability.

## Partition Strategy

As telemetry data volume grows, full table scans become inefficient and computationally expensive. Since this system processes time-series, append-heavy data that is predominantly queried by date, physical data partitioning is required to improve performance.

Partitioning organizes data storage by a chosen key so that queries can read only relevant subsets of data instead of scanning the entire dataset. In this system, data will be partitioned by event_date, which is derived from event_timestamp.

Partitioning by event_date aligns with the dominant query pattern: daily risk scoring, time-based aggregations, and historical analysis. For example, when computing metrics for a specific day, the system can read only that day’s partition rather than scanning all historical telemetry.

Late-arriving data is written into the partition corresponding to its event_date, not its ingestion date. This preserves analytical correctness because all aggregations are based on when the event occurred, not when it was received.

Partitioning by ingestion_date would misalign data with analytical windows and produce incorrect daily aggregates.

More granular partitioning strategies, such as partitioning by both event_date and station_id, are intentionally avoided at this stage. Given the current scale (*~57,000 events per day*), date-level partitioning provides sufficient pruning efficiency without introducing unnecessary complexity or small-file fragmentation.

This partition strategy supports efficient query pruning today and scales naturally when the system is migrated to distributed processing in Spark.

## Natural Keys vs Surrogate Keys

In analytical systems, every table requires a primary key to uniquely identify records. There are two types of identifiers used in data modeling: natural keys and surrogate keys. Each serves a different purpose.

## Natural Keys

A natural key is derived from real-world business attributes. It has domain meaning and exists independently of the database.

In this system, a telemetry event represents a single reading emitted by a specific sensor at a specific time. The natural identity of a telemetry event is defined by the composite key:

(station_id, sensor_id, event_timestamp)

Under the simulation assumptions, a sensor produces at most one reading per configured interval (10 minutes). Therefore, this composite key maps directly to a single real-world occurrence.

This composite natural key is used in the Silver layer to enforce uniqueness and deduplicate events. It ensures idempotent processing — re-ingesting the same raw data will not produce duplicate analytical records.

Natural keys are appropriate for fact identity because they reflect real-world uniqueness.

## Surrogate Keys

A surrogate key is an artificial identifier generated by the system. It has no business meaning and exists purely for modeling and performance purposes. Surrogate keys are typically integers.

In the Gold (warehouse) layer, dimension tables will use surrogate keys as primary keys. For example:

dim_station
* station_key (surrogate primary key)
* station_id (natural key)
* region
* latitude
* longitude

dim_sensor
* sensor_key (surrogate primary key)
* sensor_id (natural key)
* sensor_type

The fact tables in the warehouse will reference these surrogate keys instead of storing long string identifiers repeatedly.
# For example:
fact_telemetry
* station_key
* sensor_key
* date_key
* water_temperature_c
* dissolved_oxygen_mg_l
* salinity_psu

## Why This Separation Matters
Natural keys are used to represent real-world identity and enforce correctness during ingestion and deduplication.
Surrogate keys are used in the analytical warehouse layer because:
* Integer joins are faster than string joins at scale
* Storage footprint is reduced
* Historical changes to dimension attributes can be tracked without rewriting fact tables
* Business identifiers are decoupled from storage structure
As the system scales (e.g., when migrated to Spark and handling millions or billions of records), surrogate-key-based joins improve performance and support slowly changing dimension patterns.

## Final Design Decision

* Bronze and Silver layers retain natural keys for correctness and transparency.
* Gold layer introduces surrogate keys in dimension tables.
* Fact tables in the warehouse reference surrogate keys for performance and scalability.
* This design balances real-world identity correctness with warehouse performance and future scalability.