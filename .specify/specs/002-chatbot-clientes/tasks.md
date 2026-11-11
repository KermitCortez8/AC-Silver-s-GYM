# Tareas: chatbot para clientes

**Estado:** 24 tareas de integración productiva pendientes. Entrega actual: Specs y prototipos de diseño.
La entrega adicional de diseño se consulta en [Specs y prototipos](revision-prototipos.md):
tres ECU, ocho tareas resumidas y prototipos navegables/capturas. Ese avance no
completa automáticamente estas tareas de integración productiva.
**Entradas:** [spec](spec.md), [plan](plan.md), [contexto](context.md), [modelo](data-model.md), [contrato](contracts/asistente.md) y [escenarios](quickstart.md).
Antes de código: `python .specify/.codex/hooks/validate.py --feature 002-chatbot-clientes --stage implement`.
Todas las rutas de producto nuevas son propuestas; comprobar convenciones vigentes al implementarlas.

## Preparación

- [ ] T001 Contrastar base y seleccionar proveedor/modelo en `.specify/specs/002-chatbot-clientes/research.md` usando documentación oficial vigente; documentar SDK o transporte, salida estructurada, tokenizer, tarifas/cota máxima, timeout/cancelación y tratamiento/retención de datos. Concretar presupuesto diario y configuración backend, conservando IA apagada por defecto; sin contratar o efectuar llamadas reales. CA-07, CA-08.

## Base compartida

- [ ] T002 Definir política en `backend/domain/services/chatbot_policy.py`, contratos de aplicación y esquemas en `backend/presentation/chatbot_schemas.py`: mensaje no vacío máximo 150 caracteres Unicode, historial máximo ocho mensajes (usuario 150/asistente 600), cuerpo 8 KiB, contexto enum sin campos extra, IDs positivos y fecha ISO. Salida máximo 600 caracteres/tres acciones tipadas, lista cerrada, sin roles system/tool aportados por cliente. CA-01, CA-07, CA-08.
- [ ] T003 Crear `backend/migrations/021_chatbot_quotas.sql` y pruebas `backend/tests/test_chatbot_quota_postgres.py`; comprobar número/dependencias, documentar recuperación y probar reserva/liquidación idempotentes, locks de sujeto/global, RLS y RPC exclusivamente backend, `search_path` fijo, limpieza y concurrencia real entre dos conexiones. Sin modificar recursos de negocio. CA-08.
- [ ] T004 Implementar puerto `backend/application/ports/chat_quota.py` y adaptador `backend/infrastructure/repositories/chat_quota_repository.py`: público 10 turnos/10 min/IP confiable transformada por HMAC; privado 20/10 min/cliente transformado por HMAC; un turno simultáneo por sujeto. Valores configurables, leases, limpieza y reserva previa de coste máximo por llamada; sin consumo fiable conservar reserva. Fallar cerrado si faltan presupuesto positivo/tarifas o RPC. Fake en memoria solo para pruebas. CA-07, CA-08.
- [ ] T005 Implementar `backend/application/ports/chat_provider.py` y `backend/infrastructure/services/chat_provider.py`, ensamblar en `backend/app/bootstrap.py`: proveedor elegido en T001, fake determinista, máximo 2.000 tokens de entrada/256 de salida por llamada, dos llamadas por turno y timeout total 15 s sin reintentos automáticos. Cancelar solicitud local pendiente sin asumir cancelación del cobro externo; mantener reserva conservadora ante resultado incierto. Secretos solo backend. CA-01, CA-08.
- [ ] T006 Implementar `backend/application/services/chatbot_service.py`: depuración de entrada/historial y contexto mínimo, detección de patrones sensibles con guía local, instrucciones de servidor, registro cerrado de herramientas de lectura (máximo tres), salida validada y rechazo de IDs inventados. Ninguna capacidad de cobro/activación/escritura/SQL/HTTP arbitrario disponible al modelo. No retornar datos privados al proveedor ni interpretar contenido del catálogo como instrucciones. CA-01, CA-07, CA-08.
- [ ] T007 Exponer `backend/presentation/routes/chatbot_routes.py`, registrar en `backend/app/main.py` y conectar dependencias en `backend/presentation/dependencies.py`: endpoints público/privado del contrato, rol user y dueño de servidor, body cap real antes de procesar, errores 401/403/413/422/429 y guía local ante proveedor caído. No degradar solicitudes privadas a públicas. CA-01, CA-03, CA-07, CA-08.
- [ ] T008 Crear servicio/store frontend en `frontend/src/application/services/chatbot.js` y `frontend/src/application/stores/chatbotStore.js`, inyectados en `frontend/src/bootstrap.js`; memoria solo de pestaña, ocho mensajes depurados, descarte de respuestas por revisión de sesión y estados explícitos. Sin localStorage, historial persistente ni acceso directo desde UI al proveedor. CA-01, CA-03, CA-07.

