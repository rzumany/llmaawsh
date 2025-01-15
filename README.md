# Personal Time Manager Project

We are excited to introduce the Personal Time Manager project, which includes the following features:

* Google Calendar API Integration: Seamlessly connect and sync with your Google Calendar.
* Task Management: Easily add and remove tasks.
* Task Prioritization: Organize tasks by priority for better time management.
* Deadline Notifications: Receive timely reminders about upcoming deadlines.
* Natural Language Queries: Get information using natural language requests, such as "When is my next meeting?" or "What do I have scheduled for Thursday?"

Our project will also enable voice commands to add tasks to the calendar. It will provide friendly reminders about potential events that the LLM thinks could be added or that the user might have forgotten. Additionally, there will be functionality for the model to independently create a daily plan, suggesting an optimal schedule for the day.

## About

Technologies: Python, Whisper, TTS, ChatGPT, LLaMA.

Prerequisites: `credentials.json` from the Gcloud OAuth2 app!

## Howto

Init venv: `virtualenv .vemv && source .venv/bin/activate`

Run backend: `uvicorn main:app --reload`

Monkey patch frontend: `cp ./app_static_file_handler.py .venv/lib/python3.12/site-packages/streamlit/web/server/app_static_file_handler.py`

Run frontend: `streamlit run streamlit_frontend.py`
