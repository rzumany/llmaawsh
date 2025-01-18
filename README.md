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

Monkey patch frontend:  
venv: `cp ./app_static_file_handler.py .venv/lib/python3.12/site-packages/streamlit/web/server/app_static_file_handler.py`  
or
conda: 'cp ./app_static_file_handler.py ~/conda/envs/llm_agents/lib/python3.9/site-packages/streamlit/web/server/app_static_file_handler.py'

Run frontend: `streamlit run streamlit_frontend.py`

## WIP
**В текущий момент запуск сервиса доступен только для developer'ов продуктов в связи с отсутствием публикации проекта в подтвержденных google сервисах.**

Поэтому локально можно запустить только имея файл credentials.json, который можно сгенерировать в вашем собственном аккаунте Gcloud OAuth2 app. 

Для экспорта файла credentials.json для OAuth-сервисов Google выполните следующие шаги:

- Перейдите в Google Cloud Console: Откройте Google Cloud Console и войдите в систему с помощью своей учетной записи Google.

- Перейдите в раздел Учетные данные: В Google Cloud Console перейдите в раздел APIs & Services > Credentials.

- Создайте или выберите проект: Если у вас еще нет проекта, создайте новый проект или выберите существующий.

- Создайте OAuth Client ID: Нажмите на Create credentials и выберите OAuth client ID.

- Настройте OAuth Client ID: Выберите тип приложения (например, веб-приложение, Android, iOS) и настройте необходимые параметры.

- Загрузите учетные данные: После создания OAuth Client ID нажмите на кнопку Download JSON, чтобы загрузить файл credentials.json.

- Сохраните файл: Сохраните загруженный файл credentials.json в безопасном месте на своем компьютере.

Далее необходимо привести файл credentials.json к формату
```
{
    "web": {
        "client_id": <client_id>,
        "project_id": <project_id>,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": <client_secret>,
        "redirect_uris": [
            "http://localhost:8501"
        ]
    }
}
``` 

## Attention
В связи с работой модели в браузере, она может залагивать, вследвствие чего нужно нажать F5 и ввести команду заново. Также лучше не говорить в пустоту, так как это может вызвать ошибки работы сервиса и лишние вызовы LLM.  
**Спасибо за понимание**

