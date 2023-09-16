FROM python:3.11.2-slim-bullseye AS BASE

WORKDIR /app

COPY frontend_app/requirements.txt /app/frontend_app/requirements.txt
RUN pip install -r /app/frontend_app/requirements.txt

COPY frontend_app/main.py /app/main.py
COPY frontend_app/__init__.py /app/frontend_app/__init__.py

COPY database /app/database

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "/app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]