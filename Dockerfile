# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Build tools install chestunnam
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --prefix=/install vadi specific location lo install chestunnam
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user setup
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Builder nundi packages ni /usr/local loki copy chestunnam (Permission fix!)
COPY --from=builder /install /usr/local

# App code copy
COPY app/ app/

# Folder permissions appuser ki icchesthinnam
RUN chown -R appuser:appuser /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switching to appuser
USER appuser

EXPOSE 8000

# Healthcheck (httpx install ayyi undali requirements.txt lo)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://localhost:8000/health'); r.raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]