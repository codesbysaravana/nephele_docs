# Production Dockerfile for Nephele Technical Interview Engine
FROM python:3.11-slim

# Prevent python compiling bytecode and buffering streams
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start FastAPI app server
CMD ["sh", "-c", "alembic upgrade head || true && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
