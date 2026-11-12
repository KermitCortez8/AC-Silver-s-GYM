# Corrección de CI de backend y PostgreSQL

Fecha: 2026-11-12. Referencia inspeccionada: `b0e4547`.

## Síntomas y correcciones

Los logs de [backend-ci](https://github.com/KermitCortez8/AC-Silver-s-GYM/actions/runs/43301229047/job/131473046275)
confirman `no tests ran` y código 5. El mismo error afecta a la matriz backend de
la validación de PR. [backend/.dockerignore](../../../../backend/.dockerignore)
solo admitía pruebas en la raíz de `tests/`, anterior a su organización por módulo.
Ahora conserva las subcarpetas y `tests/soporte/`, excluyendo únicamente las
carpetas `manuales` además de los archivos y secretos ya ignorados globalmente.
Ambos workflows reutilizan este contexto; pytest sigue rechazando una suite vacía.

El [job PostgreSQL del PR](https://github.com/KermitCortez8/AC-Silver-s-GYM/actions/runs/43301164878/job/131472420441)
también falla: tres casos de asistencia general esperan `cierre_automatico` y el
cierre de visitas vencidas, pero la migración 023 tenía 0 bytes. Se completó
[023_general_attendance_three_hour_close.sql](../../../../backend/migrations/023_general_attendance_three_hour_close.sql)
con el contrato existente de [MOD-06/CA-11](../../modulos/06-asistencias.md): plazo
de tres horas en Perú, cierre auditado, aforo liberado, reintentos y exclusión
mutua con las salidas manuales. Las clases continúan necesitando una salida real.

Se conserva la RPC instalada por 018 o 019 como función auxiliar privada, de
modo que la reconciliación sucede antes de comprobar entrada abierta, aforo,
versión y reintentos. La corrección administrativa conserva el evento automático
y permite reconstruir una salida real. Las generales históricas ya cerradas
no se reclasifican al repetir la migración.

## Criterios de regresión

- La imagen `test` contiene todas las suites `test_*.py`, sus paquetes, `conftest.py`,
  `tests/soporte/atomic_fake.py` y el esquema SQL; no incluye scripts manuales.
- El comando original de `backend-ci` ejecuta las pruebas y flake8 sin red,
  con usuario sin root y clave sintética.
- Los seis módulos del job PostgreSQL mantienen sus comprobaciones; pasan los
  casos de general que fallaban, incluidos migración repetible y concurrencia.
- Las regresiones añadidas comprueban reingreso sin cron, conservación de salidas
  históricas y permisos de la función auxiliar, además de la admisión por fecha
  cuando 023 se instala después de 019.

## Instalación y recuperación

023 requiere esquema previo y 005, 013, 018 y 021. Si se utiliza 019, aplicarla
antes de 023. La migración conserva el cuerpo de la RPC instalada y puede repetirse.
022 puede programar la misma función cuando pg_cron está habilitado; no es
necesaria para la reconciliación por RPC. No aplicar indiscriminadamente todas
las migraciones del repositorio.

Para recuperar la versión anterior, pausar el trabajo
`silver-gym-incomplete-attendance`, detener las escrituras del backend y restaurar
la RPC desde `guardar_asistencia_sin_cierre_general`, sus permisos privados y las
funciones de 021. Conservar columnas, versiones, salidas y auditorías; un cierre
automático ya registrado no debe borrarse. No se ejecutó esta recuperación ni
se aplicaron migraciones sobre una base compartida.

## Comprobaciones de esta entrega

| Comprobación | Resultado |
| --- | --- |
| Construir y ejecutar la imagen anterior con el comando de `backend-ci` | Reproducido: flake8 imprime `0` y pytest devuelve `no tests ran`. |
| `docker build --target test --tag gym-ci-backend-fixed ./backend` | Aprobada. |
| Comparar los archivos Python de `tests/` del checkout y de la imagen | Coinciden los 82 archivos Python y las 46 suites. Fixture SQL presente, scripts manuales ausentes y UID 10001. |
| `docker run --rm --network none --env AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef gym-ci-backend-fixed` | Flake8: 0 errores. Pytest: 751 aprobadas y 57 omitidas, 0 fallos, en 31,77 s. Las 57 requieren el PostgreSQL explícito. |
| Los seis archivos del job PostgreSQL de `pr-validation.yml`, con `GYM_TEST_POSTGRES_CONTAINER=gym-ci-fix-postgres` | 49 aprobadas y 3 omitidas, 0 fallos, en 181,63 s. Incluye las tres nuevas regresiones. Las omisiones requieren pg_cron, ausente en `postgres:16-alpine`. |
| Validación sintáctica YAML | Los tres workflows existentes se parsean correctamente. |
| `python .specify/.codex/hooks/validate.py` en la instantánea Linux | Aprobada: 131 documentos y 14 contratos. |
| `python -B -m unittest discover -s .specify/tests -v` en Linux, con enlaces nativos y LF | 13 aprobadas, 0 fallos, en 17,814 s. |
| `git diff --check` | Sin errores. |

El contenedor SQL se creó exclusivamente para esta entrega, con base `gym_test`,
datos sintéticos, `--network none` y sin publicar puertos. Las pruebas se ejecutaron
con Python 3.12 y `requirements-dev.txt` en un entorno temporal; Windows necesitó
además `tzdata` para resolver `America/Lima`. No se modificaron dependencias del
producto ni se accedió a proveedores o bases remotas.

La primera validación documental en Windows falló porque el checkout materializa
los enlaces nativos como archivos (`core.symlinks=false`) y las pruebas no tienen
privilegio para crearlos (`WinError 1314`). Se usó una instantánea Git en un
contenedor Linux aislado, conservando los enlaces del índice y superponiendo
únicamente los archivos de esta corrección. El primer archivo tar heredó CRLF de
Windows; se reconstruyó con `git -c core.autocrlf=false archive` antes de repetir
las pruebas. No se modificaron los enlaces ni scripts oficiales del repositorio.

Frontend, construcción/proxy y Deno estaban aprobados en las ejecuciones remotas
inspeccionadas; no se repitieron sus suites locales porque sus fuentes no cambian.
No se ejecutaron los scripts manuales ni un despliegue, ni se relanzó GitHub
Actions con estos cambios locales. La aplicación de 023 en una base remota queda
fuera de esta comprobación.
