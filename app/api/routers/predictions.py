"""ML endpoints: occupancy prediction, trip prediction, comfort-aware routing, model metrics."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.prediction import (BatchOccupancyRequest, OccupancyRequest, OccupancyResponse,
                                        RouteRequest, TripPredictionRequest)
from app.errors import NotFoundError, ValidationError
from app.ml import predictor
from app.routing import graph
from app.services import prediction_log_service as prediction_log
from app.services import prediction_service

router = APIRouter(tags=["Predictions & Routing"])


def _model_or_503() -> dict:
    try:
        return predictor.load()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))


def _predict_one(req: OccupancyRequest) -> OccupancyResponse:
    bundle = _model_or_503()
    row = predictor.build_row(
        req.trip_id, req.stop_id, req.travel_time, req.traffic_level, req.delay_min,
        vehicle_density=req.vehicle_density, avg_speed=req.avg_speed,
        road_occupancy=req.road_occupancy, traffic_flow=req.traffic_flow,
    )
    occ = predictor.predict_rows([row])[0]
    return OccupancyResponse(
        trip_id=req.trip_id, stop_id=req.stop_id, predicted_occupancy_pct=occ,
        comfort=predictor.comfort_label(occ), is_peak_hour=bool(row["is_peak_hour"]),
        model=bundle["name"],
    )


@router.get("/models/metrics")
def model_metrics():
    m = predictor.metrics()
    if not m:
        raise NotFoundError("No metrics yet. Run: python -m app.ml.train")
    return m


@router.post("/predict/occupancy", response_model=OccupancyResponse)
def predict_occupancy(req: OccupancyRequest):
    res = _predict_one(req)
    prediction_log.log("occupancy", req.model_dump(), res.model_dump())
    return res


@router.post("/predict/occupancy/batch", response_model=list[OccupancyResponse])
def predict_occupancy_batch(req: BatchOccupancyRequest):
    return [_predict_one(item) for item in req.items]


@router.post("/predict/trip/{trip_id}")
def predict_trip(trip_id: int, req: Optional[TripPredictionRequest] = None):
    _model_or_503()
    req = req or TripPredictionRequest()
    result = prediction_service.predict_for_trip(trip_id, req.traffic_level, req.delay_min)
    prediction_log.log("trip", {"trip_id": trip_id, **req.model_dump()},
                       {k: v for k, v in result.items() if k != "stops"})
    return result


@router.get("/network/graph")
def road_graph():
    return graph.graph_info()


@router.get("/network/stops")
def network_stops():
    return graph.graph_info()["nodes"]


@router.post("/route")
def route(req: RouteRequest):
    _model_or_503()

    def occupancy_fn(pairs):
        rows = [predictor.build_row(trip, stop, req.travel_time, req.traffic_level) for trip, stop in pairs]
        return predictor.predict_rows(rows)

    try:
        result = graph.plan_route(req.origin, req.destination, req.traffic_level,
                                  occupancy_fn, beta=req.comfort_weight)
    except KeyError as e:
        raise NotFoundError(str(e).strip("'"))
    except ValueError as e:
        raise ValidationError({"route": str(e)})

    prediction_log.log("route", req.model_dump(),
                       {k: v for k, v in result.items() if k not in ("fastest_route", "comfort_route")})
    return result


@router.get("/history")
def history(limit: int = Query(20, ge=1, le=200), kind: Optional[str] = None):
    return prediction_log.recent(limit, kind)
