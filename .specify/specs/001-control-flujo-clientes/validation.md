# Validación del control del flujo de clientes

Fecha: 2026-10-29. Alcance: MOD-01/02/03/05/06, sobre datos sintéticos locales.

## Especificación, aclaración, análisis y convergencia

Se creó una sola feature mediante create-new-feature.sh. Contexto y siete componentes
completados antes de setup-plan.sh; diseño y contratos antes de setup-tasks.sh.
El análisis de ambigüedades no encontró decisiones de producto que requirieran preguntas:
se conservan las reglas de los contratos existentes, sin nueva experiencia gratuita.
No existe extensions.yml: no hay hooks de extensiones registrados que ejecutar.

Revisión con el perfil revisor en esta sesión: cinco requisitos funcionales, dos
resultados medibles, nueve criterios y dieciséis tareas; cobertura de criterios 9/9.
Sin duplicaciones, requisitos sin tareas, ambigüedades críticas ni conflictos con la
constitución en el alcance definido. Los prerrequisitos oficiales de analyze, implement
y converge pasaron; checklist de calidad de especificación con 4/4 elementos completos.

Convergencia final: contrastados nueve criterios, ocho decisiones del plan y siete principios
con las fuentes y pruebas. No se identificó trabajo funcional faltante, parcial,
contradictorio o no solicitado dentro de esta feature. No se añadió fase vacía de tareas.

## Defectos reproducidos y evidencia por criterio

La primera ejecución de las regresiones nuevas, antes del cambio productivo, dio
**24 fallos y 1 aprobado**. Tras la corrección pasaron los 25; se ampliaron a 31 casos
con recorridos integrados, compatibilidad histórica y respuestas HTTP.

| Criterio | Evidencia ejecutada en test_client_flow_control.py | Resultado |
| --- | --- | --- |
| CA-01 | Recorrido PUBLICO: alta repetida, contraseña incorrecta y DNI ajeno | Sin duplicación ni reutilización ajena |
| CA-02 | Fallo de persistencia al borrar, identificadores inválidos, HTTP 400/503 y borrado correcto | Sin 204 falso; detalle privado oculto |
| CA-03 | Compra pagada/activa/vencida, intento de transferencia, edición pendiente y HTTP 400 | Rechazo sin mutación; pendiente sin activación |
| CA-04 | Importe guardado cero y compatibilidad ausente/null | No sustituye cero; mantiene fallback histórico |
| CA-05 | Día inexistente, texto sobrante, segundos no cero y AM/PM inválido; formatos válidos | Rechaza inválidos y guarda HH:MM |
| CA-06 | Fechas vacías e imposibles, último día y vencimiento | Sin entrada inválida; fecha final inclusiva |
| CA-07 | Recorridos PUBLICO/ADMIN: pago, activación repetida, acceso, matrícula, cupo, entrada/salida y cancelación | Flujos integrados aprobados |

Pruebas en [test_client_flow_control.py](../../../backend/tests/test_client_flow_control.py).
Las suites existentes amplían la comprobación a errores HTTP, identidad, privacidad,
permisos, Stripe simulado, concurrencia y transacciones.

## Comandos y resultados

Se creó `/tmp/gym-control-venv` con requirements-dev.txt. Python local 3.14;
las dependencias permanecen sin cambios en el repositorio. Para tokens se usó la
clave sintética de CI únicamente como variable AUTH_SECRET_KEY del proceso.

| Comando / procedimiento | Resultado |
| --- | --- |
| Primera suite backend sin AUTH_SECRET_KEY | 545 aprobados, 15 omitidos, 6 fallos de configuración; se corrigió el entorno de pruebas |
| Regresiones antes de implementar | 24 fallos reproducidos, 1 aprobado |
| `python -m pytest tests/test_client_flow_control.py -q` con clave sintética | 31 aprobados |
| `python -m pytest tests/ -q` con clave sintética y GYM_TEST_POSTGRES_CONTAINER | 597 aprobados, 0 omitidos, 0 fallos (incluidas 15 pruebas PostgreSQL) |
| `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` desde backend | 0 errores |
| `npm test` desde frontend | 257 aprobados, 0 fallos (incluidas 9 regresiones nuevas de UI) |
| `npm run build` desde frontend | Compilación correcta |
| `python -B -m unittest discover -s .specify/tests -v` | 13 aprobados |
| `python .specify/.codex/hooks/validate.py` | Documentación válida: 58 archivos, 13 contratos |
| `git diff --check` | Sin errores de espacios |

PostgreSQL 16 se levantó en el contenedor exclusivo `gym-control-postgres`, sin red,
con base gym_test, usuario postgres y credenciales sintéticas. Se ejecutaron las 15
pruebas opt-in de test_atomic_transactions_postgres.py; las escrituras y truncados
quedaron limitados a esa base desechable. No se cambiaron migraciones.

## Auditoría de cierre

Se aplicó el perfil auditor en esta sesión. Revisados actor, permisos HTTP conservados,
propietario de la membresía, sanitización del error de persistencia, importe guardado,
activación independiente, idempotencia y fechas de Perú en las rutas afectadas.
Se conservaron comandos con recursos y las RPC existentes; las suites de límites de
capas, operaciones acotadas y PostgreSQL forman parte de la ejecución completa.
No se detectaron defectos adicionales en el diff revisado que impidan estos criterios.

