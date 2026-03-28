FROM python:3.11-slim

WORKDIR /app

# Build tools needed for some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps — prefer pre-built binary wheels to avoid compiling
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

EXPOSE 10000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1
