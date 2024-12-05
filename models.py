from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True,)
    username = Column(String, unique=True, index=True,)
    password = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    client_secret = Column(String)
    client_id = Column(String)

    need_google_token = Column(Boolean, default=True)
    last_interaction = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )
    is_active = Column(Boolean, default=False)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    user_text = Column(Text)
    gpt_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    audio_id = Column(Integer, nullable=True)
    is_proactive = Column(
        Boolean, default=False
    )  # Новое поле для различия типов сообщений
