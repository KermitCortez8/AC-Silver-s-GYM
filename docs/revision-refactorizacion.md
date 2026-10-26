# Revisión de los objetivos de la refactorización

Fecha: 2026-10-24 (UTC). Base: `4dcba89` y cambios presentes en el árbol de trabajo,
incluidas las seis correcciones funcionales y los cuatro grupos de smells
autorizados posteriormente. La evaluación corresponde al código local actual;
no acredita un despliegue ni una revisión individual de cierre de los 42 grupos.

## Dictamen

La refactorización cumple sus objetivos principales de separación entre capas,
dependencias explícitas, integridad transaccional y protección de sesiones.
Las correcciones posteriores resuelven los casos concretos reproducidos.
La paginación uniforme de toda la API y la reducción de responsabilidades de
todas las vistas continúan parcialmente cumplidas. No corresponde declarar
eliminada toda la deuda técnica de la auditoría original.

## Contraste entre objetivos y código

| Objetivo | Resultado | Evidencia revisada |
| --- | --- | --- |
| Separar presentación, aplicación, dominio e infraestructura | Cumplido en las dependencias verificadas | Bootstrap conecta proveedores; las pruebas de límites recorren imports. Dominio no importa FastAPI, Vue ni infraestructura. |
| Sustituir herencia múltiple y despacho por cadenas por composición y contratos explícitos | Cumplido para las operaciones actuales | `domain_components.py` compone reglas con capacidades; `GymRepository` recibe `GymQuery` y `GymCommand`; el ejecutor rechaza contratos inválidos. |
| Limitar cada mutación a sus recursos | Cumplido para los casos corregidos | `UpsertRutinaCommand` declara solo catálogo; los comandos de horarios y tienda ya no comparten el bloque amplio anterior. Las pruebas comprueban aislamiento y conflicto SQL ajeno. |
| Mantener atomicidad y evitar pérdida de cambios entre procesos | Cumplido en los escenarios probados | RPC genérica con comparación de instantáneas y reintento; RPC específicas de matrícula y asistencia. PostgreSQL comprueba rollback, concurrencia, identidades y permisos. |
| Aislar aplicaciones y sesiones del frontend | Cumplido en los consumidores revisados | Adaptadores asociados a Pinia y capturados al construir servicios; configuración copiada e inmutable. Pruebas con dos instancias, transportes distintos y respuestas pendientes. |
| Mejorar consultas de asistencia y matrícula | Cumplido para esos flujos; parcial para toda la API | Historial filtrado y paginado; resumen sin recorrer historial cerrado, con conteos y ocho recientes. Matrícula lee cinco recursos. Otros listados y las instantáneas aún cargan recursos completos. |
| Reducir duplicación y responsabilidades de vistas | Cumplido para las extracciones; parcial para todas las pantallas | Registro por código reutiliza registro por ID. Clientes y tienda delegan edición y diálogos; pagos e imágenes tienen composables propios. Persisten vistas extensas fuera de estas extracciones. |
| Conservar comportamiento y corregir las seis regresiones detectadas | Cumplido en los contratos probados | Acceso de personal inactivo, actor autenticado del progreso, fecha de alta, desglose persistido de pedidos, cascada del cliente y conteo de membresías vigentes tienen regresiones específicas. |

Las líneas de los scripts de `ClientsView.vue` y `StoreView.vue` bajan de 600 a
227 y de 449 a 205 frente a `4dcba89`. Es una medida auxiliar: la evidencia de
separación son los componentes y composables con responsabilidades y dependencias
concretas, además de sus pruebas de uso.

## Pendientes comprobados

1. **Concurrencia y coste por tabla.**
   [gym_unit_of_work.py](../backend/infrastructure/repositories/gym_unit_of_work.py),
   [gym_change_planner.py](../backend/infrastructure/repositories/gym_change_planner.py)
   y la migración 015 siguen comparando instantáneas completas y bloqueando tablas
   de los recursos elegidos. Dos cambios independientes dentro de una misma tabla
   pueden provocar reintento. Acotar recursos reduce conflictos ajenos, pero no
   equivale a control por fila.
2. **Paginación general incompleta.**
   [clients_routes.py](../backend/presentation/routes/clients_routes.py) devuelve
   la lista de clientes sin contrato de página; consultas de membresías y pedidos
   conservan listas completas. El resumen de asistencia y su historial especializado
   mejoran ese flujo, sin cerrar globalmente el hallazgo 22.
