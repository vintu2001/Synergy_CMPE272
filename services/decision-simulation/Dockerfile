FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create directories for KB and vector stores (will be mounted as volumes in docker-compose)
RUN mkdir -p ./kb && mkdir -p ./vector_stores/chroma_db

# Expose port
EXPOSE 8003

# Run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8003}"]

