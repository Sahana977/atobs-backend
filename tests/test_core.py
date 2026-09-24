"""ML + routing tests. Model-dependent tests are skipped until you run: python -m app.ml.train"""
from datetime import datetime

import pytest

from app.ml import data_gen, predictor
from app.ml.preprocess import clean
from app.routing import graph


def test_data_and_cleaning():
    raw = data_gen.generate(n_rows=2000)
    df = clean(raw)
    assert len(df) < len(raw)                      # missing rows dropped
    assert df[["time_sin", "time_cos"]].notna().all().all()


def test_graph_shape():
    info = graph.graph_info()
    assert info["node_count"] == 24 and info["edge_count"] == 41


def test_routing_with_fake_model():
    # Pretend every stop is 90% full except Brookefield (S07), which is empty
    fake = lambda pairs: [5.0 if s == "S07" else 90.0 for _, s in pairs]
    r = graph.plan_route("Marathahalli Bridge", "Whitefield", "medium", fake, beta=0.5)
    assert r["fastest_route"]["stops"][0] == "Marathahalli Bridge"
    assert r["comfort_route"]["stops"][-1] == "Whitefield"
    assert r["comfort_route"]["avg_occupancy_pct"] <= r["fastest_route"]["avg_occupancy_pct"]


@pytest.mark.skipif(not predictor.BEST_MODEL_PATH.exists(), reason="model not trained")
def test_prediction_range():
    row = predictor.build_row("T001", "S05", datetime(2026, 1, 5, 9, 0), "high", 4)
    occ = predictor.predict_rows([row])[0]
    assert 0 <= occ <= 150


@pytest.mark.skipif(not predictor.BEST_MODEL_PATH.exists(), reason="model not trained")
def test_api_endpoints():
    from fastapi.testclient import TestClient
    from app.api.main import app

    client = TestClient(app)
    assert client.get("/health").json()["model_loaded"] is True
    r = client.post("/predict/occupancy", json={"trip_id": "T010", "stop_id": "S03",
                                                "traffic_level": "high"})
    assert r.status_code == 200 and "comfort" in r.json()
    assert client.get("/network/graph").json()["edge_count"] == 41
    r = client.post("/route", json={"origin": "KR Puram", "destination": "Bellandur"})
    assert r.status_code == 200 and r.json()["comfort_route"]["legs"]
    assert client.post("/route", json={"origin": "Nowhere", "destination": "HAL"}).status_code == 404


@pytest.mark.skipif(not predictor.BEST_MODEL_PATH.exists(), reason="model not trained")
def test_predict_for_stored_trip(monkeypatch):
    from app import config
    from app.services import prediction_service
    from scripts import seed_db

    monkeypatch.setattr(config, "PASSWORD_ITERATIONS", 1_000)
    seed_db.main()
    result = prediction_service.predict_for_trip(1, "high", 3)
    assert result["stops"]
    assert [s["sequence"] for s in result["stops"]] == sorted(s["sequence"] for s in result["stops"])
    assert all(0 <= s["predicted_occupancy_pct"] <= 150 for s in result["stops"])


@pytest.mark.skipif(not predictor.BEST_MODEL_PATH.exists(), reason="model not trained")
def test_crud_and_auth_over_http(monkeypatch):
    from fastapi.testclient import TestClient
    from app import config
    from app.api.main import app

    monkeypatch.setattr(config, "PASSWORD_ITERATIONS", 1_000)
    client = TestClient(app)
    r = client.post("/depots", json={"depot_code": "D1", "name": "Test Depot"})
    assert r.status_code == 201
    depot_id = r.json()["id"]
    assert client.get(f"/depots/{depot_id}").json()["name"] == "Test Depot"
    assert client.post("/depots", json={"depot_code": "D1", "name": "Dup"}).status_code == 409
    assert client.patch(f"/depots/{depot_id}", json={"capacity": 50}).json()["capacity"] == 50
    assert client.get("/depots/count").json()["count"] == 1
    assert client.get("/depots/export.csv").text.startswith("id,")
    assert client.delete(f"/depots/{depot_id}").status_code == 204
    assert client.get(f"/depots/{depot_id}").status_code == 404

    client.post("/auth/register", json={"email": "x@example.com", "full_name": "X", "password": "secret123"})
    token = client.post("/auth/login", json={"email": "x@example.com", "password": "secret123"}).json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["email"] == "x@example.com"
    assert client.get("/auth/me").status_code == 401
