from sqlalchemy import func
from database import SessionLocal
from models import User, MatchEvent, SessionPing, Map
from datetime import datetime
from collections import defaultdict

def get_user_stats():

    db = SessionLocal()

    try:
        users = db.query(User).all()

        # ---------------------------------
        # 1. LOAD ALL MATCH EVENTS ONCE
        # ---------------------------------
        events = db.query(MatchEvent).order_by(
            MatchEvent.timestamp
        ).all()

        # ---------------------------------
        # 2. RECONSTRUCT MATCHES
        # ---------------------------------
        starts = defaultdict(list)

        # user_id → list of (map_id, outcome)
        user_matches = defaultdict(list)

        for event in events:

            players = tuple(sorted([event.user_id, event.opponent_id]))
            key = (players, event.map_id)

            if event.event_type == "match_start":
                starts[key].append(event.timestamp)

            elif event.event_type == "match_finish":

                if key not in starts or not starts[key]:
                    continue

                start_time = starts[key].pop(0)

                # assign outcome ONLY to current user
                user_matches[event.user_id].append(
                    (event.map_id, event.outcome)
                )

        # ---------------------------------
        # 3. LOAD MAPS (for names)
        # ---------------------------------
        maps = {
            m.map_id: m.map_name
            for m in db.query(Map).all()
        }

        results = []

        # ---------------------------------
        # 4. PER USER CALCULATIONS
        # ---------------------------------
        for user in users:

            matches = user_matches.get(user.user_id, [])
            total_matches = len(matches)

            # -----------------------------
            # TOTAL WIN RATIO
            # -----------------------------
            if total_matches > 0:
                total_points = sum(outcome for _, outcome in matches)
                total_win_ratio = round(
                    total_points / total_matches, 3
                )
            else:
                total_win_ratio = 0

            # -----------------------------
            # FAVORITE MAP
            # -----------------------------
            map_groups = defaultdict(list)

            for map_id, outcome in matches:
                map_groups[map_id].append(outcome)

            favorite_map_id = None
            favorite_ratio = -1

            for map_id, outcomes in map_groups.items():

                ratio = sum(outcomes) / len(outcomes)

                if ratio > favorite_ratio:
                    favorite_ratio = ratio
                    favorite_map_id = map_id

            favorite_map_name = (
                maps.get(favorite_map_id)
                if favorite_map_id else None
            )

            if favorite_ratio == -1:
                favorite_ratio = 0

            # -----------------------------
            # SESSION PLAYTIME
            # -----------------------------
            pings = db.query(SessionPing).filter(
                SessionPing.user_id == user.user_id
            ).order_by(SessionPing.timestamp).all()

            total_playtime = 0
            session_count = 0
            current_start = None

            for ping in pings:

                if ping.state == "started":
                    current_start = ping.timestamp

                elif ping.state == "ended" and current_start:
                    total_playtime += (
                        ping.timestamp - current_start
                    )
                    session_count += 1
                    current_start = None

            # -----------------------------
            # AVG MATCHES PER SESSION
            # -----------------------------
            if session_count > 0:
                avg_matches_per_session = round(
                    total_matches / session_count, 3
                )
            else:
                avg_matches_per_session = 0

            # -----------------------------
            # FINAL RESULT
            # -----------------------------
            results.append({
                "username": user.username,
                "country": user.country,
                "favorite_map": favorite_map_name,
                "favorite_map_win_ratio": round(favorite_ratio, 3),
                "total_playtime_seconds": total_playtime,
                "total_win_ratio": total_win_ratio,
                "average_matches_per_session": avg_matches_per_session,
                "registration_date": user.registration_timestamp
            })

        # ---------------------------------
        # SORT RESULTS
        # ---------------------------------
        results.sort(
            key=lambda x: x["total_win_ratio"],
            reverse=True
        )

        return results

    finally:
        db.close()

def get_map_stats(map_name, start_date=None, end_date=None):

    db = SessionLocal()

    try:
        # ---------------------------------
        # 1. MAP NAME → MAP ID
        # ---------------------------------
        game_map = db.query(Map).filter(
            Map.map_name == map_name
        ).first()

        if not game_map:
            return []

        map_id = game_map.map_id

        # ---------------------------------
        # 2. LOAD EVENTS (ORDERED)
        # ---------------------------------
        events = db.query(MatchEvent).filter(
            MatchEvent.map_id == map_id
        ).order_by(MatchEvent.timestamp).all()

        # ---------------------------------
        # 3. MATCH START STORAGE
        # key = (players, map)
        # value = list of start timestamps
        # ---------------------------------
        starts = defaultdict(list)

        # ---------------------------------
        # 4. DAILY AGGREGATION STRUCTURE
        # ---------------------------------
        daily = {}

        # ---------------------------------
        # 5. PROCESS EVENTS
        # ---------------------------------
        for event in events:

            players = tuple(sorted([event.user_id, event.opponent_id]))
            key = (players, event.map_id)

            if event.event_type == "match_start":
                starts[key].append(event.timestamp)

            elif event.event_type == "match_finish":

                if key not in starts or not starts[key]:
                    continue  # no matching start → skip

                start_time = starts[key].pop(0)

                duration = event.timestamp - start_time

                date_str = datetime.utcfromtimestamp(
                    event.timestamp
                ).strftime("%Y-%m-%d")

                # date filter
                if start_date and date_str < start_date:
                    continue

                if end_date and date_str > end_date:
                    continue

                if date_str not in daily:
                    daily[date_str] = {
                        "durations": [],
                        "scores": defaultdict(list)
                    }

                # store duration
                daily[date_str]["durations"].append(duration)

                # store outcome for best player calc
                daily[date_str]["scores"][event.user_id].append(
                    event.outcome
                )

        results = []

        # ---------------------------------
        # 6. BUILD FINAL OUTPUT
        # ---------------------------------
        for date_str, data in daily.items():

            durations = data["durations"]
            scores = data["scores"]

            match_count = len(durations)

            avg_playtime = (
                round(sum(durations) / match_count, 2)
                if match_count > 0 else 0
            )

            # BEST PLAYER
            best_user_id = None
            best_ratio = -1

            for user_id, outcomes in scores.items():

                ratio = sum(outcomes) / len(outcomes)

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_user_id = user_id

            best_username = None

            if best_user_id:
                user = db.query(User).filter(
                    User.user_id == best_user_id
                ).first()

                if user:
                    best_username = user.username

            results.append({
                "date": date_str,
                "average_playtime_seconds": avg_playtime,
                "best_player_username": best_username,
                "match_count": match_count
            })

        # ---------------------------------
        # 7. SORT BY DATE
        # ---------------------------------
        results.sort(key=lambda x: x["date"])

        return results

    finally:
        db.close()