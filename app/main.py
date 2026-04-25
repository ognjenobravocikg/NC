from database import engine
from models import Base
from parser import parse_events

Base.metadata.create_all(bind=engine)

rows = parse_events("data/events.jsonl")
print(len(rows))