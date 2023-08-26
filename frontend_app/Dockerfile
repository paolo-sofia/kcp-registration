FROM python:3.8

COPY ./frontend /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["streamlit", "run", "app.py"]
