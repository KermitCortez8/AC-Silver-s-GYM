# Relojes de asistencia y pruebas PostgreSQL

## Problema y corrección

La fixture de `test_general_attendance.py`, compartida con los casos de horarios
y sesiones, simulaba el 7 de octubre de 2026 con membresías válidas hasta el 31
de octubre. Las consultas de clientes y membresías proyectaban vencimientos con
la fecha real del dominio. Desde noviembre devolvían estado vencido antes de
comprobar la condición de asistencia que cada caso pretendía ejercitar.

Se enlazó `_today_iso` del dominio con `service.now().date()` mediante la fixture
`monkeypatch`. El enlace sigue cualquier sustitución posterior de `service.clock`
y se restaura al terminar cada prueba. No cambia el reloj ni las reglas del
producto. Una regresión comprueba vigencia en octubre y vencimiento en noviembre,
conservando el estado guardado cuando solo se consulta su proyección.

## Causa de las 33 omisiones

Todos los casos SQL se omiten explícitamente cuando no existe
`GYM_TEST_POSTGRES_CONTAINER`. La condición protege bases compartidas: sus fixtures
borran y reconstruyen el esquema `public`, reinician tablas y aplican migraciones.

| Archivo | Casos | Cobertura |
| --- | ---: | --- |
| `test_atomic_transactions_postgres.py` | 15 | Transacciones, permisos, rollback, concurrencia y campos guardados. |
| `test_attendance_deadline_postgres.py` | 6 | RPC de asistencia, cierre de clase, salida tardía, auditoría y permisos. |
| `test_public_preregistrations_postgres.py` | 5 | Privacidad, conversión atómica y concurrencia de preregistros. |
| `test_schedule_sessions_postgres.py` | 7 | Reservas por fecha, cupos, admisión, migración y recordatorios. |

Se ejecutaron los 33 casos en `gym-clock-review-postgres`, creado expresamente con
`postgres:16-alpine`, red `none`, sin puertos publicados ni datos del gimnasio.
El contenedor se eliminó al terminar y no queda una base de pruebas ejecutándose.
El esquema sintético exige que la base se llame `gym_test`. Las pruebas usan
contraseñas y proveedores de pago simulados; no acceden a Supabase ni Stripe reales.

El job PostgreSQL de `.github/workflows/pr-validation.yml` solo incluía los
archivos de transacciones y preregistros (20 casos). Ahora incluye también
asistencia y sesiones (13 casos adicionales). Se mantiene la omisión optativa en
las ejecuciones locales que no preparen PostgreSQL explícitamente.

## Resultados

- Suite sin PostgreSQL: **680 aprobadas, 33 omitidas, 0 fallos**.
- Los cuatro módulos PostgreSQL: **33 aprobadas, 0 omitidas, 0 fallos**.
- Suite completa con PostgreSQL: **713 aprobadas, 0 omitidas, 0 fallos**.
- Flake8 `E9,F63,F7,F82`: aprobado, 0 errores.
- Pruebas de `.specify`: **13 aprobadas**.
- Validador documental y `git diff --check`: aprobados.

La ejecución remota de GitHub Actions no se ha lanzado; se comprobó localmente
el comando equivalente del workflow.

## Reproducción

Preparar dependencias con `backend/requirements-dev.txt` y un contenedor nuevo:

```bash
docker run --rm --detach --name gym-clock-review-postgres --network none \
  --env POSTGRES_PASSWORD=local-clock-review-tests-only \
  --env POSTGRES_DB=gym_test postgres:16-alpine
docker exec gym-clock-review-postgres pg_isready -U postgres -d gym_test
```

Esperar que `pg_isready` confirme disponibilidad y ejecutar desde la raíz:

```bash
GYM_TEST_POSTGRES_CONTAINER=gym-clock-review-postgres \
AUTH_SECRET_KEY=local-clock-review-tests-only-secret-0123456789 \
python -m pytest backend/tests/ -q -ra
python -m flake8 backend --count --select=E9,F63,F7,F82 --show-source --statistics
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

Al terminar, retirar únicamente el contenedor creado para esta comprobación:

```bash
docker rm --force gym-clock-review-postgres
```

Los resultados de esta sesión se guardan en [results.json](evidence/results.json).
