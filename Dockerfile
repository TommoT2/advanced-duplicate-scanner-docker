# Multi-stage Docker build for Advanced Duplicate Scanner
# Stage 1: Build React frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy package files for dependency caching
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with dependencies
FROM python:3.11-slim as backend-builder

# Install system dependencies for compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install rclone for cloud storage access
RUN curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip \
    && unzip rclone-current-linux-amd64.zip \
    && mv rclone-v*/rclone /usr/bin/ \
    && rm -rf rclone-* \
    && chmod +x /usr/bin/rclone

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production runtime
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r scanner \
    && useradd -r -g scanner scanner

# Copy virtual environment from builder stage
COPY --from=backend-builder /opt/venv /opt/venv
COPY --from=backend-builder /usr/bin/rclone /usr/bin/rclone

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Set up application directory
WORKDIR /app

# Copy application source
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/db /app/logs \
    && chown -R scanner:scanner /app \
    && chmod +x /app/scripts/*.sh

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    SCANNER_ENV="production" \
    SCANNER_LOG_LEVEL="INFO" \
    SCANNER_WORKERS="4" \
    SCANNER_CHUNK_SIZE="8388608" \
    DATABASE_URL="sqlite:///app/db/duplicates.db" \
    RCLONE_CONFIG_PATH="/app/config/rclone.conf"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER scanner

# Expose ports
EXPOSE 8000

# Run application
CMD ["/app/scripts/start.sh"]