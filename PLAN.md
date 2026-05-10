# Plan: Plant Health Dashboard (FastAPI + Streamlit + Docker)

## Context
Building a local dashboard to visualize plant moisture data and images synced from a Raspberry Pi. The Pi writes `moisture_log.csv` and `plant_*.jpg` to `~/logs/plant-water/`. This dashboard runs locally in Docker, consuming that synced data.

---

## Key facts
- CSV actual columns: `timestamp, raw, moisture_pct, is_dry, watered, cooldown_active`
- Moisture chart: show `moisture_pct` (0–100%), red dashed threshold at **40**
- Images: `~/logs/plant-water/images/plant_YYYYMMDD_HHMMSS.jpg`
- Moisture CSV on Pi: `~/logs/plant-water/water/moisture_log.csv`
- No Dockerfile, docker-compose, data/, or requirements.txt exist yet

---

## Files to create

### `dashboard/requirements.txt`
```
fastapi
uvicorn
pandas
streamlit
plotly
requests
python-multipart
```

### `dashboard/api.py` (FastAPI)
Data paths: `/app/data/moisture_log.csv`, `/app/data/images/`

Endpoints:
- `GET /health` → `{"status": "ok"}`
- `GET /moisture` → all CSV rows as JSON list
- `GET /moisture/latest` → last 24h rows filtered by `timestamp`
- `GET /images/latest` → `FileResponse` of most recent `plant_*.jpg` (sorted by filename)
- `GET /images/list` → list of `{filename, timestamp}` dicts parsed from filename

### `dashboard/app.py` (Streamlit)
- API base: `http://api:8000`
- Title: "Plant Health Dashboard"
- 4 metric cards: latest moisture %, status (Dry/OK based on `is_dry`), last watered timestamp (last row where `watered==True`), total readings today
- Plotly line chart of `moisture_pct` over last 24h + horizontal red dashed line at y=40
- Latest plant image below chart
- `st.rerun()` with `time.sleep(60)` at bottom for auto-refresh

### `Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard/ ./dashboard/
```
No COPY for data/ — it's volume-mounted at runtime.

### `docker-compose.yml`
```yaml
services:
  api:
    build: .
    command: uvicorn dashboard.api:app --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]

  streamlit:
    build: .
    command: streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
    ports: ["8501:8501"]
    volumes: ["./data:/app/data"]
    depends_on: [api]
```

### `data/.gitkeep`
Empty file to track the directory in git.

---

## Files to modify

### `.gitignore`
Add:
```
data/*
!data/.gitkeep
```

### `Makefile` — append these targets
```makefile
PI_USER    = suraj
PI_IP      = <FILL_IN_PI_IP>
PI_LOG_DIR = ~/logs/plant-water

sync:
	scp $(PI_USER)@$(PI_IP):$(PI_LOG_DIR)/water/moisture_log.csv ./data/
	scp -r $(PI_USER)@$(PI_IP):$(PI_LOG_DIR)/images/ ./data/

up:
	docker compose up --build

down:
	docker compose down

dev: sync up
```
Note: Pi moisture CSV is in `water/` subdir, not root of `PI_LOG_DIR`.

---

## Verification
1. Drop a sample `moisture_log.csv` and one test image into `data/` to verify before Pi sync
2. `make up` — confirm both containers start cleanly
3. `curl http://localhost:8000/health` → `{"status":"ok"}`
4. `curl http://localhost:8000/moisture/latest` → JSON rows
5. Open `http://localhost:8501` → dashboard renders with chart and image
6. Wait 60s → page auto-refreshes
