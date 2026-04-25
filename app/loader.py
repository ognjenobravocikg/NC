import json

from database import SessionLocal
from models import User, SessionPing, MatchEvent, Map


def load_users(registrations, db):
    """
    Insert registration rows into users table.
    """

    for row in registrations:
        data = row["event_data"]

        user = User(
            user_id=row["user_id"],
            username=data["username"],
            country=data["country"],
            registration_os=data["device_os"],
            registration_timestamp=row["timestamp"]
        )

        db.merge(user)


def load_session_pings(session_pings, db):
    """
    Insert session ping rows.
    """

    for row in session_pings:
        data = row["event_data"]

        ping = SessionPing(
            id=row["id"],
            user_id=row["user_id"],
            timestamp=row["timestamp"],
            state=data["state"],
            device_os=data["device_os"]
        )

        db.merge(ping)


def load_match_events(match_rows, db):
    """
    Insert match_start and match_finish rows.
    """

    for row in match_rows:

        if row["event_type"] != "match_finish":
            continue

        data = row["event_data"]

        match = MatchEvent(
            id=row["id"],
            user_id=row["user_id"],
            opponent_id=data["opponent_id"],
            map_id=data["map_id"],
            timestamp=row["timestamp"],
            outcome=data.get("outcome")
        )

        db.merge(match)


def load_maps(filepath, db):

    with open(filepath, "r", encoding="utf-8") as file:

        for line in file:
            row = json.loads(line)

            game_map = Map(
                map_id=row["id"],
                map_name=row["name"]
            )

            db.merge(game_map)


def load_all(clean_data, maps_filepath):
    db = SessionLocal()

    try:
        load_users(clean_data["registrations"], db)

        load_session_pings(clean_data["session_pings"], db)

        all_matches = (
            clean_data["match_starts"] +
            clean_data["match_finishes"]
        )

        load_match_events(all_matches, db)

        load_maps(maps_filepath, db)

        db.commit()

        print("Database successfully populated.")

    except Exception as error:
        db.rollback()
        print("Loading failed:", error)

    finally:
        db.close()