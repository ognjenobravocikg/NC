from fastapi import FastAPI, Query
from typing import List, Optional
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.stats import get_user_stats, get_map_stats
from fastapi.middleware.cors import CORSMiddleware
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

# ---------------------------------
# USER STATS
# ---------------------------------
@app.get("/user-stats")
def user_stats(
    countries: Optional[List[str]] = Query(None),
    oss: Optional[List[str]] = Query(None)
):
    return get_user_stats(countries=countries, oss=oss)

# ---------------------------------
# LANDING PAGE
# ---------------------------------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("app/static/index.html")


# ---------------------------------
# CHART
# ---------------------------------
@app.get("/chart")
def get_chart():
    file_path = os.path.join("app", "static", "chart.html")
    return FileResponse(file_path)


# ---------------------------------
# MAP STATS
# ---------------------------------
@app.get("/map-stats/{map_name}")
def map_stats(
    map_name: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    return get_map_stats(
        map_name,
        start_date=date_from,
        end_date=date_to
    )