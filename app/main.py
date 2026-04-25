from database import engine
from models import Base
from parser import parse_events
from loader import load_all


def main():
    Base.metadata.create_all(bind=engine)

    clean_data = parse_events("data/events.jsonl")

    load_all(
        clean_data=clean_data,
        maps_filepath="data/maps.jsonl"
    )


if __name__ == "__main__":
    main()