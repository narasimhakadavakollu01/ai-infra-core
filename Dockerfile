# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (gcc lanti heavy tools ikkade untayi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Packages ni local user directory lo install chestunnam
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: Runtime (Final Slim Image) ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Security: Root user kakunda appuser create chestunnam
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Builder stage nundi kevalam installed packages matrame copy chestunnam
COPY --from=builder /root/.local /root/.local

# App code matrame copy chestunnam
COPY app/ app/

# Path and Environment settings
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switching to non-root user for security
USER appuser

EXPOSE 8000

# Healthcheck: App run avthundo ledho check chestundi
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://localhost:8000/health'); r.raise_for_status()"

# App start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]