# Tareas: agente de atención del gimnasio

**Entrada:** [SPEC](spec.md), [contexto](context.md), [plan](plan.md), [contrato](contracts/agente-publico.md).
**Estado:** primera versión implementada; tareas abiertas reflejan límites reales.
**Formato:** ID, recorrido, ruta, criterio.

## Preparación y línea base

- [x] T001 Revisar MOD-04/MOD-05, rutas, servicios y pruebas actuales de planes/horarios en `backend/` y `frontend/`; registrar diferencias con `spec.md` (CA-01).
- [ ] T002 Registrar pruebas relacionadas antes del cambio y sus resultados reales en `validation.md`; escoger datos sintéticos y proveedor falso (CA-08).
- [x] T003 Crear la matriz requisito → caso → capa → resultado esperado → prioridad → evidencia en `validation.md`, sin fijar un número artificial de casos (CA-01–CA-08).

## Base del agente

- [x] T004 [US1] Añadir casos de prueba de planes y horarios cambiantes en `backend/tests/agente/` antes de implementar (CA-01, CA-02).
- [x] T005 [US1] Definir selección intercambiable del proveedor y herramientas cerradas; validar nombres/argumentos y limitar consultas a `GymService` (CA-01, CA-06).
- [x] T006 [US1] Implementar orquestación de consulta y respuesta factual en `backend/application/services/agent_service.py`, sin precios u horarios fijos (CA-01, CA-02).
- [x] T007 [US1] Implementar adaptador en `backend/infrastructure/services/groq_agent_provider.py` y falso de pruebas; la disponibilidad real del modelo no se ha comprobado (CA-04, CA-08).
- [x] T008 [US1] Añadir `POST /api/agente/mensajes` y registro en `backend/app/main.py` (CA-01, CA-04).
- [x] T009 [US1] Añadir transporte y panel público en `frontend/src/application/services/agentService.js` y `frontend/src/presentation/components/AgentChat.vue` (CA-01, CA-04).

## Seguridad y continuidad

- [x] T010 [US2] Probar y aplicar en `backend/domain/services/agent_policy.py` longitud de 150 caracteres, bloqueo de tarjeta/contraseña, acciones privadas y herramientas desconocidas; comprobar que no llegan al proveedor ni hacen escrituras (CA-03, CA-05, CA-06).
- [ ] T011 [US2] Definir cuota/presupuesto compartidos y almacenamiento atómico antes de llamadas reales, con prueba de límite, concurrencia y limpieza; documentar migración si se requiere (CA-06, CA-08).
- [x] T012 [US2] Probar y aplicar aislamiento de conversación en `backend/application/services/agent_service.py`, sin persistir mensajes personales (CA-07).
- [x] T013 [US1] Probar catálogos vacíos y caída del proveedor en backend; el panel muestra salida segura ante HTTP 503 (CA-02, CA-04).

## Recorrido completo y cierre

- [ ] T014 Crear y ejecutar casos funcionales Playwright de planes, clases, fallo y bloqueo de acción privada, con backend/catálogos/proveedor controlados; guardar evidencia y comandos en `validation.md` (CA-01–CA-08).
- [ ] T015 Repetir batería inicial con evidencia antes/después y ejecutar análisis de calidad; se ejecutaron pytest/frontend/Playwright, pero falta línea base previa y SonarQube (CA-01–CA-08).
- [ ] T016 Actualizar los contratos vivos MOD-04/MOD-05 y completar `validation.md`, incluyendo condiciones de una eventual prueba con proveedor real y datos controlados (CA-01–CA-08).
- [ ] T017 Revisar alcance, privacidad, arquitectura y evidencia del Definition of Done; ejecutar los validadores documentales y anotar sus resultados (CA-01–CA-08).

## Dependencias y secuencia

T001–T003 preceden a T004. T004 precede a T005–T009. T010–T013 preceden a habilitar llamadas reales. T014 requiere backend y UI integrados; T015–T017 cierran la entrega. US1 y US2 se pueden comprobar por separado con dobles de prueba, pero comparten el endpoint y su política.

## Evidencia de ejecución

| Fecha | Comando o procedimiento | Resultado | Criterios | Límites |
| --- | --- | --- | --- | --- |
| 2026-11-12 | Véase `validation.md` | pytest 44; frontend 373; Playwright 12; build aprobado | CA-01–CA-08 | Dobles de prueba; sin llamada real al proveedor. |
