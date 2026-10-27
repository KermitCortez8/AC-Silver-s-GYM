<!--
Sync Impact Report: 1.1.0 → 1.1.1 (PATCH).
Reubicación de SDD en sdd/ y ajuste de referencias; principios y módulos conservados.
Sin cambios en plantillas o skills oficiales ni pendientes de contenido.
-->
# Constitución de AC Silver's GYM

## Principios

### I. Respetar las cuatro capas

Backend y frontend conservan presentación, aplicación, dominio e infraestructura.
El dominio expresa reglas; la aplicación coordina casos de uso; infraestructura
implementa adaptadores; presentación traduce HTTP o muestra la interfaz.
No introducir HTTP ni almacenamiento del navegador en vistas o reglas; no
importar FastAPI o infraestructura desde dominio o aplicación backend.
La evidencia son los tests de límites de arquitectura existentes.

### II. Mantener contratos y reglas del negocio

Conservar endpoints, estados HTTP, códigos de negocio, identidades y permisos,
salvo que la especificación del cambio describa expresamente su modificación.
Declarar antes de implementar cualquier cambio de contrato o migración, sus
efectos sobre consumidores y cómo desplegarlo y recuperarse si falla.
Conservar las invariantes de pagos, cupos, stock y asistencia; una prueba en
memoria no demuestra atomicidad ni concurrencia SQL.

### III. Especificar resultados y errores observables

Cada cambio funcional define escenarios, criterios con IDs estables y efectos
sobre los datos antes de cambiar código. Distinguir operación confirmada,
rechazada, sin confirmación y guardado confirmado con recarga fallida.
No publicar éxito con respuestas inválidas, borrar borradores ante un fallo ni
reintentar escrituras automáticamente. No exponer secretos en respuestas.
Cancelar la espera de una escritura enviada no demuestra reversión del servidor.

### IV. Verificar con evidencia proporcional al cambio

Reutilizar pytest, node:test, compilación y CI existentes. Para una regla nueva
o una regresión, añadir primero el escenario que falta y comprobar su fallo antes
de corregirlo. No crear tests redundantes para documentación o formato.
Relacionar cada criterio afectado con evidencia concreta; registrar comandos,
revisión evaluada, resultados, omisiones y límites. Una tarea sin demostrar
permanece abierta. Ejecutar PostgreSQL aislado cuando cambien transacciones o SQL.

### V. Adoptar SDD de forma incremental

Una especificación por cambio acotado, con el menor diseño necesario.
Reutilizar arquitectura y dependencias existentes. No reconstruir toda la
aplicación ni reescribir su historia para adoptar la herramienta.
Mantener las specs como contratos vivos: al cambiar una regla, actualizar su
especificación y reconciliar plan, tareas y evidencia en la misma entrega.

## Módulos funcionales y relaciones

El proyecto contiene los siguientes módulos funcionales. Este mapa sirve de
contexto compartido al especificar, planificar e implementar cambios. Un módulo
puede abarcar varias vistas y servicios; la cantidad de módulos no obliga a
crear la misma cantidad de ventanas o accesos de menú.

### Catálogo de módulos existentes

| Módulo | Responsabilidad | Referencias principales en el código |
| --- | --- | --- |
| Registro | Preregistro público, alta administrativa y continuación del proceso de pago y activación del cliente. | `RegisterView.vue`, `PaymentView.vue`, `clients_routes.py`. |
| Autenticación y usuarios | Acceso con contraseña o Google, sesión, perfiles, roles y administración de cuentas. | `LoginView.vue`, `UsersView.vue`, `auth_routes.py`, `users_routes.py`. |
| Clientes | Directorio, búsqueda, datos personales y consulta de membresías y acciones de la ficha del cliente. | `ClientsView.vue`, `clients.js`, `clients_routes.py`. |
| Planes y membresías | Catálogo de planes, duración y precio; membresías del cliente, vigencia y estados. | `MembershipPlansView.vue`, `memberships.js`, `memberships_routes.py`. |
| Promociones | Descuentos y condiciones vinculadas a planes, fechas y cupos aplicables. | `PromotionsView.vue`, `promotions_routes.py`. |
| Horarios | Horarios de servicio, disponibilidad y cupos para organizar la atención y las actividades. | `ServiceSchedulesView.vue`, `schedules.js`, `gym_routes.py`. |
| Matrículas | Inscripción y baja del cliente en horarios de servicio, con comprobación de membresía y cupos. | `EnrollmentView.vue`, `gym_routes.py`, `schedules.py`. |
| Entrenador y rutinas | Resumen del entrenador, catálogo de rutinas, asignación a matrículas y seguimiento del progreso. | `TrainerOverviewView.vue`, `TrainerRoutinesView.vue`, `TrainerRoutineMonitorView.vue`, `trainer_routes.py`. |
| Asistencias | Entradas y salidas generales o por horario, aforo, correcciones e historial del cliente. | `AttendanceView.vue`, `UserAttendanceView.vue`, `attendance.js`, `attendance_routes.py`. |
| Inventario | Artículos y equipos, categorías, ubicación, estado operativo, stock de reserva y movimientos de entrada, salida o ajuste. | `InventoryView.vue`, `InventoryMovementsPanel.vue`, `InventoryDestinationPanel.vue`, `inventory_routes.py`. |
| Tienda | Productos e imágenes, precios, disponibilidad, carrito y proceso de compra. | `StoreView.vue`, `StorePaymentView.vue`, `store.js`, `store_routes.py`. |
| Pedidos y ventas | Registro y consulta de pedidos, estados, entrega, cancelación y consulta de salidas por venta. | `OrdersView.vue`, `StoreMovementsPanel.vue`, `store_routes.py`. |
| Pagos | Historial de pagos de membresía, confirmación manual o mediante Stripe y coordinación de pagos de pedidos. | `MembershipPaymentsView.vue`, `PaymentView.vue`, `StorePaymentView.vue`, `client_payments_service.py`, `store_checkout_service.py`. |
| Paneles y configuración | Resúmenes por perfil y parámetros operativos, como capacidades del gimnasio. | `HomeView.vue`, `dashboard.js`, `configuration.py`, `gym_routes.py`. |
| Sitio público | Presentación del gimnasio, información institucional, preguntas frecuentes y acceso al registro o inicio de sesión. | `LandingView.vue`, `NosotrosView.vue`, `PreguntasFrecuentesView.vue`. |