Los contratos MOD-02, MOD-03, MOD-05 y MOD-06 y el índice de features se actualizaron.
Se corrigieron PaymentView y los detalles de clientes; ver revisión visual abajo.
El recorrido de pago se verificó sobre la ruta real y el diálogo con componentes
reales en un arnés aislado; la API y las operaciones de guardado fueron simuladas.

## Límites observados

Stripe, Google, Resend y Supabase remotos no se contactaron ni se certificaron.
La confirmación Stripe del recorrido usa pasarela simulada; las notificaciones también.
Deno no se ejecutó porque no cambió la Edge Function ni su contrato.
Una advertencia de compatibilidad FastAPI/Starlette/httpx apareció en las pruebas,
sin fallos. npm ci informó 9 avisos de dependencias (1 moderado y 8 altos);
no se cambiaron dependencias como parte de estas correcciones funcionales.
El build informó advertencias de tamaño de fragmentos y tiempos de plugins; terminó bien.

## Cierre de ejecución

Última ejecución completa: **597 aprobados, 0 fallos, 0 omitidos**, en 42,44 s.
Los 31 casos de la feature y las 15 pruebas PostgreSQL están incluidos en ese total.
Tareas T001–T016 completadas. Hook close y validador global se ejecutan sobre estos
artefactos finales; sus resultados se consignan a continuación.

- Hook close: aprobado, precondiciones de cierre correctas para 001-control-flujo-clientes.
- Validador global final: aprobado, 58 archivos y 13 contratos de siete componentes.
- Unittest SDD final: 13 aprobados en 5,567 s.
- Contenedor gym-control-postgres eliminado al terminar las pruebas.
- Revisión final de espacios con git diff --check: sin errores.

## Corrección adicional de frontend y evidencia visual

La entrega inicial no incluyó cambios de frontend; la revisión solicitada por el
usuario añadió CA-08 y CA-09 a la misma feature y completó las tareas T013–T016.

- PaymentView diferencia error, comprobación, pendiente y confirmado. Reintentar
  consulta la misma sesión, limpia el error anterior y bloquea solicitudes simultáneas.
  Comprueba id_cliente devuelto por servidor y descarta respuestas tras cambiar de ruta.
- useClientMembershipActions bloquea confirmaciones manuales repetidas mientras
  está en curso. El botón muestra «Confirmando pago…». Al activar, viewingClient
  se sustituye por la respuesta confirmada para actualizar estado y acciones del diálogo.
- ClientDetailsDialog y ClientsView conectan estos estados con los botones reales.

Regresiones en [36-client-flow-control.test.js](../../../frontend/tests/36-client-flow-control.test.js):
9 aprobadas. Suite completa frontend: **257 aprobadas**. Build final: correcto.
El backend no cambió en esta ampliación: conserva su ejecución de **597 aprobadas**.

| Criterio | Comprobación | Resultado |
| --- | --- | --- |
| CA-08 | Error seguido de reintento con misma URL, pendiente, cliente ajeno, petición duplicada, ruta sustituida y sesión ausente | 6 pruebas aprobadas y recorrido real de retorno en navegador |
| CA-09 | Petición manual duplicada, fallo manual y sincronización después de activar | 3 pruebas aprobadas; botones y ficha verificados en navegador |

Chromium/Playwright se instalaron fuera del repositorio para esta revisión, sin cambiar
package.json ni lockfile. API de pago interceptada localmente; no se enviaron peticiones
a proveedores. Diálogo verificado con componentes y composable reales, con guardados
simulados. Dos tamaños: 1440×1000 y 390×844; diálogo en oscuro y claro. Sin desbordamiento
horizontal ni excepciones de página en estos recorridos.

Capturas inspeccionadas:

- [Pago con error, escritorio](evidence/pago-error-escritorio.png).
- [Pago con error y reintento, móvil](evidence/pago-error-movil.png).
- [Pago confirmado tras reintento, móvil](evidence/pago-confirmado-movil.png).
- [Confirmación manual bloqueada mientras guarda](evidence/cliente-pago-en-curso.png).
- [Ficha activada, escritorio oscuro](evidence/cliente-activado-oscuro.png).
- [Ficha activada, móvil claro](evidence/cliente-activado-movil-claro.png).

[Resultados de navegador](evidence/browser-results.json),
[arnés de diálogo](evidence/client-dialog-harness.html) y
[script de revisión](evidence/browser-review.cjs) conservados. Para reproducir con el
mismo entorno: copiar el arnés a frontend/.flow-review.html, iniciar Vite en 5173
con /api local y ejecutar el script con Playwright instalado; el script usa /tmp/gym-browser.
Eliminar frontend/.flow-review.html al terminar; no es una ruta de producto.

Cierre tras ampliar frontend: hook close y validador global aprobados; 13 pruebas
SDD aprobadas en 5,227 s. Revisión final del diff sin errores de espacios.
La convergencia final cubre CA-01…CA-09 y las 16 tareas, con evidencia visual propia
para los cambios de pantalla. No se modificaron servicios remotos ni despliegues.
