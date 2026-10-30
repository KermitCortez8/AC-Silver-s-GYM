# Validación del control de asistencia por horario

Fecha: 2026-10-29. Implementación directa de MOD-06 por petición del usuario,
sin activar Spec Kit ni generar specs, planes o tareas.

## Alcance y reglas verificadas

- Tabla de horarios activos, filtro por día y selección por fila o botón accesible.
  La lista de la clase contiene solo sus matrículas activas y las acciones individuales.
- Entrada durante toda la clase, opción confirmada por el usuario: inicio inclusivo,
  fin exclusivo y mismo día, con reloj del servidor en America/Lima. Fuera del
  intervalo se informa el motivo y no se guarda una asistencia.
- Salida a cualquier hora real. Exactamente fin más una hora permite completar;
  un segundo después queda incompleta y devuelve el aviso: «Ya pasó más de una hora
  desde el término de la clase. La asistencia queda incompleta.»
- Una visita sin salida superado el límite figura como incompleta al consultar.
  No se inventa una salida y sigue consumiendo aforo hasta registrar la salida real.
- El límite se conserva aunque el horario se edite o desactive; puede cruzar
  medianoche. El registro general mantiene el flujo por DNI y sus reglas actuales.
- Tabla y lista solo para admin; historial, exportación y semana del cliente
  conservan alcance propio y no muestran la auditoría administrativa.
- Al cambiar de horario, sesión o desmontar, las respuestas antiguas no sustituyen
  la lista actual. Tras registrar, se actualizan lista y resumen de la misma clase.

## Regresiones y persistencia

La corrección inicial del aviso de clase terminada reprodujo 6 fallos y 23 aprobados
antes del cambio. Después pasó test_general_attendance.py con 32 casos, incluidos
límites, DNI, reloj UTC/Lima, hora enviada por navegador y revalidación transaccional.

La ampliación actual añade test_schedule_attendance.py: tabla/lista, permisos,
intervalo de entrada, salida normal/tardía, vencimiento sin salida, cambio de día,
recarga, cambio del horario, historial privado, filtros paginados y falta de esquema.
La suite frontend 29-view-flows.test.js comprueba tabla, selección, descarte de
respuestas y aviso de salida tardía con actualización de la misma clase.

La migración [018](../../../../backend/migrations/018_attendance_schedule_exit_deadline.sql)
agrega limite_salida y salida_tardia y reemplaza guardar_asistencia conservando
auditoría, permisos y locks. Requiere el esquema previo, 005_harden_attendance.sql
y 013_general_attendance.sql; 014–017 no son dependencias de esta migración.
Se debe aplicar antes de usar este backend en Supabase.

La migración asigna límite a visitas de clase abiertas usando el horario vigente
al migrar; no reclasifica visitas cerradas históricas. Recuperación: restaurar la
función de 013 y conservar las columnas/datos adicionales. La transacción revierte
todo si falla. El repositorio valida el esquema antes de escribir, evitando guardar
una asistencia que perdería el límite por una instalación incompleta.

test_attendance_deadline_postgres.py aplica 005/013/018 en PostgreSQL real, repite
018, comprueba captura de plazo, hora del servidor, reintentos, rechazo al cierre,
salida tardía, auditoría, límite inclusivo, correcciones y permisos de la RPC.

## Comprobaciones completas

Dependencias Python instaladas fuera del repositorio en /tmp/gym-attendance-venv
desde requirements-dev.txt. AUTH_SECRET_KEY usa la clave sintética de CI.
PostgreSQL 16 se ejecuta en el contenedor exclusivo gym-attendance-postgres, sin red,
con base gym_test y credenciales sintéticas. GYM_TEST_POSTGRES_CONTAINER apunta
solo a ese contenedor; los truncados y migraciones quedan limitados a esa base.

| Comando / procedimiento | Resultado |
| --- | --- |
| `python -m pytest tests/ -q` con AUTH_SECRET_KEY sintética y GYM_TEST_POSTGRES_CONTAINER desde backend | 634 aprobados, 0 fallos, 0 omitidos; 62,39 s |
| `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` desde backend | 0 errores |
| `npm test` desde frontend | 262 aprobados, 0 fallos |
| `npm run build` desde frontend | Compilación correcta |
| Chromium/Playwright, ruta real /admin/attendance | Recorrido completo aprobado, sin errores de página ni desbordamiento horizontal |
| `python .specify/.codex/hooks/validate.py` | Documentación válida: 59 archivos, 13 contratos |
| `python -B -m unittest discover -s .specify/tests -v` | 13 aprobados |
| `git diff --check` | Sin errores de espacios |

## Revisión visual propia

Se montó la ruta real con sesión y API sintéticas interceptadas en el navegador,
sin contactar proveedores. Se comprobaron selección de clase, listado, bloqueo por
membresía y por día incorrecto, entrada, incompleta sin salida, salida tardía e historial.
Escritorio 1440×1100 en oscuro y móvil 390×844 en claro, sin desbordamiento horizontal.
Se inspeccionaron las capturas generadas:

- [Tabla y matriculados, escritorio](evidence/tabla-clientes-escritorio.png).
- [Incompleta sin salida, escritorio oscuro](evidence/incompleta-escritorio-oscuro.png).
- [Incompleta sin salida, móvil claro](evidence/incompleta-movil-claro.png).
- [Salida tardía guardada, móvil](evidence/salida-tardia-movil.png).
- [Entrada bloqueada en otro día](evidence/otro-dia-movil.png).
- [Historial con incompleta](evidence/historial-incompleta-movil.png).

[Resultados](evidence/browser-results.json) y [script reproducible](evidence/browser-review.cjs).
Iniciar Vite con VITE_AUTH_API_BASE_URL=/api en 127.0.0.1:5173 y ejecutar el script
desde la raíz con Playwright en /tmp/gym-attendance-browser/node_modules/playwright
o GYM_PLAYWRIGHT_MODULE. No se agregaron dependencias al frontend.

## Límites

Supabase remoto no se modificó ni se desplegó. La migración 018 se verificó solamente
en PostgreSQL local desechable y queda disponible para el despliegue del producto.
El navegador utiliza respuestas simuladas; las reglas y RPC se verifican por separado
con pruebas de backend y SQL real. Las pantallas actualizan sus lecturas cada minuto;
el servidor comprueba la hora exacta en cada intento de registro.

FastAPI/Starlette emite una advertencia de deprecación de httpx. Frontend conserva
avisos de contexto Pinia, rutas de prueba y antigüedad de Browserslist; no impiden
las suites ni la compilación. Deno no se ejecuta porque no cambió la Edge Function.

El contenedor desechable se eliminó al terminar. El servidor Vite de revisión se detuvo.
