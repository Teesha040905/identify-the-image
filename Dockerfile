# Identify The Image: a small FastAPI app that tells cats from dogs.
# One container: the FastAPI backend also serves the static frontend.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FRONTEND_DIR=/srv/frontend

WORKDIR /srv/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY backend/models ./models
COPY frontend /srv/frontend

# Run as a normal user, not root.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# Kept on one line: DeployPilot reads the health URL (/health) from it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
