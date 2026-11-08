# Plan de implementación: chatbot para clientes

**Fecha:** 2026-11-03 · **Feature:** `002-chatbot-clientes` · **Rama de trabajo conservada:** `feat/refeat`.
**Entradas:** [spec](spec.md), [contexto consultado](context.md) y contratos MOD-01 a MOD-05.
**Estado:** planificación completa; implementación pendiente. No se ha elegido ni contratado proveedor.

## Entrega de diseño para revisión

El usuario pidió revisar Specs y prototipos, en formato navegable y en imágenes.
Se continúa esta misma feature con [tres ECU](casos-de-uso.md), un
[prototipo local](prototipos/index.html) y la [matriz de trazabilidad](revision-prototipos.md).
Los archivos HTML/CSS/JS están en `prototipos/`; no se agrega una ruta pública o
servicio al producto ni se conecta proveedor alguno. Los resultados de esta
revisión se registran en `prototipos/validation.md`; las tareas productivas siguen abiertas.

Verificación de esta entrega: navegación, formularios, alternativas, confirmación,
reinicio/limpieza y límites en navegador; capturas de escritorio/móvil y validación
documental. Las ocho tareas resumidas del encargo están en la matriz de revisión;
`tasks.md` conserva sus 24 pasos técnicos de implementación.

## Summary

Agregar conversación IA en español con acciones guiadas sobre el recorrido que ya existe. La interfaz acompaña preregistro/acceso y permite buscar sesiones y confirmar matrícula propia. El modelo dispone únicamente de consultas acotadas. La escritura la inicia el usuario, desde una tarjeta canónica, reutilizando la matrícula actual.

Primer incremento: panel público con IA, catálogo real, enlaces a formularios y alternativa guiada. Segundo: continuidad de sesión privada. Tercero: horarios y matrícula confirmada.

## Technical Context

| Aspecto | Decisión y evidencia |
| --- | --- |
| Stack | Vue 3, Pinia 3, Vite 8; FastAPI, Pydantic 2 y Supabase actuales, sin cambiar versiones por este trabajo. |
| Capas | Presentación valida HTTP/UI; aplicación coordina conversación y consultas; dominio define políticas; infraestructura implementa proveedor y cuotas. |
| Almacenamiento | Historial en memoria de pestaña. Solo cuotas técnicas persistidas, con RPC atómica y RLS; no tabla de conversaciones. |
| Contratos | Dos endpoints de conversación, público y privado. Esquemas cerrados en [contrato](contracts/asistente.md). Matrícula conserva su endpoint. |
| UI | Panel flotante en páginas del recorrido, tarjetas de acciones y estados de carga/error/confirmación. Fuera de vistas administrativas y de entrenador. |
| Integración | Puerto `ChatProvider`; adaptador y configuración se concretan en T001 con documentación oficial vigente del proveedor. Fake determinista para pruebas. |
| Pruebas | Servicios/rutas, proveedor falso, sesión frontend y concurrencia PostgreSQL; escenarios [E1–E9](quickstart.md). |
| Reutilización | `publicCatalog`, registro/login, `sessionBoundary`, módulo de horarios, `GymService` y RPC existente de matrícula. Fuentes en [contexto](context.md). |

## Constitution Check

Comprobaciones de diseño; no acreditan implementación.

- [x] I: spec con siete componentes, nueve CA y alcance solicitado.
- [x] II: cuatro capas, adaptadores por bootstrap y flujos existentes reutilizados.
- [x] III: no se duplica identidad; matrícula mantiene su operación atómica; cuotas usan RPC técnica propia.
- [x] IV: identidad/permisos en servidor y herramientas sin escritura; separación público/privado.
- [x] V: sin cambios de importes, pagos o activación; fechas de clase Lima y reconciliación de matrícula.
- [x] VI: escenarios por CA, proveedor falso y PostgreSQL aislado sin llamadas externas.
- [x] VII: actualizar contratos afectados únicamente después de verificar la implementación.

## Project Structure

Rutas nuevas propuestas, todavía inexistentes salvo los documentos de esta feature:

