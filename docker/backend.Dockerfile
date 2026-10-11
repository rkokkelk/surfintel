# Shared image for the FastAPI backend and all Celery roles (worker, beat,
# flower) — they're the same codebase/dependencies, only the container
# command (set in docker-compose.yml) differs.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir .

# Ingestion scrapes pages via a real Chromium (app/ingestion/playwright.py);
# --with-deps also installs the OS-level libraries Chromium needs on Debian.
RUN playwright install --with-deps chromium

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
