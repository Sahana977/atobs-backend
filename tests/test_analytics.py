"""Analytics on top of the seeded sample network."""
import pytest

from app import config
from app.services import analytics_service as analytics
from scripts import seed_db


@pytest.fixture(autouse=True)
def seeded(monkeypatch):
    monkeypatch.setattr(config, "PASSWORD_ITERATIONS", 1_000)
    seed_db.main()


def test_occupancy_by_hour_has_peak_above_midday():
    by_hour = {r["hour"]: r["avg_occupancy_pct"] for r in analytics.occupancy_by_hour()}
    assert by_hour[9] > by_hour[13]


def test_occupancy_by_hour_for_one_route():
    rows = analytics.occupancy_by_hour(route_id=1)
    assert rows and all("comfort" in r for r in rows)


def test_busiest_stops_sorted():
    rows = analytics.busiest_stops(5)
    values = [r["avg_occupancy_pct"] for r in rows]
    assert len(rows) == 5 and values == sorted(values, reverse=True)


def test_route_performance_covers_all_routes():
    assert len(analytics.route_performance()) == len(seed_db.ROUTE_PLANS)


def test_fleet_summary():
    fleet = analytics.fleet_summary()
    assert fleet["buses_total"] == 40
    assert 0 < fleet["buses_operational"] <= 40


def test_feedback_summary():
    summary = analytics.feedback_summary()
    assert summary["total"] == 40
    assert 1 <= summary["avg_rating"] <= 5


def test_active_alerts_critical_first():
    alerts = analytics.active_alerts()
    assert alerts[0]["severity"] == "critical"


def test_training_rows_match_csv_columns():
    rows = analytics.training_rows()
    assert rows
    for column in ["trip_id", "stop_id", "minute_of_day", "is_peak_hour", "occupancy_pct"]:
        assert column in rows[0]


def test_dashboard_has_all_sections():
    board = analytics.dashboard()
    assert set(board) == {"fleet", "busiest_stops", "occupancy_by_hour", "traffic", "feedback", "active_alerts"}
