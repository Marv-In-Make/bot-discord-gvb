# ================================================================
# DISCORD BOT MONSTER - DOCKERFILE MULTI-STAGE
# ================================================================
# Python 3.11 optimisé pour production
# Build time: ~2 min | Image finale: ~250MB
# ================================================================

# === STAGE 1: Builder (compilation dépendances) ===
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libpq-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create virtual environment et install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# === STAGE 2: Runtime (image finale légère) ===
FROM python:3.11-slim

LABEL maintainer="Marvin Ansseau <marv.inmake83@gmail.com>"
LABEL description="Discord Bot Monster - GVB-Électricité"
LABEL version="2.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        ca-certificates \
        tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set venv in PATH
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=UTF-8

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash botuser && \
    mkdir -p /app/logs && \
    chown -R botuser:botuser /app

# Copy bot code
COPY --chown=botuser:botuser bot_monster.py .
COPY --chown=botuser:botuser admin_migration.py .
COPY --chown=botuser:botuser utils.py .
COPY --chown=botuser:botuser cogs/ ./cogs/

# Switch to non-root user
USER botuser

# Healthcheck endpoint API
HEALTHCHECK --interval=60s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose API REST port
EXPOSE 5000

# Expose Prometheus metrics port (optionnel)
EXPOSE 9090

# Start bot
CMD ["python", "bot_monster.py"]
