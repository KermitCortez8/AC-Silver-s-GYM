FROM python:3.12-slim AS runtime

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
COPY --chown=root:root --chmod=644 app/*.py ./app/
COPY --chown=root:root presentation/ ./presentation/
COPY --chown=root:root application/ ./application/
COPY --chown=root:root domain/ ./domain/
COPY --chown=root:root infrastructure/ ./infrastructure/

# Los directorios necesitan permiso de acceso, sin permitir escritura a appuser.
RUN find /app/app /app/presentation /app/application /app/domain /app/infrastructure -type d -exec chmod 755 {} + \
    && find /app/app /app/presentation /app/application /app/domain /app/infrastructure -type f -exec chmod 644 {} +

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Herramientas y pruebas solo en la imagen de CI.
FROM runtime AS test
USER root
COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY --chown=root:root --chmod=644 tests/test*.py tests/conftest.py ./tests/
RUN chmod 755 /app/tests
USER appuser
CMD ["sh", "-c", "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics && python -m pytest tests/ -q -p no:cacheprovider"]

# La construcción predeterminada conserva la imagen de producción.
FROM runtime AS production
