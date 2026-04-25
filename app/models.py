# Defining database

from sqlalchemy import Column, String, Integer
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key = True)
    username = Column(String)
    country = Column(String)
    device_os = Column(String)
    registration_date = Column(Integer)