from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from openai import OpenAI
import os
from dotenv import load_dotenv
from database import get_db, engine
from models import Base, User
from crud import (
    create_user,
    authenticate_user,
    create_message,
    get_user_by_username,
    get_messages,
    get_all_messages,
)
from io import BytesIO
from passlib.context import CryptContext

import traceback
import json

from google_functions import (
    check_token_for_valid,
    set_google_token_,
    return_service,
    list_events,
    add_event,
    delete_event,
    edit_event,
    show_event,
)


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

api_key_openai = os.getenv("OPENAI_API_KEY")

from llm_prompts import full_system_string

system_string = full_system_string


def get_openai_client(api_key=api_key_openai):
    client = OpenAI(
        api_key=api_key,
    )
    return client


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: timedelta = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=180)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
            )
        user = get_user_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )


# Регистрация пользователя
@app.post("/register/")
async def register(
    request: Request,
    db: Session = Depends(get_db),
):
    # try:
    json_body = await request.json()
    if not json_body:
        raise HTTPException(
            status_code=400,
            detail="No JSON body provided",
        )
    username = json_body.get("username")
    password = json_body.get("password")
    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password must be provided",
        )
    db_user = get_user_by_username(db, username)
    if db_user:
        # raise HTTPException(
        #     status_code=400,
        #     detail="Username already registered",
        # )
        return {"msg": "Username already registered"}
    create_user(db, username, password)
    return {"msg": "User registered successfully"}
    # except:
    #     print(traceback.format_exc())


# Авторизация пользователя
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/get_chat_messages/")
async def get_chat_messages(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    messages = get_messages(db, token)
    return messages


@app.post("/process_audio/")
async def process_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    audio_id = len(get_all_messages(db))
    file_location = f"./audio_query/{audio_id}.wav"

    audio_content = await file.read()

    with open(file_location, "wb+") as file_object:
        file_object.write(audio_content)
    print(file)

    client = get_openai_client()

    audio_file = BytesIO(audio_content)
    audio_file.name = file.filename

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    print(transcription)
    transcription_text = transcription.text

    old_messages = get_messages(db, token)

    time_definition = datetime.now()

    convo = [
        {
            "role": "system",
            "content": system_string.replace(
                "<time definition>", str(time_definition)
            ),
        }
    ]

    for message in old_messages:
        if message.user_text:
            convo.append({"role": "user", "content": message.user_text})
        if message.gpt_response:
            convo.append(
                {"role": "assistant", "content": message.gpt_response}
            )
    convo.append({"role": "user", "content": transcription_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=convo,
    )
    gpt_response = response.choices[0].message.content.strip("`").strip("json")
    gpt_response_json = json.loads(gpt_response)
    gpt_text = gpt_response_json["text"]
    gpt_function = gpt_response_json["function"]
    gpt_helper_function = gpt_response_json["helper_function"]
    print(gpt_response)
    print(gpt_text)
    print(gpt_function)

    if gpt_text:
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=gpt_text,
        )

    audio_path = f"./audio_responses/{audio_id}.mp3"

    audio_response.stream_to_file(audio_path)

    create_message(db, token.id, transcription_text, gpt_response, audio_id)

    while gpt_function:
        service = return_service(db, token)
        print(service)
        result = eval(gpt_function)
        print(result)
        if gpt_helper_function:
            convo.append(
                {
                    "role": "user",
                    "content": "Requested Information: " + str(result),
                }
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=convo,
            )
            gpt_response = (
                response.choices[0].message.content.strip("`").strip("json")
            )
            gpt_response_json = json.loads(gpt_response)
            gpt_text = gpt_response_json["text"]
            gpt_function = gpt_response_json["function"]
            gpt_helper_function = gpt_response_json["helper_function"]
            print(gpt_response)
            print(gpt_text)
            print(gpt_function)
            audio_id = len(get_all_messages(db))
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input=gpt_text,
            )
            audio_path = f"./audio_responses/{audio_id}.mp3"

            audio_response.stream_to_file(audio_path)
            create_message(
                db,
                token.id,
                "Requested Information: " + str(result),
                gpt_response,
                audio_id,
            )

    return FileResponse(audio_path, media_type="audio/mpeg")


@app.get("/get_user_info/")
async def get_user_info(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    print(token)
    # user = get_user_by_username(db, username)
    if token:
        return token


@app.post("/check_google_token/")
async def check_google_token(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    # user = get_user_by_username(db, username)
    res = check_token_for_valid(db, token)
    return res


@app.post("/set_google_token/")
async def set_google_token(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
    request: Request = None,
):
    json_body = await request.json()
    google_token = json_body["google_token"]
    set_google_token_(db, token, google_token)


# def set_user_token


# def init_google_calendar():
