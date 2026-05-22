# =============================================================================
# Manufacturing MAS — Agent-02 Production & MES
# Multi-stage Docker build for production
# =============================================================================

# ── Stage 1: Base ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="Manufacturing MAS - Agent-02 Production & MES"
LABEL org.opencontainers.image.description="Production & MES agent for OEE calculation, quality alerting, and schedule optimization"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Manufacturing MAS Team"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app


# ── Stage 2: Dependencies ──────────────────────────────────────────────────
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn


# ── Stage 3: Production ────────────────────────────────────────────────────
FROM base AS production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY pyproject.toml .
COPY config/ config/
COPY src/ src/
COPY main.py .

# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Agent health check — verifies agent HTTP health endpoint is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live', timeout=5)" 2>/dev/null || exit 1

ENTRYPOINT ["python", "main.py", "--mode", "serve"]


# ── Stage 4: Development ───────────────────────────────────────────────────
FROM base AS development

COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

ENTRYPOINT ["python", "main.py", "--mode", "serve", "--log-level", "DEBUG"]
