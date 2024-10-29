from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
)
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    user_text = Column(Text)
    gpt_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    audio_id = Column(Integer)
