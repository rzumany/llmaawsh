from sqlalchemy.orm import Session
from models import User, Message
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str):
    hashed_password = pwd_context.hash(password)
    db_user = User(username=username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not pwd_context.verify(password, user.password):
        return None
    return user


def create_message(
    db: Session,
    user_id: int,
    user_text: str,
    gpt_response: str,
    audio_id,
):
    message = Message(
        user_id=user_id,
        user_text=user_text,
        gpt_response=gpt_response,
        audio_id=audio_id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, token):
    return db.query(Message).filter(Message.user_id == token.id).all()


def get_all_messages(db: Session):
    return db.query(Message).all()
