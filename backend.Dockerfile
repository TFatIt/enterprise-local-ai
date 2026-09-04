# Backend Dockerfile for Enterprise Local AI Assistant
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for document parsing and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend /app

# Ensure uploads, documents and chroma data directories exist
RUN mkdir -p /app/uploads /app/chroma_data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
