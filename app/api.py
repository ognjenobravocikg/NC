from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.stats import get_user_stats, get_map_stats, get_player_stats
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import SessionLocal
import os

app = FastAPI(
    title="Golf Rival Data API",
    description="Data Engineering Challenge API",
    version="1.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#------ NECESSARY ENDPOINTS ------ Landing page, user stats, map stats

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("app/static/index.html")

@app.get("/user-stats")
def user_stats(
    countries: Optional[List[str]] = Query(None),
    oss: Optional[List[str]] = Query(None)
):
    return get_user_stats(countries=countries, oss=oss)

@app.get("/map-stats/{map_name}")
def map_stats(
    map_name: str,
    date_from: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    data = get_map_stats(
        map_name,
        start_date=date_from,
        end_date=date_to
    )
    if data is None:
        raise HTTPException(status_code=404, detail=f"Map '{map_name}' not found")
    return data

#------ BONUS ENDPOINTS ------ Player stats, charts, health check
@app.get("/player-stats/{username}")
def player_stats(username: str):
    data = get_player_stats(username)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")
    return data

@app.get("/chart")
def get_chart():
    file_path = os.path.join("app", "static", "chart.html")
    return FileResponse(file_path)

@app.get("/health")
def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
