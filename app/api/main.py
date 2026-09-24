"""
ATOBS REST API.

Run:  uvicorn app.api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import database
from app.api.routers import analytics, auth, predictions
from app.api.routers.crud import CRUD_ROUTERS
from app.errors import AppError, ValidationError
from app.ml import predictor


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="ATOBS API",
    description="AI-Based Traffic Optimization and Bus Occupancy Prediction System (CatBoost)",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError):
    body = {"detail": exc.message}
    if isinstance(exc, ValidationError):
        body["errors"] = exc.errors
    return JSONResponse(status_code=exc.status_code, content=body)


@app.get("/health", tags=["System"])
def health():
    try:
        name = predictor.load()["name"]
    except FileNotFoundError:
        name = None
    return {"status": "ok", "model_loaded": name is not None, "model": name}


app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(analytics.router)
for crud_router in CRUD_ROUTERS:
    app.include_router(crud_router)
