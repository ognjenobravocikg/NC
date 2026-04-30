from fastapi import FastAPI, Query
from typing import List, Optional
from stats import get_user_stats, get_map_stats

app = FastAPI(
    title="Golf Rival Data API",
    description="Data Engineering Challenge API",
    version="1.0"
)

# ---------------------------------
# USER STATS
# ---------------------------------
@app.get("/user-stats")
def user_stats(
    countries: Optional[List[str]] = Query(None),
    oss: Optional[List[str]] = Query(None)
):
    data = get_user_stats()

    # Optional filtering (bonus)
    if countries:
        data = [u for u in data if u["country"] in countries]

    if oss:
        # NOTE: you didn’t store OS per user separately,
        # so skip or extend model later if needed
        pass

    return data


# ---------------------------------
# MAP STATS
# ---------------------------------
@app.get("/map-stats/{map_name}")
def map_stats(
    map_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    data = get_map_stats(
        map_name,
        start_date=start_date,
        end_date=end_date
    )

    return data