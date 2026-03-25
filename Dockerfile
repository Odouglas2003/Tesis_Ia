#############
# Python Multi-Stage Dockerfile
#############
# ===========================================
# Stage 1: Base - Common setup
# ===========================================
FROM python:3.11-bullseye AS base
RUN apt-get update && rm -rf /var/lib/apt/lists/*

# ===========================================
# Stage 2: Builder - Install dependencies
# ===========================================
FROM base AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .

# Instalación simple
RUN pip install --no-cache-dir wheel && \
    pip install --no-cache-dir -r requirements.txt

# ===========================================
# Stage 3: Production
# ===========================================
FROM python:3.11-bullseye as runtime
WORKDIR /app

RUN adduser --system --group --no-create-home appuser

RUN mkdir /app/cache && chown -R appuser:appuser /app/cache

# --- ¡BLOQUE ENV CORREGIDO! ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # ¡AÑADE ESTA LÍNEA DE VUELTA!
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

# Ahora el sistema encontrará 'uvicorn'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]