- Backend: `backend/domain/services/chatbot_policy.py`, `backend/application/ports/chat_provider.py`, `backend/application/ports/chat_quota.py`, `backend/application/services/chatbot_service.py`, `backend/application/services/chatbot_queries.py`.
- Infraestructura/presentación: `backend/infrastructure/services/chat_provider.py`, `backend/infrastructure/repositories/chat_quota_repository.py`, `backend/presentation/chatbot_schemas.py`, `backend/presentation/routes/chatbot_routes.py`.
- Cuotas: `backend/migrations/021_chatbot_quotas.sql`, `backend/app/chatbot_maintenance.py`.
- Ensamblaje existente: `backend/app/bootstrap.py`, `backend/app/main.py`, `backend/presentation/dependencies.py`.
- Frontend: `frontend/src/application/services/chatbot.js`, `frontend/src/application/stores/chatbotStore.js`, `frontend/src/presentation/composables/chatbot/useChatbot.js`, `frontend/src/presentation/components/chatbot/ChatbotPanel.vue`, `frontend/src/presentation/components/chatbot/ChatbotActionCard.vue`.
- Integración existente: `frontend/src/bootstrap.js`, `frontend/src/App.vue`, `frontend/src/presentation/router/index.js`, `frontend/src/application/services/sessionBoundary.js` y `frontend/src/presentation/composables/enrollment/useEnrollmentWorkspace.js`.
- Pruebas nuevas: `backend/tests/test_chatbot_service.py`, `backend/tests/test_chatbot_routes.py`, `backend/tests/test_chatbot_quota_postgres.py`, `frontend/tests/chatbot.test.js`.

## Diseño del cambio

1. **Entrada y contexto.** Panel disponible en landing, registro, login, retorno de pago y área cliente (incluidas Matrícula y Mi horario). Máximo 150 caracteres con bloqueo al llegar, sin contador/regla visible. Etiqueta accesible, foco y estado de carga. No cubrir botones del formulario. Rutas de acciones obtenidas de una lista interna; sin navegación a URLs emitidas por IA.
2. **IA limitada por código.** Validar cuerpo/esquema y filtrar datos sensibles antes de llamar. Instrucciones del sistema controladas por servidor y datos del catálogo tratados como contenido no confiable. Herramientas enumeradas, argumentos tipados, máximo tres lecturas y dos llamadas al modelo por turno. Ninguna herramienta escribe en negocio. Rechazar salida desconocida, ID inexistente o texto que anuncie un éxito no respaldado. Confirmaciones y errores de negocio se redactan desde la aplicación.
3. **Registro/acceso.** IA explica pasos y abre formularios originales; no recibe campos personales ni credenciales, no llama Stripe, no promete activación. Puede preseleccionar un plan validado sin alterar precio/promoción. Retorno de pago conserva la confirmación existente, fuera del chat. Pendiente/vencido obtiene orientación genérica; no se crea consulta pública de estado por DNI/correo.
4. **Sesión privada.** Endpoint privado usa `require_roles('user')` y la validación existente. ID de cliente del servidor, nunca del prompt. La consulta de inscripciones produce tarjeta local; datos privados no entran al contexto del proveedor. Cada cambio de sesión aborta peticiones y descarta resultados por revisión de sesión; memoria y acciones se vacían. Un 401/403 no reenvía automáticamente historial al endpoint público.
5. **Búsqueda y propuesta.** Pedir fecha/servicio cuando falten; resolver fechas relativas con reloj Lima y mostrar fecha absoluta. Recargar sesión concreta y contrastar datos reales. La tarjeta muestra servicio, fecha, hora y disponibilidad orientativa. No hay reserva de cupo. Propuesta válida cinco minutos; recargar si caduca o cambian datos.
6. **Confirmación.** Solo el clic en Confirmar matrícula invoca la capacidad existente de inscripción, con horario/fecha; el backend impone cliente de sesión, permisos y reglas actuales. No exponer esta mutación como herramienta del modelo. Bloquear botón en curso; revalidar al confirmar. Ante timeout, consultar matrículas propias para esa sesión; si no se puede verificar, estado pendiente y sin reintento automático. Duplicados se reconocen mediante backend y lectura propia; dos clientes por último cupo mantienen la RPC actual.
7. **Límites operativos.** Valores iniciales configurables: mensaje 150 caracteres; historial ocho mensajes depurados; cuerpo 8 KiB; 2.000 tokens de entrada y 256 de salida por llamada; dos llamadas/tres consultas por turno; respuesta hasta 600 caracteres/tres acciones. Público 10 turnos/10 min/IP, privado 20/10 min/cliente, una solicitud simultánea por sujeto y timeout total de 15 s. Reservar coste máximo antes de cada llamada usando presupuesto diario obligatorio; coordinar cuotas entre instancias y fallar hacia guía local. No reintentar automáticamente llamadas al proveedor.
8. **Privacidad y operación.** Sin historial persistido o logs de texto, tokens, PII o argumentos privados. Métricas: request ID opaco, duración, estado, códigos de límite y consumo/coste agregado. Distinguir desactivado, límite agotado y proveedor fallido para mostrar orientación breve. El apagado conserva todos los formularios. Ver [decisiones y limitaciones](research.md).

