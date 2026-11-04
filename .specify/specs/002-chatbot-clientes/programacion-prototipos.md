# Programación contemplada en los prototipos

Las cinco tareas de programación acordadas determinan las interacciones del
prototipo y su integración posterior. Este documento complementa las tres
[ECU](casos-de-uso.md), la [Spec](spec.md) y el [plan técnico](plan.md).

## PG01 · Programar las reglas de control

**Pantallas:** P01–P10; transversal a los tres casos de uso.

**Demostrado localmente:** nombres/correos de hasta 50 caracteres; DNI de 8
dígitos y teléfono de 9; mensaje máximo 150 sin contador; acciones delimitadas;
confirmación separada del chat; bloqueo local de doble clic; limpieza al salir.

**Código del prototipo:** [formularios y control de acciones](prototipos/prototipo.js)
y [campo de conversación](prototipos/index.html).

**Programación del producto:** repetir la validación en el servidor, derivar
cliente/rol desde sesión, limitar frecuencia y presupuesto entre instancias y
preservar las RPC existentes. Un bloqueo visual no sustituye estos controles.

**Criterios:** CA-03, CA-05, CA-06, CA-07, CA-08.

## PG02 · Integrar la IA en el backend

**Pantallas:** conversación de P01–P10 y alternativa «IA no disponible».

**Demostrado localmente:** mensajes, sugerencias permitidas y continuidad con
botones ante indisponibilidad. Las respuestas se seleccionan por reglas fijas;
no hay un proveedor de IA conectado.

**Programación del producto:** implementar el puerto/adaptador de proveedor,
salida estructurada, consultas permitidas, contexto mínimo, timeout y reserva de
presupuesto. Los datos de negocio y las confirmaciones provienen del sistema.
Las claves se configuran en backend; el modelo no recibe herramientas de escritura.

**Criterios:** CA-01, CA-07, CA-08.

## PG03 · Programar la interfaz del chatbot

**Pantallas:** las diez pantallas y sus versiones de escritorio/móvil.

**Demostrado localmente:** navegación, formularios, conversación, botones,
tarjetas de planes/sesiones, confirmación, errores y estados de carga.

**Código del prototipo:** [HTML](prototipos/index.html),
[estilos](prototipos/estilos.css) e [interacciones](prototipos/prototipo.js).

**Programación del producto:** trasladar el diseño a componentes Vue y composables,
con estado por sesión en Pinia e inyección mediante el bootstrap. Separar
presentación, aplicación, dominio e infraestructura y mantener el comportamiento
del recorrido existente. Los controles de revisión académica quedan fuera de la UI del cliente.

**Criterios:** CA-01, CA-03, CA-09.

## PG04 · Conectar preregistro y acceso

**Pantallas:** P01–P06; CU-CHAT-01 y CU-CHAT-02.

**Demostrado localmente:** selección de plan, formulario con datos de ejemplo,
continuidad al pago, ingreso simulado, cuenta pendiente, membresía vencida y salida.

**Programación del producto:** reutilizar catálogo, formulario de registro,
Stripe, acceso con contraseña/Google y validación de sesión existentes. La
solicitud, el pago y la activación mantienen estados distintos. El chat orienta
y abre formularios; no crea cuentas activas por una respuesta conversacional.

**Criterios:** CA-02, CA-03, CA-07.

## PG05 · Conectar horarios y matrícula

**Pantallas:** P07–P10; CU-CHAT-03.

**Demostrado localmente:** servicio y fecha, consulta de ejemplo, resumen,
confirmación explícita, inscripción local única, cupo agotado y reconciliación
simulada de respuesta perdida. Buscar o escribir «confirma» no matricula.

**Programación del producto:** consultar sesiones reales en America/Lima;
usar la capacidad actual de matrícula tras el clic de confirmación; revalidar
identidad, vigencia, cupo y duplicidad en backend; refrescar Mi horario y
reconciliar respuestas inciertas antes de permitir reintentos. Conservar la RPC
especializada y sus bloqueos frente a concurrencia real.

**Criterios:** CA-04, CA-05, CA-06, CA-07.

## Correspondencia para la exposición

| Caso de uso | Programación asociada | Qué mostrar |
| --- | --- | --- |
| CU-CHAT-01 · Preregistro | PG01, PG02, PG03, PG04 | Plan, conversación, formulario y continuidad al pago |
| CU-CHAT-02 · Acceso | PG01, PG02, PG03, PG04 | Formulario, restricciones de cuenta y limpieza al salir |
| CU-CHAT-03 · Horarios/matrícula | PG01, PG02, PG03, PG05 | Consulta, confirmación y alternativas ante fallos |

La barra «Programación asociada» del prototipo muestra esta correspondencia.
El PDF incluye este documento. Las 24 tareas de [tasks.md](tasks.md) son el
desglose técnico para ejecutar las cinco tareas; permanecen pendientes de
integración. Las comprobaciones del prototipo validan su navegación local.
