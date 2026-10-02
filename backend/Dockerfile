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

# appuser puede leer el codigo, pero solo root puede modificarlo.
# Los archivos subidos conservan escritura en /app/db/store-images.
COPY --chown=root:root --chmod=644 config.py dependencies.py ./
COPY --chown=root:root --chmod=644 app/*.py ./app/
COPY --chown=root:root --chmod=644 models/*.py ./models/
COPY --chown=root:root --chmod=644 routes/*.py ./routes/
COPY --chown=root:root --chmod=644 services/*.py ./services/
COPY --chown=root:root --chmod=644 utils/*.py ./utils/

# Los directorios necesitan permiso de acceso, sin permitir escritura a appuser.
RUN chmod 755 /app/app /app/models /app/routes /app/services /app/utils

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
