# Plan de implementación: agente de atención del gimnasio

**Rama:** `levano/agenteAgente` · **Fecha:** 2026-11-12 · **SPEC:** [spec.md](spec.md) · **Contexto:** [context.md](context.md).
**Estado:** primera versión implementada; verificación real de Groq y cuota distribuida pendientes.

## Summary

En esta rama hay catálogos públicos de planes y horarios, pero no un agente integrado. Se añadirá un flujo público de solo lectura: el visitante pregunta, el backend decide entre dos herramientas autorizadas, consulta los servicios existentes, valida los datos afirmables y devuelve una respuesta segura. El proveedor inicial planificado es Groq con `openai/gpt-oss-120b`, según la referencia técnica de Rodrigo; el caso de uso no dependerá de ese proveedor para poder probarlo con un falso.

## Technical Context

| Aspecto | Decisión y evidencia |
| --- | --- |
| Lenguaje/dependencias | Backend FastAPI/Pydantic según `backend/requirements.txt`; frontend Vue 3/Vite/Pinia según `frontend/package.json`. Evaluar dependencia HTTP solo si la biblioteca actual no basta. |
| Módulos/capas | MOD-04 y MOD-05 aportan datos públicos; presentación recibe HTTP, aplicación orquesta, dominio valida herramientas/permisos, infraestructura conecta proveedor. |
| Almacenamiento | Catálogos actuales por `GymService`. Conversación temporal sin nuevos datos de negocio. Antes de llamadas reales en varias instancias, cuota compartida atómica; identificar recurso o migración necesaria durante implementación. |
| Contratos | [Contrato público propuesto](contracts/agente-publico.md); no se toca la autorización de rutas privadas. |
| UI | Panel conversacional público con carga, respuesta, error y enlaces permitidos; reutilizar navegación y servicios del frontend. |
| Integraciones | Proveedor Groq detrás de un puerto intercambiable y falso de pruebas. Confirmar acceso al modelo antes de una llamada real. Credenciales solo en backend; avisar al usuario antes de crear variables de entorno. |
| Pruebas | pytest para dominio, aplicación y ruta; pruebas frontend existentes con `npm test`; Playwright para recorrido visible; proveedor/catálogos falsos y cero pagos/correos reales. |
| Base reutilizada | [Rutas públicas y dependencias](context.md), `GymService`, catálogo frontend, validadores y estructura de cuatro capas. Código de Rodrigo solo como referencia, sin fusionarlo. |

## Constitution Check

- [x] I: el SPEC tiene siete componentes y parte de módulos reales.
- [x] II: el diseño conserva cuatro capas y reutiliza `GymService`.
- [x] III: la primera entrega no escribe datos de negocio; cuotas compartidas requieren atomicidad antes de habilitar llamadas reales.
- [x] IV: consultas públicas únicamente; backend controla herramientas y secretos.
- [x] V: precios y horarios salen de servicios actuales; no se cambian pagos, matrículas ni fechas.
- [x] VI: hay pruebas previstas por criterio y evidencia sin afirmar ejecuciones futuras.
- [x] VII: MOD-04/MOD-05 y el contrato del nuevo agente se actualizarán al implementar.

## Project Structure

Archivos propuestos; los nombres concretos pueden ajustarse a las convenciones al programar:

- `backend/presentation/routes/agent_routes.py`: entrada HTTP pública y errores.
- `backend/application/services/agent_service.py`: orquestación del turno y uso de catálogos.
- `backend/domain/services/agent_policy.py`: acciones permitidas, validación de entrada y datos afirmables.
- `backend/infrastructure/services/groq_agent_provider.py`: adaptador del modelo; falso inyectable en pruebas.
- `backend/app/main.py`: registro de la ruta.
- `frontend/src/application/services/agentService.js` y `frontend/src/presentation/components/AgentChat.vue`: transporte y panel.
- `backend/tests/agente/` y `frontend/tests/agente/`: pruebas nuevas; pruebas funcionales Playwright en el lugar acordado con la suite del repositorio.

## Diseño del cambio

1. Registrar línea base de pruebas relacionadas. Crear primero casos de comportamiento esperado para catálogos cambiantes, proveedor falso, datos sensibles, permisos, fallos y conversaciones aisladas.
2. La UI envía texto acotado. La ruta valida y el servicio de aplicación usa la política de herramientas. El proveedor puede sugerir `consultar_planes` o `consultar_horarios_publicos`; el backend valida la sugerencia y obtiene datos solo de los servicios existentes.
3. El sistema arma la parte factual desde el resultado consultado. Una salida del modelo que contradice datos reales o propone herramientas ajenas se descarta. El frontend muestra estado, texto seguro y enlaces conocidos.
4. Mantener contexto temporal aislado. Límite de mensaje 150 caracteres. Una política de cuota y presupuesto compartidos precede a activar llamadas reales con varias instancias; probar límites con reloj/controlador falso.
5. Los fallos de catálogo, modelo o red tienen salida pública segura. Las pruebas de integración sustituyen Groq, Supabase, pagos y correo. La comprobación real del proveedor se hace solo con configuración existente y datos controlados, después de revisar su aislamiento.

## Datos y migraciones

El recorrido de consulta no modifica tablas de negocio. Si la cuota compartida necesita almacenamiento nuevo, definir una migración específica y prueba de actualización atómica antes de habilitar el proveedor real; registrar el recurso y limpieza en la tarea T011. La conversación temporal no persiste mensajes personales. Ninguna migración se ejecuta en esta etapa documental.

## Verificación y trazabilidad

| Criterio | Archivos previstos | Comprobación | Evidencia esperada |
| --- | --- | --- | --- |
| CA-01, CA-02 | `agent_service.py`, `agent_policy.py` | pytest con catálogos cambiantes y proveedor falso | Solo valores del catálogo consultado. |
| CA-03, CA-06 | `agent_policy.py`, `agent_routes.py` | pytest de permisos/herramientas | Cero mutaciones y rechazo de herramientas ajenas. |
| CA-04 | `agent_service.py`, panel Vue | pytest y prueba funcional con error controlado | Mensaje de error y navegación pública disponible. |
| CA-05 | `agent_policy.py`, adaptador | pytest con datos sensibles sintéticos | Proveedor falso no recibe el contenido. |
| CA-07 | `agent_service.py` | pytest de dos conversaciones y continuación | Contexto aislado. |
| CA-08 | backend/frontend/Playwright | suites aisladas con fakes | Ejecución repetible sin efectos externos. |

## Complexity Tracking

La suite Playwright ya se ubica en `frontend/e2e/`. El cupo local por proceso se implementó para limitar pruebas y uso de una instancia; **no sustituye un límite compartido entre servidores**. Antes de exponer el proveedor real a tráfico público se requiere un cupo distribuido, revisión más amplia de datos personales y una prueba controlada de acceso a Groq. No se declara esa fase como aprobada.
