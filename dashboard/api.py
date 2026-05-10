from fastapi import FastAPI
from fastapi.responses import FileResponse
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

app = FastAPI()
DATA_DIR = Path("/app/data")
CSV_PATH = DATA_DIR / "moisture_log.csv"
IMAGE_DIR = DATA_DIR / "images"


def load_df():
    df = pd.read_csv(CSV_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    for col in ('is_dry', 'watered', 'cooldown_active'):
        df[col] = df[col] == 'True'
    return df


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/moisture")
def moisture_all():
    return load_df().to_dict(orient="records")


@app.get("/moisture/latest")
def moisture_latest():
    df = load_df()
    cutoff = datetime.now() - timedelta(hours=24)
    return df[df['timestamp'] >= cutoff].to_dict(orient="records")


@app.get("/images/latest")
def image_latest():
    images = sorted(IMAGE_DIR.glob("plant_*.jpg"))
    if not images:
        return {"error": "no images"}
    return FileResponse(images[-1])


@app.get("/images/list")
def image_list():
    images = sorted(IMAGE_DIR.glob("plant_*.jpg"))
    result = []
    for p in images:
        stem = p.stem[len("plant_"):]
        ts = datetime.strptime(stem, "%Y%m%d_%H%M%S").isoformat()
        result.append({"filename": p.name, "timestamp": ts})
    return result
