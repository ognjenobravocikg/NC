# parser.py

import json


VALID_OS = {"iOS", "Android"}
VALID_STATES = {"started", "in_progress", "ended"}
VALID_OUTCOMES = {0.0, 0.5, 1.0, 0, 1}


def validate_common(row):
    """
    Checks fields required by every event type.
    """

    if not isinstance(row, dict):
        return False

    if "id" not in row or "timestamp" not in row or "event_type" not in row or "user_id" not in row or "event_data" not in row:
        return False

    if not isinstance(row["event_data"], dict):
        return False

    if row["timestamp"] <= 0:
        return False

    return True


def validate_registration(row):
    """
    registration event validation
    """

    data = row["event_data"]

    username = data.get("username")
    country = data.get("country")
    device_os = data.get("device_os")

    if not username or not country or device_os not in VALID_OS:
        return False

    if len(country) != 3:
        return False

    return True


def validate_session_ping(row):
    """
    session_ping validation
    """

    data = row["event_data"]

    state = data.get("state")
    device_os = data.get("device_os")

    if state not in VALID_STATES:
        return False

    if device_os not in VALID_OS:
        return False

    return True


def validate_match_start(row):
    """
    match_start validation
    """

    data = row["event_data"]

    map_id = data.get("map_id")
    opponent_id = data.get("opponent_id")

    if not map_id or not opponent_id:
        return False

    if opponent_id == row["user_id"]:
        return False

    return True


def validate_match_finish(row):
    """
    match_finish validation
    """

    data = row["event_data"]

    if not validate_match_start(row):
        return False

    outcome = data.get("outcome")

    if outcome not in VALID_OUTCOMES:
        return False

    return True


def is_valid_event(row):
    """
    Routes validation based on event type.
    """

    if not validate_common(row):
        return False

    event_type = row["event_type"]

    if event_type == "registration":
        return validate_registration(row)

    elif event_type == "session_ping":
        return validate_session_ping(row)

    elif event_type == "match_start":
        return validate_match_start(row)

    elif event_type == "match_finish":
        return validate_match_finish(row)

    return False


def get_dedup_key(row):
    """
    Duplicate key.
    Uses business meaning, not raw row id.
    """

    event_type = row["event_type"]
    user_id = row["user_id"]
    timestamp = row["timestamp"]
    data = row["event_data"]

    if event_type == "registration":
        return (
            event_type,
            user_id
        )

    elif event_type == "session_ping":
        return (
            event_type,
            user_id,
            timestamp,
            data.get("state")
        )

    elif event_type == "match_start":
        return (
            event_type,
            user_id,
            data.get("opponent_id"),
            data.get("map_id"),
            timestamp
        )

    elif event_type == "match_finish":
        return (
            event_type,
            user_id,
            data.get("opponent_id"),
            data.get("map_id"),
            timestamp,
            data.get("outcome")
        )

    return ("unknown", row["id"])


def parse_events(filepath):

    seen = {}

    raw_rows = 0
    malformed_rows = 0
    invalid_rows = 0

    with open(filepath, "r", encoding="utf-8") as file:

        for line in file:

            raw_rows += 1

            try:
                row = json.loads(line)

            except json.JSONDecodeError:
                malformed_rows += 1
                continue

            if not is_valid_event(row):
                invalid_rows += 1
                continue

            key = (row["event_type"], row["id"])

            if key not in seen:
                seen[key] = row

            else:
                old_row = seen[key]

                if row["timestamp"] < old_row["timestamp"]:
                    seen[key] = row

    registrations = []
    session_pings = []
    match_starts = []
    match_finishes = []

    for row in seen.values():

        event_type = row["event_type"]

        if event_type == "registration":
            registrations.append(row)

        elif event_type == "session_ping":
            session_pings.append(row)

        elif event_type == "match_start":
            match_starts.append(row)

        elif event_type == "match_finish":
            match_finishes.append(row)

    clean_rows = len(seen)
    duplicate_rows = raw_rows - malformed_rows - invalid_rows - clean_rows

    print("\n========== PARSER REPORT ==========")
    print("Raw rows read:        ", raw_rows)
    print("Malformed rows:      ", malformed_rows)
    print("Invalid rows:        ", invalid_rows)
    print("Duplicate rows:      ", duplicate_rows)
    print("Clean rows kept:     ", clean_rows)

    print("\nEvent buckets:")
    print("Registrations:       ", len(registrations))
    print("Session pings:       ", len(session_pings))
    print("Match starts:        ", len(match_starts))
    print("Match finishes:      ", len(match_finishes))
    print("===================================\n")

    return {
        "registrations": registrations,
        "session_pings": session_pings,
        "match_starts": match_starts,
        "match_finishes": match_finishes
    }