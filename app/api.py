from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from typing import List, Optional
from app.stats import get_user_stats, get_map_stats, get_player_stats
from app.database import SessionLocal
from datetime import date
import os

class UserStatEntry(BaseModel):
    username: str 
    country: Optional[str] 
    fav_map: Optional[str] 
    fav_map_win_ratio: float 
    total_playtime: int 
    total_win_ratio: float 
    avg_matches_per_session: float 
    registration_date: date


class MapStatEntry(BaseModel):
    date: str 
    match_cnt: int 
    avg_playtime: float 
    best_player_username: Optional[str] 


class MatchHistoryEntry(BaseModel):
    date: str 
    map: str 
    opponent: str
    outcome: float 
    duration_seconds: int 


class PlayerStatEntry(BaseModel):
    username: str 
    country: Optional[str]
    registration_date: str
    total_matches: int  
    total_win_ratio: float  
    best_map: Optional[str] 
    best_map_ratio: float 
    match_history: List[MatchHistoryEntry] 


class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok' if the database is reachable")

app = FastAPI(
    title="Data Engineering Challenge API",
    description=
    """
## Nordeus Data Engineering Challenge API, project by Ognjen Obradović
"""
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

@app.get(
        "/user-stats",
        tags = ["Demanded Endpoint"], 
        description = """
Returns one entry per player containing their overall win ratio, favorite map,
total playtime, and session statistics.

Results are ordered by `total_playtime` descending.
    """,
    response_model=List[UserStatEntry],
    response_description="List of player stat entries ordered by total playtime descending"
)

def user_stats(
    countries: Optional[List[str]] = Query(None, description = "Filter by three-letter coded country"),
    oss: Optional[List[str]] = Query(None, description = "iOS and/or Android")
):
    return get_user_stats(countries=countries, oss=oss)

@app.get(
        "/map-stats/{map_name}",
        tags = ["Demanded Endpoint"],
        description = """
Returns one entry per day on which at least one match was completed on the given map,
within the optional date range.

**`best_player_username`** is computed cumulatively - it is the player with the highest
win ratio on this map across all matches from the beginning of the dataset up to and
including that date.

Important note: if the user has the best win ratio on a map, but doesn't appear in the dataset and/or registered before the data you provided, he will BE INCLUDE but without his username instead only his user_id will appear.

    """,
    response_model=List[MapStatEntry],
    response_description="List of daily map stat entries ordered by date descending",
    responses={
        404: {"description": "Map not found"},
        422: {"description": "Invalid date format - must be YYYY-MM-DD"}
    }
        )

def map_stats(
    map_name: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
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
@app.get(
    "/player-stats/{username}",
    tags=["Bonus"],
    description="""
Returns aggregated stats and a complete match history for a single player looked up by username.

**Match history** is ordered by date descending and includes the map, opponent username,
outcome (1.0 = win, 0.5 = draw, 0.0 = loss), and duration for every match.

Returns `404` if the username does not exist in the database.
    """,
    response_model=PlayerStatEntry,
    response_description="Player profile with stats and full match history",
    responses={
        404: {"description": "Player not found"}
    }
)
def player_stats(username: str):
    data = get_player_stats(username)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")
    return data


@app.get(
        "/chart",
        tags = ["Bonus"])
def get_chart():
    file_path = os.path.join("app", "static", "chart.html")
    return FileResponse(file_path)

@app.get(
    "/health",
    tags=["Bonus"],
    summary="Health check",
    description="Verifies that the API is running and the database is reachable. Returns `503` if the database connection fails.",
    response_model=HealthResponse,
    response_description="Database connectivity status",
    responses={
        503: {"description": "Database unavailable"}
    }
)
def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")