FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

RUN useradd --create-home --uid 10001 appuser \
    && install -d --owner=appuser --group=appuser /app/db/store-images

COPY --chown=appuser:appuser config.py dependencies.py ./
COPY --chown=appuser:appuser app/*.py ./app/
COPY --chown=appuser:appuser models/*.py ./models/
COPY --chown=appuser:appuser routes/*.py ./routes/
COPY --chown=appuser:appuser services/*.py ./services/
COPY --chown=appuser:appuser utils/*.py ./utils/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
