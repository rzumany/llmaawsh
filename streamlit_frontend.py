from io import BytesIO
import time
import base64
import base64
import re
from urllib.parse import urlparse, parse_qs

import streamlit as st
from streamlit_cookies_controller import CookieController
from streamlit_js_eval import streamlit_js_eval

import requests

import traceback

# from tvdmcomp import tvdmcomp

API_URL = "http://localhost:8000"

st.set_page_config("LLM agent", layout="wide")


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
    headers = {
        "Authorization": f"Bearer {controller.get('cookies_name_access_token')}"
    }
    response = requests.get(
        f"{API_URL}/get_chat_messages/",
        headers=headers,
    )
    return response.json()


def get_user_info_by_token():
    headers = {
        "Authorization": f"Bearer {controller.get('cookies_name_access_token')}"
    }
    response = requests.get(
        f"{API_URL}/get_user_info/",
        headers=headers,
    )
    return response.json()


def set_google_token(google_token):
    headers = {
        "Authorization": f"Bearer {controller.get('cookies_name_access_token')}"
    }
    data = {"google_token": google_token}
    response = requests.post(
        f"{API_URL}/set_google_token/", headers=headers, json=data
    )
    return response.json()


def check_google_token():
    headers = {
        "Authorization": f"Bearer {controller.get('cookies_name_access_token')}"
    }
    response = requests.post(
        f"{API_URL}/check_google_token/",
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


def has_query_parameters(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params


controller = CookieController()

cookies = controller.getAll()

col_1, col_2, col_3 = st.columns(3)

if "cookies_name_access_token" not in controller.getAll():
    with col_2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            result = register(username, password)
            st.success(result.get("msg"))

        if st.button("Login"):
            result = login(username, password)
            access_token = result.get("access_token")
            if access_token:
                controller.set("cookies_name_access_token", access_token)
                controller.refresh()
                st.success("Logged in!")
            else:
                st.error("Invalid credentials")

# st.write(st.session_state)

try:
    if "cookies_name_access_token" in controller.getAll():
        with col_1:
            if st.button("Dislogin"):
                controller.remove("cookies_name_access_token")
                controller.refresh()
        with col_2:
            user = get_user_info_by_token()
            st.subheader(user["username"])

            res = check_google_token()

            if user["need_google_token"]:
                google_token = st.text_input("Google token")
                st.write("Please go to this URL:")
                st.write(res["message"])
                query_params = st.query_params
                if "code" in query_params:
                    try:
                        set_google_token(query_params["code"])
                        st.rerun()
                    except:
                        pass
            else:
                messages = get_messages()
                written_messages = [
                    {
                        "user_text": message["user_text"],
                        "gpt_response": message["gpt_response"],
                        "is_proactive": message["is_proactive"],
                    }
                    for message in messages
                ]
                # st.write(written_messages)

                if "len_messages" not in st.session_state:
                    st.session_state["len_messages"] = len(messages)

                if st.session_state["len_messages"] != len(messages):
                    with st.spinner("Waiting"):
                        time.sleep(1)

                for message in range(len(messages)):
                    try:
                        st.audio(
                            f"./audio_query/{messages[message]['audio_id']}.wav"
                        )
                    except:
                        pass
                    if message == len(messages) - 1:
                        try:
                            autoplay_audio(
                                f"./audio_responses/{messages[message]['audio_id']}.mp3"
                            )
                        except Exception as e:
                            print(e)
                    else:
                        try:
                            st.audio(
                                f"./audio_responses/{messages[message]['audio_id']}.mp3"
                            )
                        except Exception as e:
                            print(e)

                from tvdmcomp import tvdmcomp

                audio_bytes = tvdmcomp(my_input_value="Input")
                try:
                    base64_data = re.search(r"base64,(.*)", audio_bytes).group(
                        1
                    )
                    audio_bytes = base64.b64decode(base64_data)
                except:
                    pass
                    # st.write(f"Error decoding base64: {e}")

                if "cookies_name_audio_bytes" not in st.session_state:
                    st.session_state["cookies_name_audio_bytes"] = ""

                if (
                    audio_bytes
                    and audio_bytes
                    != st.session_state["cookies_name_audio_bytes"]
                ):

                    st.session_state["len_messages"] += 1
                    st.session_state["cookies_name_audio_bytes"] = audio_bytes

                    st.audio(audio_bytes, format="audio/wav")

                    audio_file = BytesIO(audio_bytes)
                    audio_file.name = "recorded_audio.wav"
                    print(audio_file)

                    headers = {
                        "Authorization": f"Bearer {controller.get('cookies_name_access_token')}"
                    }
                    files = {
                        "file": (audio_file.name, audio_file, "audio/wav")
                    }

                    response = requests.post(
                        f"{API_URL}/process_audio/",
                        headers=headers,
                        files=files,
                    )
                    # time.sleep(7)
                    streamlit_js_eval(
                        js_expressions="parent.window.location.reload()"
                    )


except:
    st.write(traceback.format_exc())
    if "st.rerun()" in traceback.format_exc():
        st.rerun()
    # else:
    #     del st.session_state["access_token"]
    #     controller.remove('access_token')
