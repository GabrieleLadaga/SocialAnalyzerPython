FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir click
RUN python -m spacy download en_core_web_sm

COPY src/ ./src/
COPY .env .env

CMD ["python", "src/main.py"]