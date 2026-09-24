"""
Export stored readings as a training CSV (same columns as data/bmtc_raw.csv).

Run:  python -m scripts.export_training_data  [output.csv]
Then: copy it to data/bmtc_raw.csv and run python -m app.ml.train
"""
import csv
import sys

from app.services import analytics_service

COLUMNS = ["trip_id", "stop_id", "minute_of_day", "is_peak_hour", "traffic_level", "vehicle_density",
           "avg_speed", "road_occupancy", "traffic_flow", "delay_min", "occupancy_pct"]


def main(path: str = "data/training_export.csv") -> None:
    rows = analytics_service.training_rows()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows -> {path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
