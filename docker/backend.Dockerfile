# Shared image for the FastAPI backend and all Celery roles (worker, beat,
# flower) — they're the same codebase/dependencies, only the container
# command (set in docker-compose.yml) differs.
FROM python:3.12-slim

ARG VERSION="v1.0.0"
ENV SURFINTEL_VERSION=${VERSION}
ARG COMMIT="9dce0c5"
ENV SURFINTEL_COMMIT=${COMMIT}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic

RUN pip install --no-cache-dir .

# Ingestion scrapes pages via a real Chromium (app/ingestion/playwright.py);
# --with-deps also installs the OS-level libraries Chromium needs on Debian.
RUN playwright install --with-deps chromium

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
