# OrganAI — deployable CT segmentation & volumetry service
FROM python:3.11-slim

# System libs TotalSegmentator / nibabel / matplotlib need
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for layer caching
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# App code
COPY api ./api

# Persistent data volume for uploads + masks
ENV ORGANAI_DATA_DIR=/data \
    ORGANAI_DEVICE=cpu \
    ORGANAI_FAST=true
VOLUME ["/data"]

EXPOSE 8000

# Model weights (~150 MB) download on first inference; increase timeout accordingly.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
