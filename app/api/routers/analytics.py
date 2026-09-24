"""Reports for dashboards — all read-only."""
from typing import Optional

from fastapi import APIRouter, Query

from app.services import analytics_service as analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard():
    return analytics.dashboard()


@router.get("/occupancy-by-hour")
def occupancy_by_hour(route_id: Optional[int] = Query(None, ge=1)):
    return analytics.occupancy_by_hour(route_id)


@router.get("/busiest-stops")
def busiest_stops(limit: int = Query(10, ge=1, le=100)):
    return analytics.busiest_stops(limit)


@router.get("/route-performance")
def route_performance():
    return analytics.route_performance()


@router.get("/traffic")
def traffic():
    return analytics.traffic_summary()


@router.get("/fleet")
def fleet():
    return analytics.fleet_summary()


@router.get("/feedback")
def feedback():
    return analytics.feedback_summary()


@router.get("/alerts/active")
def active_alerts():
    return analytics.active_alerts()
