# Marine Reef Telemetry Intelligence Pipeline
Design and implement a medallion-architecture-based telemetry intelligence pipeline simulating distributed marine reef monitoring stations. The system ingests high-frequency sensor events, performs data validation and cleaning, computes reef bleaching risk metrics, and produces daily regional summaries. The pipeline will be built locally (pandas + SQLite) and later refactored to PySpark to simulate scalable lakehouse processing.

System Scale Assumptions:
* 100 reef stations
* 4 sensors per station
* Telemetry every 10 minutes
* ~57,600 events per day
* Simulate 30 days initially (~1.7M events)