## US1 · Orientación pública y preregistro

Objetivo verificable: conversar sin sesión y llegar al formulario con un plan real, sin consultas privadas ni cobros desde el chat. Escenarios E1, E2, E7 y E8.

- [ ] T009 [US1] Crear `frontend/src/presentation/components/chatbot/ChatbotPanel.vue`, `ChatbotActionCard.vue` y `frontend/src/presentation/composables/chatbot/useChatbot.js`; montar en `frontend/src/App.vue` con páginas permitidas desde router. Campo máximo 150 caracteres al escribir/pegar, sin regla/contador visible; renderizar texto sin HTML, carga/error y hasta tres acciones. Teclado, foco restaurado, lector de pantalla y tamaños móvil/escritorio. CA-01, CA-08, CA-09.
- [ ] T010 [US1] Añadir guía local y acciones seguras a `frontend/src/presentation/composables/chatbot/useChatbot.js` y `backend/application/services/chatbot_service.py`: proveedor apagado/sin configurar, JSON inválido, timeout o presupuesto agotado mantienen enlaces al recorrido original. Fuera de alcance recibe orientación breve; fallo del panel nunca bloquea formularios. CA-01, CA-07, CA-08, CA-09.
- [ ] T011 [US1] Implementar consultas públicas acotadas en `backend/application/services/chatbot_queries.py` mediante capacidades existentes y navegación frontend en `frontend/src/presentation/composables/chatbot/useChatbot.js`; contrastar catálogo y rutas existentes, preseleccionar solo plan vigente y abrir registro/acceso sin capturar PII ni llamar pagos. Mantener nombre/correo 50, DNI 8 y teléfono 9 en formularios; distinguir pago confirmado de activación. CA-02, CA-07.
- [ ] T012 [US1] Cubrir E1/E2/E7/E8 en `backend/tests/test_chatbot_service.py`, `backend/tests/test_chatbot_routes.py` y `frontend/tests/chatbot.test.js`: esquema, herramientas desconocidas, IDs falsos, prompt injection, centinelas PII/secretos en payload/logs, planes agotados, 150/151 caracteres, cuotas y alternativa guiada. Fake sin red externa. CA-01, CA-02, CA-07, CA-08.

## US2 · Acceso y continuidad de sesión

Objetivo verificable: ingresar usando acceso existente, preservar privacidad propia y borrar todo al cambiar sesión. Escenario E3, además del recorrido público anterior.

- [ ] T013 [US2] Integrar el panel con `frontend/src/application/services/sessionBoundary.js`, `frontend/src/application/stores/chatbotStore.js` y `frontend/src/presentation/composables/chatbot/useChatbot.js`: abortar peticiones, vaciar historial/propuestas y descartar respuestas de sesión anterior en login/logout/expiración. No reenviar historial privado a público después de 401/403. CA-03, CA-07.
- [ ] T014 [US2] Completar orientación de acceso/activación en `backend/application/services/chatbot_service.py` y `frontend/src/presentation/composables/chatbot/useChatbot.js` reutilizando los formularios: cuenta pendiente/vencida recibe guía pública genérica tras limpiar contexto; no hay lookup por DNI/correo ni bypass de `get_current_user`. Contraseña y Google permanecen en el flujo actual. CA-02, CA-03, CA-07.
- [ ] T015 [US2] Ampliar `backend/tests/test_chatbot_routes.py` y `frontend/tests/chatbot.test.js` con cambio A→B, cierre con respuesta tardía, sesión vencida, pendiente, rol no permitido e IDs ajenos en cuerpo/herramientas. Verificar ausencia de datos privados en respuestas, historial y proveedor. CA-03, CA-07.

## US3 · Horarios y matrícula confirmada

Objetivo verificable: buscar una sesión concreta, confirmar y verla en Mi horario sin duplicados ni promesas de cupo. Escenarios E4 a E6.

