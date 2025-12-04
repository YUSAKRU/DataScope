# İKA-VMS v2.0 - Docker Image
#
# Build:
#   docker build -t ika-vms:2.0 .
#
# Run:
#   docker run --rm -v ./outputs:/app/outputs ika-vms:2.0 --hashtag iklim --limit 50
#

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create directories
RUN mkdir -p /app/data /app/outputs /app/logs /app/credentials

# Set environment variables for the application
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/key.json \
    OUTPUT_DIR=/app/outputs \
    LOG_DIR=/app/logs \
    DATA_DIR=/app/data

# Create non-root user for security
RUN useradd -m -u 1000 ikavms && \
    chown -R ikavms:ikavms /app

USER ikavms

# Set entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command (show help)
CMD ["--help"]


