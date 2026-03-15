# Use an official Python slim image for a smaller footprint
FROM python:3.10-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures console output is sent directly to the logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
# libpq-dev is needed for psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# We copy requirements first to leverage Docker cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# The port your app runs on
EXPOSE 8000

# The default command to run when the container starts
# For DigitalOcean Web Services, we use gunicorn
# Note: Celery workers will override this command in app.yaml or the DO UI
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
