import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import os
import uuid

np.random.seed(42)

NUM_STATIONS = 6
SENSORS_PER_STATION = 2
START_DATE = "2025-07-12"
FREQUENCY = "10min"


def generate_time_index():
    start = pd.to_datetime(START_DATE)
    end = start + pd.Timedelta(days=1) - pd.Timedelta(minutes=10)
    return pd.date_range(start=start, end=end, freq=FREQUENCY)


def generate_station_ids():
    return [f"ST_{i:03d}" for i in range(1, NUM_STATIONS + 1)]

def generate_sensor_ids():
    return ["TEMP_01", "CHEM_01"]

def generate_telemetry_data():
    timestamps = generate_time_index()
    stations = generate_station_ids()
    sensors = generate_sensor_ids()

    rows = []

    for ts in timestamps:
        for station in stations:
            for sensor in sensors:
                if sensor == "TEMP_01":
                    temperature = np.random.uniform(26.0, 31.0)
                    oxygen = np.random.uniform(4.0, 6.5)
                    salinity = np.random.uniform(34.5, 35.5)
                    ph = np.random.uniform(7.9, 8.2)

                elif sensor == "CHEM_01":
                    temperature = np.random.uniform(24.0, 29.0)
                    oxygen = np.random.uniform(5.0, 7.0)
                    salinity = np.random.uniform(34.0, 36.5)
                    ph = np.random.uniform(7.8, 8.3)
                ingestion_delay = np.random.randint(0, 31)
                ingestion_ts = ts + timedelta(seconds=int(ingestion_delay))

                row = {
                    "station_id": station,
                    "sensor_id": sensor,
                    "event_timestamp": ts,
                    "ingestion_timestamp": ingestion_ts,
                    "water_temperature_c": temperature,
                    "salinity_psu": salinity,
                    "ph_level": ph,
                    "dissolved_oxygen_mg_l": oxygen,
                    "battery_level_pct": np.random.uniform(60, 100),
                    "device_status": "active",
                    "event_id": str(uuid.uuid4()),
                }

                rows.append(row)

    return pd.DataFrame(rows)

def save_to_csv(df):
    output_path = "data/raw"
    os.makedirs(output_path, exist_ok=True)

    file_name = f"telemetry_{START_DATE.replace('-', '_')}.csv"
    df.to_csv(os.path.join(output_path, file_name), index=False)

if __name__ == "__main__":
    df = generate_telemetry_data()
    save_to_csv(df)

    print("Rows generated:", len(df))
    print(df.head())
