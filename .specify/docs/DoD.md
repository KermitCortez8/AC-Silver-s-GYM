# Definition of Done

Un cambio se puede cerrar cuando cumple las condiciones aplicables y conserva
evidencia de su verificación. La existencia de pruebas no significa que se hayan
ejecutado. Esta base documental no declara certificado el producto completo.

## Condiciones de cierre

- [ ] La spec contiene los siete componentes y criterios binarios numerados.
- [ ] `context.md` identifica base, módulos, código, pruebas y reutilización; el plan lo enlaza.
- [ ] Cada criterio tiene evidencia: prueba existente/nueva o procedimiento manual reproducible.
- [ ] Plan y tareas coinciden con el comportamiento finalmente entregado.
- [ ] Se conservan permisos, privacidad, identidad, importes, fechas y atomicidad afectados.
- [ ] Las comprobaciones pertinentes pasan; los fallos u omisiones están declarados.
- [ ] Se actualizó el contrato vivo del módulo y los documentos transversales afectados.
- [ ] No hay secretos ni datos reales añadidos al repositorio.
- [ ] Si cambia SQL, se documentaron dependencias, orden, recuperación y verificación aislada.
- [ ] Si cambia interfaz, se registró la revisión visual pertinente.

## Comprobaciones desde la raíz

| Alcance | Comando |
| --- | --- |
| Documentación, contexto e integración SDD | `python .specify/.codex/hooks/validate.py` y `python -B -m unittest discover -s .specify/tests -v` |
| Backend | `(cd backend && python -m pytest tests/ -q)` |
| Errores Python del control existente | `(cd backend && python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics)` |
| Frontend | `(cd frontend && npm test)` y `(cd frontend && npm run build)` |
| Función de correo | `deno check supabase/functions/schedule-emails/index.ts` y `deno test supabase/tests/` |

Preparar dependencias según [README](../../README.md). Para cambios de reglas,
empezar por los archivos de prueba enlazados desde el módulo y ejecutar la suite
del componente cuando corresponda. No hay script `npm run lint` en este proyecto.

## PostgreSQL y migraciones

[test_atomic_transactions_postgres.py](../../backend/tests/test_atomic_transactions_postgres.py)
requiere `GYM_TEST_POSTGRES_CONTAINER` apuntando a un PostgreSQL desechable con
base `gym_test`, usuario `postgres` y acceso por `docker exec`. Su fixture trunca
tablas y aplica 014/015/016/020; no apuntarlo a una base compartida. La preparación
reproducible está en [pr-validation.yml](../../.github/workflows/pr-validation.yml).
Sin esa variable estas pruebas se omiten, y debe informarse la omisión.
El mismo job incluye
[test_public_preregistrations_postgres.py](../../backend/tests/test_public_preregistrations_postgres.py),
que comprueba privacidad, atomicidad y concurrencia de la conversión a cliente.

El conjunto de migraciones presupone un esquema previo: no asumir que constituye
una instalación completa de la base desde cero. Hay numeraciones `008`/`009`
compartidas y archivos de rollback. Seleccionar dependencias por nombre y contenido;
no ejecutar ciegamente todos los `.sql` en orden alfabético. Para persistencia
actual, consultar las precondiciones y enlaces SQL de [arquitectura](arquitectura.md).

Los scripts de [tests/manual](../../backend/tests/manual/README.md) no son pytest;
algunos escriben sobre la base configurada.

## Evidencia de cierre

En `tasks.md` o en la descripción del cambio, registrar fecha, comandos, resultados,
criterios cubiertos y límites. Para una omisión, incluir causa e impacto; no marcar
como comprobado el criterio dependiente. CI valida PR y pruebas según los
workflows; un hook de Render aceptado no confirma que el despliegue haya terminado.
