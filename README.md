# Nordeus Data Engineering Challenge

**Author:** Ognjen Obradović — ognjenobradovickg@gmail.com

Challenge provided by Nordeus. The dataset and full challenge description can be found at:
[nordeus.com/nordeus-challenge/data-engineering](https://nordeus.com/nordeus-challenge/data-engineering/)

---

## Overview

This project implements a full data engineering pipeline on top of raw game event data from _Golf Rival_. It covers ingestion and parsing of raw `.jsonl` event logs, structured storage in a SQLite database, statistical computation over match and session data, and exposure of results through a REST API with a lightweight frontend.

---

## Tech Stack

| Layer         | Technology              |
| ------------- | ----------------------- |
| Language      | Python 3.10+            |
| API Framework | FastAPI + Uvicorn       |
| ORM           | SQLAlchemy              |
| Database      | SQLite                  |
| Frontend      | HTML / CSS / JavaScript |
| Charting      | Chart.js                |

---

## Project Structure

```
project/
│
├── app/
│   ├── api.py          # FastAPI routes and request validation
│   ├── stats.py        # Core statistical computation logic
│   ├── database.py     # SQLAlchemy session and engine setup
│   ├── models.py       # ORM models (User, MatchEvent, SessionPing, Map)
│   ├── loader.py       # Database insertion logic
│   ├── parser.py       # Raw .jsonl parsing and validation
│   └── static/
│       ├── index.html  # Landing page
│       ├── chart.html  # Match count line chart (bonus)
│       └── profile.html # Player profile search page (bonus)
│
├── data/
│   ├── events.jsonl    # Raw game event log
│   └── maps.jsonl      # Map metadata
│
├── main.py             # Entry point for data loading
└── requirements.txt
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ognjenobravocikg/NC.git
cd NC
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Load data into the database

```bash
python main.py
```

This runs the full parsing and loading pipeline. It will parse `events.jsonl` and `maps.jsonl`, validate and clean records, and populate a local SQLite database at `nord_challenge.db`. Duplicate and malformed records are handled automatically.

You can inspect the database using [DB Browser for SQLite](https://sqlitebrowser.org/).

### 4. Start the API server

```bash
uvicorn app.api:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Opening that in your browser will take you to the landing page.

---

## API Endpoints

### `GET /user-stats`

Returns aggregated statistics for all players, ordered by total playtime descending.

**Optional query parameters:**

| Parameter   | Type        | Description                                                                 |
| ----------- | ----------- | --------------------------------------------------------------------------- |
| `countries` | `list[str]` | Filter results to specific country codes                                    |
| `oss`       | `list[str]` | Filter session-based stats to sessions played on specific operating systems |

> **Note on OS filtering:** The `oss` filter applies only to session-derived statistics (`total_playtime`, `avg_matches_per_session`). Win ratio and favorite map are always computed globally across all matches, regardless of OS. This distinction reflects the challenge spec: a user's match performance is not tied to the device they played on.

**Response fields:**

| Field                     | Description                                    |
| ------------------------- | ---------------------------------------------- |
| `username`                | Player username                                |
| `country`                 | Player country code                            |
| `fav_map`                 | Map with the highest win ratio for this player |
| `fav_map_win_ratio`       | Win ratio on their favorite map                |
| `total_playtime`          | Total seconds spent in active game sessions    |
| `total_win_ratio`         | Overall win ratio across all matches           |
| `avg_matches_per_session` | Average number of matches played per session   |
| `registration_date`       | Date the player registered                     |

---

### `GET /map-stats/{map_name}`

Returns daily statistics for a given map, ordered by date descending.

**Optional query parameters:**

| Parameter   | Format       | Description                     |
| ----------- | ------------ | ------------------------------- |
| `date_from` | `YYYY-MM-DD` | Start of date range (inclusive) |
| `date_to`   | `YYYY-MM-DD` | End of date range (inclusive)   |

Both parameters are validated server-side — malformed dates return a `422` error.

**Response fields:**

| Field                  | Description                                                                            |
| ---------------------- | -------------------------------------------------------------------------------------- |
| `date`                 | The date this row covers                                                               |
| `match_cnt`            | Number of matches completed on this map on this date                                   |
| `avg_playtime`         | Average match duration in seconds on this date                                         |
| `best_player_username` | Player with the highest cumulative win ratio on this map up to and including this date |

> **Note on `best_player_username`:** This is computed cumulatively — it reflects the player with the best win ratio across all their matches on this map from the beginning of the dataset up to the given date, not just on that single day. Date filtering is applied only to the output rows; the cumulative win ratio always incorporates full historical data.

---

### `GET /player-stats/{username}`

Returns full profile and match history for a single player. Returns `404` if the username does not exist.

**Response fields:**

| Field               | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `username`          | Player username                                                     |
| `country`           | Country code                                                        |
| `registration_date` | Registration date                                                   |
| `total_matches`     | Total matches played                                                |
| `total_win_ratio`   | Overall win ratio                                                   |
| `best_map`          | Map with the highest win ratio                                      |
| `best_map_ratio`    | Win ratio on best map                                               |
| `match_history`     | List of all matches with date, map, opponent, outcome, and duration |

---

### `GET /health`

Returns `{ "status": "ok" }` if the database is reachable, or `503` if not. Useful for deployment health checks.

---

## Data Processing

### Parsing (`parser.py`)

The parser reads raw `.jsonl` files line by line and performs the following:

- Validates that all required fields are present and correctly typed for each event type
- Discards malformed or incomplete records
- Deduplicates events using business keys (player pair + map + timestamp)

### Loading (`loader.py`)

The loader takes the cleaned event stream and:

- Inserts records into the appropriate SQLite tables via SQLAlchemy
- Skips records with conflicting primary keys, keeping the earliest occurrence
- Normalizes match events into a flat `MatchEvents` table shared across all queries

---

## Statistical Design Decisions

### Match reconstruction

Matches are reconstructed by pairing `match_start` and `match_finish` events. Player pairs are always sorted before keying, so mirrored events (where the same two players appear with swapped `user_id`/`opponent_id`) are correctly deduplicated and only produce one match record.

### Opponent outcome tracking

Every `match_finish` event records the outcome for `user_id`. The opponent's outcome is derived as `1.0 - outcome` for wins/losses and `0.5` for draws. Both players are always credited, so a player's statistics are correct regardless of whether they appeared as `user_id` or `opponent_id` in the raw data.

### Session detection without `state` column (Bonus)

Sessions are reconstructed purely from ping timestamps. Consecutive pings with a gap of 120 seconds or less belong to the same session. When a gap exceeds 120 seconds, the current session is closed and a new one begins. Session duration is recorded as `last_ping_timestamp - first_ping_timestamp` within each group.

---

## Frontend (Bonus)

The frontend is served as static HTML from FastAPI and requires no separate build step.

### `/` — Landing page

Navigation hub linking to the chart and player profile pages.

### `/chart` — Match Count Chart

Fetches live data from `/map-stats` for all maps and renders a multi-line Chart.js chart showing match counts per day across the full dataset range. A sidebar panel lets you click any date to see a per-map breakdown table for that day, including average match duration. Clicking directly on a chart point also triggers the panel.

### `/profile` — Player Profile Search

Search for any player by username. Displays a profile card with country and registration date, four stat summary cards (total matches, win ratio, best map, best map win ratio), and a full paginated match history table with opponent, result badge (Win / Loss / Draw), and match duration.

---

## Notes

- All timestamps in the database are stored as UTC Unix timestamps. Date strings in API responses are formatted in UTC.
- The database file (`nord_challenge.db`) must be generated by running `main.py` before the API server is started.
- The API uses FastAPI's automatic OpenAPI documentation, accessible at `http://127.0.0.1:8000/docs` once the server is running.
