# Use a lightweight Debian Linux base image
FROM python:3.10-slim

# Set environment variables for efficient Python execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install OS dependencies (Required for FFmpeg only)
# Clean apt cache directly in one layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# DevOps Security Implementation: Initialize Non-Root User
RUN useradd -m baarian_user

# Copy all project source code with immediate ownership assignment to avoid layer duplication
COPY --chown=baarian_user:baarian_user . .

# Secure container runtime environment
USER baarian_user

# Execute main pipeline
CMD ["python", "main.py"]