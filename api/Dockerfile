#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
FROM bmltenabled/uvicorn-gunicorn-fastapi:python3.10-slim

COPY ./api /app/api
COPY ./database /app/database

WORKDIR /app

RUN pip install --no-cache-dir -r /app/api/requirements.txt

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
