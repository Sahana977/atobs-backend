# ATOBS Backend

Backend for **ATOBS: AI-Based Traffic Optimization and Bus Occupancy Prediction System Using CatBoost** (ICSCSA-2026).

Python + FastAPI + scikit-learn / XGBoost / CatBoost + SQLite. No external services, no ORM — just plain functions and plain SQL.

## Quick start

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m app.ml.train                 # generates data if missing, trains 3 models, saves the best
python -m scripts.seed_db              # fills the database with a sample Marathahalli network
uvicorn app.api.main:app --reload      # API at http://127.0.0.1:8000  (Swagger UI at /docs)
pytest -q                              # ~340 tests
```

Seeded logins: `admin@atobs.dev / admin12345`, `commuter1@atobs.dev / commuter1pass`.

## How the code is organised

Every table follows the same four simple layers, so once you understand one, you understand all of them:

```
model        app/models/<name>.py          table definition + dataclass
repository   app/repositories/<name>_repo.py   plain SQL: create / get / list / update / delete
service      app/services/<name>_service.py    validation, reference checks, uniqueness
router       app/api/routers/<name>.py         HTTP endpoints (+ schemas in app/api/schemas/)
```

Tables: depots, stops, routes, route_stops, buses, trips, traffic_readings, occupancy_readings, alerts, users, feedback.

```
app/
  config.py                 settings + model hyperparameters from the paper
  database.py               SQLite connection, init/reset
  errors.py                 NotFound / Validation / Conflict / Auth errors
  ml/                       data generation, preprocessing, 3 models, training, predictor
  routing/graph.py          24-node / 41-edge graph, fastest vs comfort-aware Dijkstra
  services/
    auth_service.py         register, login, bearer tokens (PBKDF2 password hashing)
    analytics_service.py    dashboard reports
    prediction_service.py   occupancy prediction for every stop of a stored trip
  api/main.py               FastAPI app, error handling, router registration
scripts/
  seed_db.py                sample data
  export_training_data.py   turn stored readings into a training CSV
tests/                      one test file per table + auth, analytics, ML, routing
```

## Endpoints

Every table (`/depots`, `/stops`, `/routes`, `/route-stops`, `/buses`, `/trips`, `/traffic-readings`, `/occupancy-readings`, `/alerts`, `/users`, `/feedback`) has:

| Method | Path | What it does |
|---|---|---|
| GET | `/x` | list with filters, text search (`q`), paging, sorting |
| GET | `/x/count` | count with the same filters |
| GET | `/x/export.csv` | CSV download |
| GET | `/x/{id}` | get one |
| POST | `/x` | create |
| POST | `/x/bulk` | create many (all-or-nothing) |
| PATCH | `/x/{id}` | update some fields |
| DELETE | `/x/{id}` | delete |

Plus:

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | status + loaded model |
| GET | `/models/metrics` | 6-metric comparison of RF / XGBoost / CatBoost |
| POST | `/predict/occupancy` | occupancy % + comfort label for one trip/stop/time |
| POST | `/predict/occupancy/batch` | up to 500 at once |
| POST | `/predict/trip/{trip_id}` | predicted occupancy at every stop of a stored trip |
| POST | `/route` | fastest route vs comfort route, per-leg occupancy |
| GET | `/network/graph` | road graph |
| GET | `/analytics/dashboard` | fleet, busiest stops, occupancy by hour, traffic, feedback, alerts |
| GET | `/analytics/...` | each dashboard section on its own |
| POST | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/change-password`; GET `/auth/me` | accounts |
| GET | `/history` | log of recent predictions |

Example:

```bash
curl -X POST localhost:8000/predict/occupancy -H "Content-Type: application/json" \
  -d '{"trip_id":"T012","stop_id":"S05","travel_time":"2026-10-01T09:15:00","traffic_level":"high","delay_min":4}'

curl -X POST localhost:8000/route -H "Content-Type: application/json" \
  -d '{"origin":"Marathahalli Bridge","destination":"Whitefield","traffic_level":"high","comfort_weight":0.5}'
```

## Using real BMTC data

Put a CSV at `data/bmtc_raw.csv` with these columns, then re-run `python -m app.ml.train`:

`trip_id, stop_id, minute_of_day, is_peak_hour, traffic_level (low/medium/high/severe), vehicle_density, avg_speed, road_occupancy, traffic_flow, delay_min, occupancy_pct`

Or record readings through the API and run `python -m scripts.export_training_data data/bmtc_raw.csv`.

## Notes

- The bundled training data and seed data are **synthetic**, so your metrics will be close to but not identical to the paper's table.
- The model with the lowest RMSE is saved automatically.
- Route cost = `travel_minutes + comfort_weight × max(0, occupancy − 50)`. `comfort_weight = 0` gives the plain fastest route.