## Datos y migraciones

Nueva tabla técnica/RPC, descrita en [modelo](data-model.md), sin cambios en tablas de clientes o matrículas. Nombre previsto `021_chatbot_quotas.sql`: confirmar disponibilidad del número antes de implementarla. Documentar como dependencias el esquema de roles y recursos de la instalación y las migraciones de negocio presentes, sin ejecutar todos los SQL alfabéticamente.

Reserva y liquidación idempotentes con locks de sujeto y presupuesto global, timestamps UTC, claves HMAC y leases. Revocar acceso de roles públicos/anónimos; RLS y RPC solo para backend, `search_path` fijo y privilegios mínimos. El adaptador de memoria solo vale para pruebas, no como sustituto de cuotas distribuidas en producción.

Prueba aislada de permisos, carreras entre dos instancias, timeout, ausencia de consumo y limpieza. Recuperación: deshabilitar IA, conservar formularios y retirar únicamente tabla/RPC técnica tras resolver reservas; nunca borrar datos de negocio. El mantenimiento purga ventanas caducadas y no requiere una migración de conversaciones.

## Verificación y trazabilidad

| Criterio | Área prevista | Escenario | Tareas |
| --- | --- | --- | --- |
| CA-01 | Esquemas, servicio y panel | E1 de [guía](quickstart.md) | T002, T005–T009, T012 |
| CA-02 | Catálogo y navegación | E2 de [guía](quickstart.md) | T010–T012 |
| CA-03 | Rutas, stores y sesión | E3 de [guía](quickstart.md) | T007, T008, T013–T015 |
| CA-04 | Consultas y tarjetas | E4 de [guía](quickstart.md) | T016, T017, T020, T021 |
| CA-05 | Confirmación y matrícula actual | E5 de [guía](quickstart.md) | T018, T020, T021 |
| CA-06 | Estados/reconciliación | E6 de [guía](quickstart.md) | T019–T021 |
| CA-07 | Política, esquemas y herramientas | E7 de [guía](quickstart.md) | T002, T006, T007, T012, T015, T020, T022 |
| CA-08 | Cuotas, proveedor y límites | E8 de [guía](quickstart.md) | T001–T006, T009, T010, T012, T022, T023 |
| CA-09 | Accesibilidad y degradación | E9 de [guía](quickstart.md) | T009, T010, T021, T023, T024 |

Comandos y evidencia esperada en [quickstart](quickstart.md). En esta fase solo se validan documentos y sus prerrequisitos; las suites de producto se ejecutan al implementar.

## Complexity Tracking

Sin excepciones a la constitución. La cuota compartida añade una migración técnica para limitar abuso/gasto entre procesos, evitando un contador local ineficaz. No se añade base vectorial ni historial persistente. T001 concreta proveedor/modelo, tokenizer/tarifas, condiciones de retención y presupuesto antes de construir el adaptador; no se presuponen precios ni compatibilidad externos. La revisión inicial de disponibilidad de IA no implica un despliegue.
