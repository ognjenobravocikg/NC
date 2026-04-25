import json

file_path = "data/events.jsonl"

wanted_types = {
    "registration",
    "session_ping",
    "match_start",
    "match_finish"
}

counts = {
    "registration": 0,
    "session_ping": 0,
    "match_start": 0,
    "match_finish": 0
}

with open(file_path, "r", encoding="utf-8") as file:

    for line in file:

        row = json.loads(line)

        event_type = row.get("event_type")

        if event_type in wanted_types and counts[event_type] < 3:

            print("\n======================")
            print(event_type.upper())
            print(row)

            counts[event_type] += 1

        if all(count >= 3 for count in counts.values()):
            break