- [ ] T016 [US3] Implementar búsqueda de sesiones y solicitud de inscripciones propias en `backend/application/services/chatbot_queries.py`, reutilizando capacidades de `GymService`: reloj America/Lima, fecha concreta y servicio no ambiguo, calendario/vigencia vigentes; backend deriva cliente. Tarjetas privadas fuera del contexto del modelo, sin escritura ni reserva de cupo al consultar. CA-03, CA-04, CA-07.
- [ ] T017 [US3] Completar tarjetas en `frontend/src/presentation/components/chatbot/ChatbotActionCard.vue` y estado en `frontend/src/application/stores/chatbotStore.js`: fecha ISO visible como fecha absoluta, servicio/hora y disponibilidad de API; selección ligada a sesión con caducidad de cinco minutos, recarga si cambia/caduca y confirmación separada. CA-04, CA-05.
- [ ] T018 [US3] Conectar botón Confirmar matrícula desde `frontend/src/presentation/composables/chatbot/useChatbot.js` a la capacidad existente usada por `frontend/src/presentation/composables/enrollment/useEnrollmentWorkspace.js` y módulo de horarios; extraer coordinación compartida si hace falta sin duplicar reglas. Solo clic humano inicia POST; mantener dueño/validación/RPC backend y refrescar inscripciones/Mi horario. CA-05.
- [ ] T019 [US3] Implementar estados enviando/verificada/rechazada/por_reconciliar en `frontend/src/application/stores/chatbotStore.js` y `useChatbot.js`: bloqueo de doble clic, error real de cupo/vigencia, y lectura de inscripciones propias tras pérdida de respuesta antes de ofrecer reintento. Si no se verifica, no anunciar éxito ni repetir automáticamente. CA-06.
- [ ] T020 [US3] Ampliar `backend/tests/test_chatbot_service.py`, `backend/tests/test_chatbot_routes.py` y las pruebas vigentes `backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py`: fechas límite Lima, consultas solo propias, fecha fuera de vigencia, duplicado y dos clientes por último cupo. Reutilizar pruebas que ya demuestren reglas; añadir solo huecos reales. CA-04, CA-05, CA-06, CA-07.
- [ ] T021 [US3] Completar `frontend/tests/chatbot.test.js` con resumen canónico, propuesta sin POST, confirmación explícita, cinco minutos/cambio de sesión, doble clic, resultado perdido/reconciliado y actualización de Mi horario. Comprobar errores de matrícula sin depender del texto del modelo. CA-04, CA-05, CA-06, CA-09.

## Cierre y verificación

- [ ] T022 Documentar/configurar feature flag, límites, claves privadas, tarifas y presupuesto; añadir métricas sin texto/PII/secretos y comando `backend/app/chatbot_maintenance.py` para purgar cuotas vencidas según `data-model.md`. Registrar instrucciones en `.specify/specs/002-chatbot-clientes/quickstart.md` y comentarios de configuración del proyecto; no modificar README principal. IA permanece apagada si falta configuración o cuota compartida. CA-07, CA-08.
- [ ] T023 Ejecutar E1–E9 de `.specify/specs/002-chatbot-clientes/quickstart.md`, suites afectadas frontend/backend, PostgreSQL con pruebas nuevas sin omitir y build. Revisar UI a 360 px/escritorio con teclado y proveedor apagado; registrar comandos/resultados y límites reales en `.specify/specs/002-chatbot-clientes/validation.md`. CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-07, CA-08, CA-09.
- [ ] T024 Revisar todos los CA y completar contratos realmente afectados de `.specify/base/modulos/01-identidad-acceso.md` a `05-horarios-matriculas.md`, más arquitectura/diseño si cambian; crear contrato de asistente en el inventario solo tras implementar. Actualizar evidencia de esta feature y ejecutar validadores global/cierre y pruebas `.specify/tests`. No publicar, desplegar, cobrar o enviar correos. CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-07, CA-08, CA-09.

## Dependencias y secuencia

T001 → T002 → T003/T004/T005 → T006/T007/T008 → US1 (T009–T012) → US2 (T013–T015) → US3 (T016–T021) → cierre (T022–T024).
T004 depende de T003; T005 depende de T001/T002. T006 depende de T004/T005, T007 de T006 y T008 del contrato T007. En US3, T018 depende de T016/T017 y T019 de T018.

Ejecución en esta sesión sin agentes adicionales. Sin marcadores de paralelismo porque varias tareas comparten archivos/decisiones. Tras cerrar T002 pueden prepararse conceptualmente proveedor (T005) y cuota SQL (T003) de forma independiente; no iniciar integración hasta satisfacer sus dependencias.

## Entrega incremental

1. MVP público: T001–T012, conversación acotada, datos reales, preregistro/acceso y degradación guiada; no inscribe aún.
2. Continuidad segura: T013–T015, sesión y privacidad.
3. Recorrido completo: T016–T024, consulta/confirmación, concurrencia y verificación.

Resumen: preparación 1, base 7, US1 4, US2 3, US3 6 y cierre 3 = 24 tareas. No hay tareas marcadas como hechas porque ninguna implementación está autorizada en esta entrega.

## Evidencia de ejecución

No ejecutada para el producto. La validación documental de este encargo se informa por separado y no completa estas tareas.
