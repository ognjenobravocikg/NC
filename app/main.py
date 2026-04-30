from database import engine
from models import Base
from parser import parse_events
from loader import load_all
from stats import get_user_stats, get_map_stats


def main():

    Base.metadata.create_all(bind=engine)

    clean_data = parse_events("data/events.jsonl")

    load_all(
        clean_data=clean_data,
        maps_filepath="data/maps.jsonl"
    )

    users = get_user_stats()
    for row in users:
        print(row)

    maps = get_map_stats("Lake")
    for row in maps:
        print(row)

if __name__ == "__main__":
    main()