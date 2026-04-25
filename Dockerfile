FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY data/ ./data/
COPY tests/ ./tests/
COPY webapp/ ./webapp/
COPY app.py .

RUN mkdir -p /app/.chroma

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
