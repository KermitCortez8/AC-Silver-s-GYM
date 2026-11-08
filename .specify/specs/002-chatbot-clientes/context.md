# Contexto: chatbot para clientes

Fecha: 2026-11-03. Encargo de planificación y prototipos para revisión académica, sin integración contratada ni implementación productiva.
El usuario eligió conversación con IA y acciones guiadas con reglas que las limiten.
Posteriormente pidió revisar Specs junto con prototipos navegables y capturas.
La entrega de diseño se limita a archivos locales independientes del frontend/backend.

## Base obligatoria

- [AGENTS.md](../../../AGENTS.md).
- [Constitución](../../memory/constitution.md).
- [Base implementada](../000-base-implementada/spec.md).
- [Índice de módulos](../../base/modulos/README.md).
- [Arquitectura](../../docs/arquitectura.md).
- [Diseño](../../docs/diseno.md).
- [Seguridad](../../.codex/rules/seguridad.md).
- [DoD](../../docs/DoD.md).
- [Reglas por rutas](../../.codex/settings.json).
- [Guía de referencia para chatbot](../../guias/guia-spec-driven-chatbot.md).

## Módulos afectados

- **MOD-01**: [identidad y acceso](../../base/modulos/01-identidad-acceso.md); conservar contraseña/Google, validación de sesión y acceso condicionado a activación/vigencia.
- **MOD-02**: [clientes](../../base/modulos/02-clientes.md); acompañar el formulario público existente, sin registrar datos personales dentro del chat.
- **MOD-03**: [membresías y pagos](../../base/modulos/03-membresias-pagos.md); orientar sobre pago y activación separados, sin ejecutar cobros ni activaciones.
- **MOD-04**: [planes y promociones](../../base/modulos/04-planes-promociones.md); consultar el catálogo vigente sin inventar ofertas o importes.
- **MOD-05**: [horarios y matrículas](../../base/modulos/05-horarios-matriculas.md); inscribir mediante el caso de uso existente y confirmación humana.

No se añade al inventario un módulo como implementado durante la planificación.

## Código y pruebas existentes

- [Registro público](../../../backend/presentation/routes/clients_routes.py), [composable de registro](../../../frontend/src/presentation/composables/auth/useRegistrationForm.js) y [pruebas de preregistros](../../../backend/tests/test_public_preregistrations.py).
- [Acceso](../../../backend/presentation/routes/auth_routes.py), [permisos](../../../backend/presentation/dependencies.py) y [servicio frontend](../../../frontend/src/application/services/authentication.js).
- [Catálogo público](../../../frontend/src/application/services/publicCatalog.js) y [pagos del cliente](../../../frontend/src/application/services/clientPayments.js).
- [Rutas de horarios y matrícula](../../../backend/presentation/routes/gym_routes.py), [módulo de horarios](../../../frontend/src/application/modules/schedules.js) y [composable de matrícula](../../../frontend/src/presentation/composables/enrollment/useEnrollmentWorkspace.js).
- [Pruebas de matrículas](../../../backend/tests/test_schedule_enrollment.py), [sesiones](../../../backend/tests/test_schedule_sessions.py) y [sesiones con PostgreSQL](../../../backend/tests/test_schedule_sessions_postgres.py).
- [Límite de sesión frontend](../../../frontend/src/application/services/sessionBoundary.js), [bootstrap frontend](../../../frontend/src/bootstrap.js) y [bootstrap backend](../../../backend/app/bootstrap.py).
- [Migración 019](../../../backend/migrations/019_schedule_sessions.sql) y [migración 020](../../../backend/migrations/020_public_preregistrations.sql).

## Restricciones que se deben contrastar

Separar las cuatro capas. El servidor obtiene el cliente desde la sesión. La matrícula conserva su RPC y bloqueos; una conversación no reserva cupos. Fechas en America/Lima y vigencia inclusiva. Pago confirmado no equivale a cuenta activada.

Nombre/correo conservan 50 caracteres; DNI 8 dígitos y teléfono 9. El chat no captura esos campos ni contraseñas. El mensaje usa máximo 150 caracteres y bloqueo al llegar, sin mostrar regla o contador, con validación equivalente en backend.

Historial efímero, sin persistencia al cerrar sesión. El proveedor solo recibe contexto permitido y depurado; nunca tokens, identidad, datos de pago o conversaciones ajenas. Frecuencia y presupuesto se controlan entre procesos, no solo en memoria local.

## Evaluación específica del cambio

Ya existen formularios, servicios y rutas para el recorrido. Falta una interfaz conversacional que los coordine. Se agrega panel y servicio IA acotado, reutilizando registro, acceso, Stripe y matrícula. Las herramientas del modelo serán consultas; la escritura de matrícula saldrá exclusivamente de una confirmación humana hacia el servicio existente.

La guía del chatbot es una referencia, no la especificación activa: este alcance incluye orientación pública y preregistro además de clientes autenticados. Un cliente pendiente/vencido recibe orientación pública genérica y los enlaces existentes, sin acceso privado alternativo.

Proveedor/modelo, condiciones de datos y presupuesto operativo se concretan en T001 antes de implementar el adaptador; no se contrata un proveedor por suposición. Pruebas previstas con proveedor falso y PostgreSQL aislado. No se ejecutan pagos, correos o despliegues reales.
