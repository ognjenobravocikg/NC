# Data Engineering Challenge

**Author:** Ognjen Obradović — ognjenobradovickg@gmail.com

Challenge provided by Nordeus. The dataset and full challenge description can be found at:
[nordeus.com/nordeus-challenge/data-engineering](https://nordeus.com/nordeus-challenge/data-engineering/)

## A Brief Overview

This project has a job of taking jsonl files provided, parsing, cleaning and storing them in a SQLite database. After that API endpoints are provided, as well as profile section where you can search for players, get their match history, best maps etc.

---

## Tech Stack

| Layer         | Technology              |
| ------------- | ----------------------- |
| Language      | Python 3.10             |
| API Framework | FastAPI + Uvicorn       |
| ORM           | SQLAlchemy              |
| Database      | SQLite                  |
| Frontend      | HTML / CSS / JavaScript |
| Charting      | Chart.js                |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ognjenobravocikg/NC.git
cd NC
```

The project file system should like the following:

```
NC/
│
├── app/
│   ├── api.py
│   ├── stats.py
│   ├── database.py
│   ├── models.py
│   ├── loader.py
│   ├── parser.py
│   └── static/
│       ├── index.html
│       ├── chart.html
│       └── profile.html
│
├── data/
│   ├── events.jsonl
│   └── maps.jsonl
│
├── main.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 2. Run the project

### OPTION A Run with Docker (I highly recommend)

Make sure Docker is installed and running and you are located in the project directory. Build and start the application via:

```bash
docker-compose up --build
```

Access the application at http://localhost:8000/.

---

### OPTION B Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Load data into the database (skip if you ran with Docker)

```bash
python main.py
```

This runs the full parsing and loading pipeline. It will parse `events.jsonl` and `maps.jsonl`, validate and clean records, and populate a local SQLite database at `nord_challenge.db`. Duplicate and malformed records are handled automatically.

You can inspect the database using [DB Browser for SQLite](https://sqlitebrowser.org/).

### 4. Start the API server (skip if you ran with Docker)

```bash
uvicorn app.api:app --reload
```

The API will be available at http://localhost:8000/. Opening that in your browser will take you to the landing page.

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

> **Another note on `best_player_username`:** The best_player_username can also be a guest or a player which registered before the data recording began, so I made a design decision while cleaning the data to keep those matches in the final SQLite DB. In these cases "Unknow user with ID ..." will be given as a result.

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

### `GET /matches/{date}`

Returns every reconstructed match that finished on the given date, across all maps.

**Path parameter:**

| Parameter | Format       | Description                   |
| --------- | ------------ | ----------------------------- |
| `date`    | `YYYY-MM-DD` | The date to fetch matches for |

**Response fields:**

| Field              | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `datetime_utc`     | Full UTC timestamp of when the match ended (YYYY-MM-DD HH:MM:SS)                     |
| `map`              | Map name the match was played on                                                     |
| `player`           | Username of the first player                                                         |
| `opponent`         | Username of the second player                                                        |
| `outcome`          | Match outcome from the first player's perspective: 1.0 = win, 0.0 = loss, 0.5 = draw |
| `duration_seconds` | Match duration in seconds                                                            |

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

## Bonus Features

### Session detection without `state` column

Sessions are reconstructed purely from ping timestamps. Two consecutive pings with a gap greater than 120 seconds are treated as belonging to different sessions. Session duration is `last_ping - first_ping` within each group. This approach is fully equivalent to using the `state` column but requires no dependency on it.

### Interactive chart

This interactive chart is designed as a way to help Data Analyst down the road track the popularity of the game and or certain maps so he can make informed and precise descisions to game designers and descision makers. A Chart.js chart showing match counts per day for each map. Selecting a date — either via the sidebar buttons or by clicking directly on a chart point — updates two panels simultaneously:

- **Left panel** — per-map match count and average playtime for that day
- **Right panel** — full match log for that day showing both player usernames, map (color-coded to match the chart line), UTC datetime, and match duration

### Player profile search (`/profile`)

Since we already did one feature for the employee-side I find that designing a player profile search is a good idea, since it shows what the data parsed, cleaned and analysed can be used for from a player perspective. A search page where you can look up any player by username. Displays a profile card, four stat summary cards, a per-map win rate breakdown with progress bars and a W/D/L record bar, and a full match history table with opponent, result badge, and duration. This feature can be implemented in two ways, "Profile" and "Search other Player" tabs in the video-game, it can be paired with a sent friend request for example in the second use case scenario.

### OpenAPI documentation

All endpoints include `response_model`, `description`, `summary`, and `tags` so the auto-generated docs at `/docs` are fully self-documenting. Error responses (`404`, `422`, `503`) are documented per route.

---

## Notes

- All timestamps in the database are stored as UTC Unix timestamps. Date strings in API responses are formatted in UTC.
- The database file (`nord_challenge.db`) must be generated by running `main.py` before the API server is started.
- The API uses FastAPI's automatic OpenAPI documentation, accessible at `http://127.0.0.1:8000/docs` once the server is running.
