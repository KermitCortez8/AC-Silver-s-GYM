# Trabajo en AC Silver's GYM

## Desarrollo guiado por especificaciones

Para cambios funcionales, leer `.specify/memory/constitution.md` y trabajar con
`specs/<numero>-<cambio>/spec.md`, `plan.md` y `tasks.md`. Usar las skills oficiales
de `.agents/skills/speckit-*` cuando corresponda. La guía local está en
`docs/spec-driven-development.md`.

Antes de cambiar comportamiento, definir el escenario esperado y su evidencia.
Reutilizar pruebas existentes; añadir una regresión cuando falte un escenario.
Actualizar criterios, plan y tareas si cambia el alcance. Documentación, formato
y refactorizaciones sin cambios de comportamiento no requieren otra spec.

Conservar las cuatro capas de ambos proyectos y los contratos públicos salvo que
el cambio solicitado requiera modificarlos expresamente. Las vistas no hacen
HTTP directo; dominio y aplicación backend no importan infraestructura o FastAPI.

No marcar tareas ni especificaciones como verificadas solo por existir pruebas.
Registrar comandos, resultados y limitaciones en la carpeta de la funcionalidad.
Los resultados omitidos de PostgreSQL o de revisión visual siguen pendientes.

Los archivos instalados de Spec Kit son herramientas de desarrollo. Mantener
personalizaciones del proyecto fuera de las skills y plantillas oficiales para
facilitar actualizaciones. No reinicializar con `--force` sobre trabajo existente
sin revisar antes los archivos que se reemplazarían.

## Comprobaciones existentes

- Frontend: `npm --prefix frontend test` y `npm --prefix frontend run build`.
- Backend, con dependencias de desarrollo y desde `backend/`:
  `python -m pytest tests/ -q` y
  `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`.
- PostgreSQL aislado: `backend/tests/test_atomic_transactions_postgres.py`,
  habilitado mediante `GYM_TEST_POSTGRES_CONTAINER`; consultar el workflow de PR.
- Contratos de arquitectura: `backend/tests/test_layer_boundaries.py` y
  `frontend/tests/23-layer-boundaries.test.js`.

Para los tests que requieren firma de sesión usar una clave exclusiva de pruebas,
como la configurada en `.github/workflows/pr-validation.yml`.
