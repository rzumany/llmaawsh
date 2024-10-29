import streamlit as st
import requests
from io import BytesIO
from audio_recorder_streamlit import audio_recorder
import time
import base64


API_URL = "http://localhost:8000"


def login(username, password):
    response = requests.post(
        f"{API_URL}/token", data={"username": username, "password": password}
    )
    return response.json()


def register(username, password):
    data = {"username": username, "password": password}
    response = requests.post(
        f"{API_URL}/register/",
        json=data,
    )
    return response.json()


def get_messages():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    response = requests.get(
        f"{API_URL}/get_chat_messages/",
        headers=headers,
    )
    return response.json()


st.title("Voice Chat with AI")


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )


if "access_token" not in st.session_state:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        result = register(username, password)
        st.success(result.get("msg"))

    if st.button("Login"):
        result = login(username, password)
        access_token = result.get("access_token")
        if access_token:
            st.session_state["access_token"] = access_token
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")

if "access_token" in st.session_state:
    messages = get_messages()

    if "len_messages" not in st.session_state:
        st.session_state["len_messages"] = len(messages)

    if st.session_state["len_messages"] != len(messages):
        with st.spinner("Waiting"):
            time.sleep(1)
            st.rerun()

    for message in range(len(messages)):
        st.audio(f"./audio_query/{messages[message]['audio_id']}.wav")
        if message == len(messages) - 1:
            autoplay_audio(
                f"./audio_responses/{messages[message]['audio_id']}.mp3"
            )
        else:
            st.audio(f"./audio_responses/{messages[message]['audio_id']}.mp3")

    # st.write(messages)
    audio_bytes = None
    audio_bytes = audio_recorder(
        text="Lets talk with AI",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="user",
        icon_size="6x",
        pause_threshold=2.2,
        key=f"audio_recorder_{len(messages)}",
        # energy_threshold=(-1.0, 1.0),
    )
    if "audio_bytes" not in st.session_state:
        st.session_state["audio_bytes"] = ""

    if audio_bytes and audio_bytes != st.session_state["audio_bytes"]:
        st.session_state["len_messages"] += 1
        st.session_state["audio_bytes"] = audio_bytes
        st.audio(audio_bytes, format="audio/wav")

        audio_file = BytesIO(audio_bytes)
        # audio_bytes = None
        audio_file.name = "recorded_audio.wav"
        print(audio_file)

        headers = {
            "Authorization": f"Bearer {st.session_state['access_token']}"
        }
        files = {"file": (audio_file.name, audio_file, "audio/wav")}
        response = requests.post(
            f"{API_URL}/process_audio/", headers=headers, files=files
        )
        st.rerun()
        # if response.status_code == 200:
        #     audio_data = response.content
        #     st.audio(audio_data, format="audio/mpeg")
        #     audio_bytes = None
        #     st.rerun()
        # else:
        #     st.error("Error processing audio on server.")