Las rutas de aplicación de esta memoria se refieren a la raíz del repositorio;
la raíz de trabajo de Spec Kit es `sdd/`.

Las vistas se encuentran en `frontend/src/presentation/views/`, los componentes
en `frontend/src/presentation/components/` y los módulos de aplicación frontend
en `frontend/src/application/modules/`. Las rutas backend están en
`backend/presentation/routes/`, las operaciones en `backend/application/operations/`
y los servicios en `backend/application/services/`.

Fuentes para mantener el mapa: [rutas de navegación](../../../frontend/src/presentation/router/index.js),
[rutas backend](../../../backend/presentation/routes) y
[arquitectura](../../../docs/arquitectura.md). Los nombres de archivo de la tabla
son puntos de entrada representativos, no implementaciones independientes de
todo el módulo.

### Relaciones que deben contemplar las especificaciones

- **Registro, clientes, membresías y pagos:** un alta y una confirmación de pago
  tienen efectos distintos. Mantener explícitas las condiciones de activación
  y las relaciones entre cuenta, cliente, plan y membresía.
- **Horarios, matrículas, entrenador y asistencias:** verificar las dependencias
  de membresía, cupos, asignación de rutina y registro de asistencia cuando el
  cambio afecte esos flujos.
- **Inventario, tienda, pedidos y pagos:** distinguir la reserva del inventario,
  la reposición hacia tienda y el stock del producto. Conservar las reglas
  existentes de reserva, descuento o liberación de existencias según el resultado
  del pedido y su pago.
- **Autenticación y permisos:** aplicar los controles del perfil y del recurso en
  la API y la interfaz. Este catálogo no concede permisos por la mera presencia
  de un módulo en un menú.
- **Capacidades compartidas:** notificaciones por correo, imágenes, sincronización,
  caché, validaciones y control de errores apoyan varios módulos. Especificar los
  efectos sobre ellas cuando corresponda.

Cada `spec.md` debe identificar el módulo principal, los módulos relacionados
y los flujos afectados. Cada `plan.md` debe revisar esas relaciones y justificar
los cambios de contrato o de responsabilidad necesarios. Actualizar este mapa
cuando se añada, retire o redefina un módulo funcional.

Al simplificar pantallas, agrupar acciones por la tarea del usuario y verificar
que se conservan las capacidades, permisos y datos de los módulos involucrados.
La propuesta de simplificación de inventario se evaluará en su propia spec;
este mapa registra el alcance actual y no aprueba un rediseño concreto.

## Flujo y comprobaciones

1. Especificar el resultado y sus límites en `spec.md`.
2. Resolver decisiones que afecten al cambio; documentar supuestos razonables.
3. Preparar `plan.md`, evaluar estos principios y dividir `tasks.md` por historia.
4. Analizar consistencia, implementar tareas necesarias y verificar criterios.
5. Registrar brechas sin declarar convergencia mientras quede aceptación pendiente.

La revisión forma parte del trabajo autorizado; estos pasos no añaden una
solicitud de permiso para cada archivo o tarea. Un cambio de documentación o una
refactorización sin cambios de comportamiento puede referenciar specs existentes.

## Gobernanza

Esta constitución guía el trabajo del repositorio junto con `AGENTS.md`.
Las instrucciones explícitas del usuario prevalecen. Toda excepción concreta
debe justificarse en el plan y limitarse al cambio solicitado.
Las modificaciones de principios actualizan la versión y los artefactos afectados:
MAJOR para reglas incompatibles, MINOR para nuevas reglas y PATCH para aclaraciones.
Fuentes iniciales: README, `docs/arquitectura.md`,
`docs/control-errores-modulos.md` y CI del repositorio.
No establece condiciones nuevas de despliegue ni exige aprobaciones adicionales.

**Version**: 1.1.1 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27
