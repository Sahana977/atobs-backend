"""REST endpoints for feedback  ->  /feedback"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.feedback import FeedbackCreate, FeedbackOut, FeedbackPage, FeedbackUpdate
from app.services import feedback_service as service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _filters(
    user_id: Optional[int] = None,
    trip_id: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    min_comfort_rating: Optional[int] = None,
    max_comfort_rating: Optional[int] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "user_id": user_id,
        "trip_id": trip_id,
        "min_rating": min_rating,
        "max_rating": max_rating,
        "min_comfort_rating": min_comfort_rating,
        "max_comfort_rating": max_comfort_rating,
        "category": category,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=FeedbackPage, summary="List feedback")
def list_feedbacks(
    user_id: Optional[int] = Query(None, description="exact user_id"),
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    min_rating: Optional[int] = Query(None, description="minimum rating"),
    max_rating: Optional[int] = Query(None, description="maximum rating"),
    min_comfort_rating: Optional[int] = Query(None, description="minimum comfort_rating"),
    max_comfort_rating: Optional[int] = Query(None, description="maximum comfort_rating"),
    category: Optional[str] = Query(None, description="exact category"),
    q: Optional[str] = Query(None, description="text search in comment"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(user_id=user_id, trip_id=trip_id, min_rating=min_rating, max_rating=max_rating, min_comfort_rating=min_comfort_rating, max_comfort_rating=max_comfort_rating, category=category, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count feedback")
def count_feedbacks(
    user_id: Optional[int] = Query(None, description="exact user_id"),
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    min_rating: Optional[int] = Query(None, description="minimum rating"),
    max_rating: Optional[int] = Query(None, description="maximum rating"),
    min_comfort_rating: Optional[int] = Query(None, description="minimum comfort_rating"),
    max_comfort_rating: Optional[int] = Query(None, description="maximum comfort_rating"),
    category: Optional[str] = Query(None, description="exact category"),
    q: Optional[str] = Query(None, description="text search in comment"),
):
    return {"count": service.count(_filters(user_id=user_id, trip_id=trip_id, min_rating=min_rating, max_rating=max_rating, min_comfort_rating=min_comfort_rating, max_comfort_rating=max_comfort_rating, category=category, q=q))}


@router.get("/export.csv", summary="Download feedback as CSV")
def export_feedbacks(
    user_id: Optional[int] = Query(None, description="exact user_id"),
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    min_rating: Optional[int] = Query(None, description="minimum rating"),
    max_rating: Optional[int] = Query(None, description="maximum rating"),
    min_comfort_rating: Optional[int] = Query(None, description="minimum comfort_rating"),
    max_comfort_rating: Optional[int] = Query(None, description="maximum comfort_rating"),
    category: Optional[str] = Query(None, description="exact category"),
    q: Optional[str] = Query(None, description="text search in comment"),
):
    csv_text = service.export_csv(_filters(user_id=user_id, trip_id=trip_id, min_rating=min_rating, max_rating=max_rating, min_comfort_rating=min_comfort_rating, max_comfort_rating=max_comfort_rating, category=category, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback.csv"},
    )


@router.get("/{item_id}", response_model=FeedbackOut, summary="Get one")
def get_feedback(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=FeedbackOut, status_code=201, summary="Create")
def create_feedback(payload: FeedbackCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[FeedbackOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_feedbacks(payload: list[FeedbackCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=FeedbackOut, summary="Update some fields")
def update_feedback(item_id: int, payload: FeedbackUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_feedback(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
