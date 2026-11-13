# Contexto: agente de atención del gimnasio

Fecha: 2026-11-12. Rama `levano/agenteAgente`, creada desde `develop`. Este documento registra fuentes y decisiones de especificación; no acredita código ni pruebas del agente.

## Base consultada

- [Reglas del repositorio](../../../AGENTS.md), [constitución](../../memory/constitution.md), [base implementada](../000-base-implementada/spec.md) e [índice de módulos](../../base/modulos/README.md).
- [Arquitectura](../../docs/arquitectura.md), [seguridad](../../.codex/rules/seguridad.md), [pruebas](../../.codex/rules/testing.md) y [DoD](../../docs/DoD.md).
- [Diseño previo del chatbot](../002-chatbot-clientes/spec.md) y su [contexto](../002-chatbot-clientes/context.md), como referencias y no como evidencia de integración terminada.

## Módulos afectados

- **MOD-04:** [planes y promociones](../../base/modulos/04-planes-promociones.md), para consultar precios y duración del catálogo público.
- **MOD-05:** [horarios y matrículas](../../base/modulos/05-horarios-matriculas.md), para consultar clases activas sin matricular en esta entrega.
- **MOD-01:** [identidad y acceso](../../base/modulos/01-identidad-acceso.md), cuyos permisos delimitan futuras consultas privadas. El primer recorrido es público.

## Código y pruebas existentes

- Planes: [ruta de membresías](../../../backend/presentation/routes/memberships_routes.py), `GET /api/planes-membresia`, y [catálogo frontend](../../../frontend/src/application/services/publicCatalog.js).
- Horarios: [ruta del gimnasio](../../../backend/presentation/routes/gym_routes.py), `GET /api/gym/horarios-publicos`.
- Acceso: [dependencias de autorización](../../../backend/presentation/dependencies.py), relevantes para una ampliación privada.
- La aplicación [registra las rutas actuales](../../../backend/app/main.py). En esta rama no se encontró una ruta o servicio del agente.
- Reutilizar las pruebas del catálogo y horarios indicadas en MOD-04 y MOD-05; añadir casos del nuevo recorrido con proveedor y datos de prueba.

## Diferencia solicitada y límites

El SPEC `002-chatbot-clientes` define recorridos y prototipos, pero declara pendiente la integración productiva. El usuario pidió un SPEC nuevo para desarrollar un agente. La propuesta inicial verificable es consultar datos públicos reales mediante herramientas limitadas del backend y responder en la interfaz.

El código y SPEC de Rodrigo viven en otra rama y se usan **solo como referencia**, por indicación expresa del usuario. No se incorporan automáticamente. Sus diferencias con el diseño anterior requieren acuerdo si afectan la implementación.

La primera entrega queda fijada como consulta pública de planes y horarios. El plan selecciona la integración técnica; las acciones adicionales requieren un alcance posterior. No se crean variables de entorno sin avisar al usuario. Antes de flujos reales se aíslan pagos, correos y servicios externos, usando datos de prueba.

## Comprobaciones previstas

Preparar matriz por criterio, registrar estado inicial, probar reglas con proveedor falso, probar consultas contra servicios controlados y verificar el recorrido de interfaz. Al implementar, ejecutar pruebas y validadores proporcionales del DoD y registrar resultados reales.
