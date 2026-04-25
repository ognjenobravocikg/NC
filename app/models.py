from sqlalchemy import Column, Integer, String, Float
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    country = Column(String, nullable=False)
    registration_os = Column(String, nullable=False)
    registration_timestamp = Column(Integer, nullable=False)


class SessionPing(Base):
    __tablename__ = "session_pings"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)
    state = Column(String, nullable=False)
    device_os = Column(String, nullable=False)


class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True)


    user_id = Column(String, nullable=False) 
    opponent_id = Column(String, nullable = False)
    map_id = Column(String, nullable = False)
    timestamp = Column(Integer, nullable = False)
    outcome = Column(Float, nullable = False)


class Map(Base):
    __tablename__ = "maps"

    map_id = Column(String, primary_key=True)
    map_name = Column(String, nullable=False, unique=True)