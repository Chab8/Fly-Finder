# Fly Finder API image. Build from the repository root:
#   docker build -f backend/Dockerfile -t fly-finder-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface
WORKDIR /app

COPY backend/requirements.txt backend/requirements-ml.txt backend/
# CPU-only torch keeps the image far smaller than the default CUDA build.
RUN pip install -r backend/requirements.txt \
 && pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install open_clip_torch==3.3.0

COPY backend/app backend/app
COPY data/catalog data/catalog
COPY data/demo data/demo

RUN useradd --create-home appuser && mkdir -p /app/.cache && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "--app-dir", "backend", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
