# Single-stage Docker build for Advanced Duplicate Scanner (no external frontend)
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    netcat-openbsd \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r scanner \
    && useradd -r -g scanner scanner

# Install rclone for cloud storage access
RUN curl -sS -L https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rclone.zip \
    && unzip -d /tmp /tmp/rclone.zip \
    && mv /tmp/rclone-*/rclone /usr/bin/rclone \
    && chmod +x /usr/bin/rclone \
    && rm -rf /tmp/rclone*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/db /app/logs \
    && chown -R scanner:scanner /app \
    && chmod +x /app/scripts/*.sh

# Environment variables (can be overridden by docker-compose/.env)
ENV PYTHONPATH="/app" \
    SCANNER_ENV="production" \
    SCANNER_LOG_LEVEL="INFO" \
    SCANNER_WORKERS="4" \
    SCANNER_CHUNK_SIZE="8388608" \
    DATABASE_URL="sqlite:///app/db/duplicates.db" \
    RCLONE_CONFIG_PATH="/app/config/rclone.conf"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Switch to non-root user
USER scanner

# Expose API port
EXPOSE 8000

# Run application
CMD ["/app/scripts/start.sh"]