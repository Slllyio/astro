# Backend image for the Jyotish reading engine (FastAPI + pyswisseph).
# The Android app is a thin WebView over this server; deploy it on any host
# that runs Docker (Render, Railway, Fly.io, a VPS) and point the app at the URL.
FROM python:3.11-slim

# gcc is only needed if a source build of pyswisseph is required; harmless otherwise.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the application source (the engine, templates) and the runtime data the
# reading needs: the encoded B. V. Raman compendium + its schema + conflicts.
# (Ephemeris uses the built-in Moshier model, so no .se1 data files are needed.)
COPY app ./app
COPY data/raman_doctrine/compendium ./data/raman_doctrine/compendium
COPY data/raman_doctrine/schema ./data/raman_doctrine/schema

ENV PORT=8000
EXPOSE 8000

# Serve the slim reading-only app (app.reading_app) — not app.main, which also
# mounts auth/RAG/mundane routers with heavier dependencies. One Uvicorn worker
# is plenty for personal/family use; scale via the host.
CMD ["sh", "-c", "uvicorn app.reading_app:app --host 0.0.0.0 --port ${PORT}"]
