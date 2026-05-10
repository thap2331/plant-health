#!/usr/bin/env python3
"""
For each moisture reading, find the nearest image captured within 30 minutes.
Output: data/labeled_dataset.csv — foundation for model training.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "water" / "moisture_log.csv"
IMAGE_DIR = DATA_DIR / "images"
OUT_PATH = DATA_DIR / "labeled_dataset.csv"


def load_moisture():
    df = pd.read_csv(CSV_PATH, header=0,
                     names=['timestamp', 'raw', 'moisture_pct', 'is_dry', 'watered', 'cooldown_active'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    for col in ('is_dry', 'watered', 'cooldown_active'):
        df[col] = df[col].astype(str).str.lower() == 'true'
    return df.sort_values('timestamp').reset_index(drop=True)


def load_images():
    rows = []
    for p in sorted(IMAGE_DIR.glob("plant_*.jpg")):
        stem = p.stem[len("plant_"):]
        ts = datetime.strptime(stem, "%Y%m%d_%H%M%S")
        rows.append({"image_file": p.name, "image_timestamp": pd.Timestamp(ts)})
    return pd.DataFrame(rows).sort_values('image_timestamp').reset_index(drop=True)


def main():
    moisture = load_moisture()
    images = load_images()

    if images.empty:
        print(f"No images found in {IMAGE_DIR}")
        return

    labeled = pd.merge_asof(
        moisture,
        images,
        left_on='timestamp',
        right_on='image_timestamp',
        direction='nearest',
        tolerance=pd.Timedelta('30min'),
    )

    labeled['time_delta_sec'] = (
        labeled['image_timestamp'] - labeled['timestamp']
    ).dt.total_seconds().abs()

    labeled.to_csv(OUT_PATH, index=False)

    matched = labeled['image_file'].notna().sum()
    total = len(labeled)
    print(f"Moisture readings : {total}")
    print(f"Matched to image  : {matched}  (within 30 min)")
    print(f"Unmatched         : {total - matched}")
    print(f"Output            : {OUT_PATH}")

    if matched:
        print()
        print(labeled[['timestamp', 'moisture_pct', 'is_dry', 'image_file', 'time_delta_sec']]
              .dropna(subset=['image_file'])
              .head(10)
              .to_string(index=False))


if __name__ == "__main__":
    main()