3. **Fachadas y vistas todavía amplias.**
   [gym_service.py](../backend/application/services/gym_service.py) y
   [gymStore.js](../frontend/src/application/stores/gymStore.js) conservan una
   interfaz central extensa. Es compatible con la composición interna, aunque
   limita su independencia. El seguimiento posterior separó responsabilidades
   también en `TrainerRoutineMonitorView.vue` y `AttendanceView.vue`.
   Otras vistas, como `TrainerRoutinesView.vue` y `HomeView.vue`, conservan scripts
   amplios y requieren una evaluación propia. El hallazgo 28 está reducido en las
   cuatro pantallas intervenidas, no cerrado para toda la presentación.

Estos límites no invalidan la atomicidad ni el aislamiento demostrado, pero
impiden una afirmación de cierre total de los smells.

## Verificación de la revisión inicial

| Comprobación | Resultado |
| --- | --- |
| Backend, Python 3.14, con clave sintética de sesión | 378 pasan; 14 SQL omitidas por requerir ejecución explícita |
| PostgreSQL 16 aislado, sin puertos publicados | 14 pasan |
| Frontend, Node 24 | 128 pasan |
| Compilación Vite de producción | Correcta |
| Flake8 `E9,F63,F7,F82` y `git diff --check` | Sin errores |

La suite ordinaria de backend necesita `AUTH_SECRET_KEY` de al menos 32 bytes.
Una primera ejecución sin esa variable falló en seis casos de emisión de sesión;
al proporcionar una clave sintética todos pasaron, sin modificar la política de
autenticación. Las pruebas SQL usan únicamente la base desechable `gym_test`.

El frontend incluye renderizado SSR de los diálogos extraídos y pruebas de flujos;
no se ejecutó una validación visual en navegador. No se hizo una prueba de carga
en Supabase ni se verificaron configuración o datos de producción. Las advertencias
de Starlette y de contexto Pinia en el arnés de pruebas no impidieron las suites.
Las pruebas de imports y la cantidad de casos aportan evidencia, no una garantía
de ausencia de errores.

## Seguimiento: responsabilidades de las vistas

La petición posterior de reducir duplicación y responsabilidades se aplicó a las
dos pantallas prioritarias identificadas en esta revisión:

| Vista | Líneas antes → después | Líneas de script antes → después |
| --- | --- | --- |
| `TrainerRoutineMonitorView.vue` | 1.173 → 443 | 429 → 96 |
| `AttendanceView.vue` | 1.111 → 169 | 289 → 66 |

La comparación usa el árbol de trabajo previo a esta extracción. La reducción de
líneas acompaña cambios concretos de responsabilidad:

- Seguimiento: composables independientes para búsqueda, asignaciones, borradores
  de progreso, mensajes y temporizador; componentes para fichas, historial,
  ejercicios y diálogos. El guardado de asignaciones se comparte entre los dos
  puntos de entrada y el temporizador tiene una sola implementación visual.
- Asistencias: componentes de resumen, búsqueda, horarios, acceso general y
  pendientes; composables de búsqueda y coordinación de escrituras. Las acciones
  usan eventos y los formularios mantienen sus modelos reactivos.

Las regresiones de [29-view-flows.test.js](../frontend/tests/29-view-flows.test.js)
verifican búsquedas reemplazadas, conservación de datos ante fallos, bloqueo de
escrituras repetidas, reutilización del ID de entrada al reintentar, asignaciones
compatibles, borradores de progreso, modelos de los diálogos, controles de
ejercicios y limpieza del temporizador. Incluyen renderizado SSR de ambas vistas
y sus componentes reales; no sustituyen una comprobación visual en navegador.

Verificación del seguimiento: **137 pruebas de frontend pasan** (nueve nuevas),
compilación Vite de producción correcta y `git diff --check` sin errores. No se
modificó el backend en esta extracción; sus resultados anteriores se conservan
como evidencia de la revisión inicial.

## Comprobación posterior en navegador y con configuración real

La [comprobación visual](comprobacion-visual.md) añade recorridos reales de
navegador con datos sintéticos en escritorio y móvil, ambos temas, y capturas sin
datos personales. Detectó y corrigió la superposición del autocompletado del
entrenador sobre el botón de búsqueda en móvil.

La conexión y las lecturas reales de Supabase funcionan, pero el alta de las
cuentas de prueba reveló un permiso de secuencia que las pruebas anteriores no
detectaban. La corrección está preparada en la migración 016 y las 15 pruebas SQL
pasan en una base aislada. Posteriormente, con las dos cuentas existentes
proporcionadas por el usuario, se completó la comprobación visual autenticada de
lecturas y diálogos contra la API real, sin guardar cambios. **La aplicación de
016 sigue pendiente para las altas de personal**; el acceso con cuentas existentes
no acredita ese despliegue ni permite afirmar que todas las altas funcionen en la
instalación.

Referencias: [arquitectura actual](arquitectura.md),
[seguimiento de correcciones](correcciones-prioritarias.md) y
[auditoría original conservada](auditoria-code-smells.md).
