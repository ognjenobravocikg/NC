from sqlalchemy import func
from app.database import SessionLocal
from app.models import User, MatchEvent, SessionPing, Map
from datetime import date, datetime, UTC
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
                "registration_os": user.registration_os,
                "favorite_map": favorite_map_name,
                "favorite_map_win_ratio": round(favorite_ratio, 3),
                "total_playtime_seconds": total_playtime,
                "total_win_ratio": total_win_ratio,
                "average_matches_per_session": avg_matches_per_session,
                "registration_date": date.fromtimestamp(user.registration_timestamp)
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
            print(f"[MAP NOT FOUND] map_name={map_name}")
            return []

        map_id = game_map.map_id
        print(f"[MAP FOUND] map_name={map_name} map_id={map_id}")

        # ---------------------------------
        # 2. LOAD EVENTS (ORDERED)
        # ---------------------------------
        events = db.query(MatchEvent).filter(
            MatchEvent.map_id == map_id
        ).order_by(MatchEvent.timestamp).all()

        print(f"[EVENTS LOADED] total_events={len(events)}")

        # ---------------------------------
        # 3. MATCH START STORAGE
        # ---------------------------------
        starts = defaultdict(list)

        # ---------------------------------
        # 4. COLLECT ALL FINISHED MATCHES
        # ---------------------------------
        all_matches = []

        processed_matches = set()

        for event in events:

            players = tuple(sorted([event.user_id, event.opponent_id]))
            key = (players, event.map_id)

            if event.event_type == "match_start":
                starts[key].append(event.timestamp)
                print(f"[START] players={players} map={event.map_id} time={event.timestamp}")

            elif event.event_type == "match_finish":

                match_instance_key = (players, event.map_id, event.timestamp)

                if match_instance_key in processed_matches:
                    print(f"[SKIP DUPLICATE FINISH] players={players} time={event.timestamp}")
                    continue

                if key not in starts or not starts[key]:
                    print(f"[SKIP NO START] players={players} time={event.timestamp} — no matching start found")
                    continue

                start_time = starts[key].pop(0)
                duration = event.timestamp - start_time

                processed_matches.add(match_instance_key)

                date_str = datetime.utcfromtimestamp(
                    event.timestamp
                ).strftime("%Y-%m-%d")

                opponent_outcome = (
                    1.0 - event.outcome if event.outcome in [0, 1] else 0.5
                )

                print(f"[FINISH] players={players} date={date_str}")
                print(f"         start={start_time} finish={event.timestamp} duration={duration}s")
                print(f"         user_id={event.user_id} outcome={event.outcome} | opponent_id={event.opponent_id} opp_outcome={opponent_outcome}")

                all_matches.append((
                    date_str, duration,
                    event.user_id, event.outcome,
                    event.opponent_id, opponent_outcome
                ))

        print(f"\n[ALL MATCHES COLLECTED] total_matches={len(all_matches)}")

        # ---------------------------------
        # 5. GET SORTED UNIQUE DATES
        # ---------------------------------
        all_dates = sorted(set(m[0] for m in all_matches))
        print(f"[ALL DATES] {all_dates}")

        # ---------------------------------
        # 6. BUILD DAILY STATS + CUMULATIVE WIN RATIOS
        # ---------------------------------
        results = []

        cumulative_wins = defaultdict(float)
        cumulative_matches = defaultdict(int)

        daily_durations = defaultdict(list)
        daily_outcomes = defaultdict(lambda: defaultdict(list))

        for date_str, duration, user_id, outcome, opponent_id, opp_outcome in all_matches:
            daily_durations[date_str].append(duration)
            daily_outcomes[date_str][user_id].append(outcome)
            daily_outcomes[date_str][opponent_id].append(opp_outcome)

        for date_str in all_dates:

            print(f"\n[PROCESSING DATE] {date_str}")

            # Update cumulative stats
            for user_id, outcomes in daily_outcomes[date_str].items():
                prev_wins = cumulative_wins[user_id]
                prev_matches = cumulative_matches[user_id]

                cumulative_wins[user_id] += sum(outcomes)
                cumulative_matches[user_id] += len(outcomes)

                print(f"  [CUMULATIVE UPDATE] user_id={user_id}")
                print(f"    wins: {prev_wins} → {cumulative_wins[user_id]}")
                print(f"    matches: {prev_matches} → {cumulative_matches[user_id]}")
                print(f"    win_ratio: {round(cumulative_wins[user_id] / cumulative_matches[user_id], 4)}")

            # Apply date window filter AFTER updating cumulative stats
            if start_date and date_str < start_date:
                print(f"  [SKIP DATE] {date_str} < start_date={start_date} (cumulative still updated)")
                continue
            if end_date and date_str > end_date:
                print(f"  [SKIP DATE] {date_str} > end_date={end_date} (cumulative still updated)")
                continue

            durations = daily_durations[date_str]
            match_count = len(durations)
            avg_playtime = round(sum(durations) / match_count, 2) if match_count > 0 else 0

            print(f"  [DAILY STATS] match_count={match_count} avg_playtime={avg_playtime}s")
            print(f"  [DURATIONS] {durations}")

            # Best player calculation
            best_user_id = None
            best_ratio = -1

            print(f"  [WIN RATIO SNAPSHOT] (cumulative up to {date_str})")
            for user_id, total_matches in cumulative_matches.items():
                ratio = cumulative_wins[user_id] / total_matches
                print(f"    user_id={user_id} wins={cumulative_wins[user_id]} matches={total_matches} ratio={round(ratio, 4)}")
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_user_id = user_id

            print(f"  [BEST PLAYER] user_id={best_user_id} ratio={round(best_ratio, 4)}")

            best_username = None
            if best_user_id:
                user = db.query(User).filter(
                    User.user_id == best_user_id
                ).first()
                if user:
                    best_username = user.username
                    print(f"  [BEST PLAYER USERNAME] {best_username}")
                else:
                    print(f"  [BEST PLAYER USERNAME] NOT FOUND for user_id={best_user_id}")

            results.append({
                "date": date_str,
                "avg_playtime": avg_playtime,
                "best_player_username": best_username,
                "match_cnt": match_count
            })

        # ---------------------------------
        # 7. SORT BY DATE DESCENDING
        # ---------------------------------
        results.sort(key=lambda x: x["date"], reverse=True)

        print(f"\n[FINAL RESULTS] total_rows={len(results)}")
        for r in results:
            print(f"  {r}")

        return results

    finally:
        db.close()