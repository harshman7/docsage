# FastAPI backend — build from repository root:
# docker build -f api/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app/ ./app/
COPY api/scripts/ ./scripts/

RUN mkdir -p data/raw_docs data/processed data/embeddings

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
