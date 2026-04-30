# Nordeus Data Engineering Challenge

Project by Ognjen Obradovic

This project processes raw gameplay event data (from JSONL files) and exposes insights through a RestAPI.

## Approach

We can divide the solution into 4 main stages:

1. ----- PARSING AND CLEANING THE DATA -----
   In this stage I created a simple ETL that: - Reads JSONL input - Removes either invalid or duplicate events - Applies rules per event type

2. ----- DATA STORAGE -----
   This is where the Loading part of the ETL happens. For this project I used SQLite and SQLAlchemy ORM. We store normalized tables for: - users - session_pings - match_events - maps

3. ----- DATA PROCESSING -----
   Logic for the APIs, handling statistics about maps and events. - Reconstructing matches from match_start and match_finish events - Calculating durations, win ratios and aggregates

4. ----- API LAYER -----
   Providing endpoints for testing and viewing the data. Built using FastAPI.

## DATA

Here we explain what we store in the database as well as explaining for some data columns.

### Users

- id
- username
- country
- device_os
- registration_timestamps

### Session Pings

- user_id
- timestamp (later used for calculating time spent in the application)
- state

### Match Events

- id
- event_type (either match_start or match_finish)
- user_id
- opponent_id
- map_id
- timestamp
- outcome (can be NULL value for the match_start event type)

### Maps

- map_id
- map_name

## Key Design Decisions

- **Single-pass parsing**
  Input file is processed only once, then persisted.

- **Event deduplication**
  Duplicate events are removed using a business-level key.

- **Match reconstruction**
  Matches are reconstructed by pairing match_start and match_finish events using:
  - unordered player pairs
  - map_id
  - chronological ordering

- **Accurate playtime calculation**
  Map playtime is computed using match durations instead of session pings.

- **Session tracking**
  Uses session_ping start/end events to calculate total playtime.

## API Endpoints

### GET /user-stats

Returns player statistics.

Optional filters:

- countries
- oss

---

### GET /map-stats/{map_name}

Returns daily statistics for a map.

Optional query params:

- start_date (YYYY-MM-DD)
- end_date (YYYY-MM-DD)
