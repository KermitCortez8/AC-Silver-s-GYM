# Pruebas ordenadas por módulo y tipo

Reorganización de pruebas: **2026-11-10**. Alcance: árbol de trabajo de `7744c6c`.
La [batería de casos de uso está en la spec base](spec.md#batería-de-pruebas-de-casos-de-uso).
La [batería individual completa](casos-de-prueba/indice.md) detalla los 1.177 casos
backend/frontend y sus variantes; los 89 escenarios de la spec agrupan recorridos.

El inventario incluye **99 archivos automatizados**: 46 backend, 51 frontend,
uno Deno y uno del flujo documental; además, tres scripts manuales, los 20
informes de `base/validaciones` y las validaciones de las specs 000/001 y del
prototipo 002. Las pruebas están físicamente en `backend/tests/<módulo>/<tipo>/` y
`frontend/tests/<módulo>/<tipo>/`; las referencias apuntan a esas rutas.
Los archivos compartidos indican los otros módulos que ejercitan.

## Cómo interpretar las pruebas

| Tipo | Qué comprueba | Límite |
| --- | --- | --- |
| Unitaria/reglas | Funciones, validaciones y reglas con datos controlados. | No demuestra HTTP, base real o pantalla. |
| Integración con dobles | Casos de aplicación, HTTP en TestClient, repositorios o transportes inyectados. | Una clase Supabase/Stripe/Resend con doble no acredita ese servicio remoto. |
| PostgreSQL | Migraciones/RPC, locks, permisos y concurrencia en base desechable. | Requiere contenedor explícito; cron requiere además pg_cron. |
| Interfaz Node/SSR | Stores, composables y componentes Vue renderizados en Node. | No demuestra apariencia ni interacción en navegador real. |
| Navegador/visual | Recorridos Chromium y capturas enlazados en validaciones históricas. | Salvo el recorrido conectado declarado, usan sesiones/API sintéticas. |
| Manual | Scripts invocados expresamente y recorridos documentados. | Un script existente no implica ejecución ni aprobación. |
| Arquitectura/documental | Capas, tamaño de vistas, enlaces, contratos y flujo SDD. | No acredita aceptación funcional del gimnasio. |

Los tipos se asignan por mecanismo; seguridad, regresión, fronteras, concurrencia
y pruebas funcionales describen el objetivo dentro de cada tipo. Una misma suite
puede mezclar mecanismos y cubrir varios módulos. Once archivos
frontend usan aserciones de nivel superior; también son pruebas aunque no
contengan una llamada `test()`. Los parámetros y bucles amplían los casos: no
se debe confundir número de archivos o funciones con casos ejecutados.

**Estado de esta revisión:** archivos reorganizados físicamente, imports/rutas y
CI actualizados. Antes y después se comprobaron 751 pruebas backend aprobadas
(54 SQL omitidas sin contenedor) y 372 frontend aprobadas. Además se ejecutaron
50 casos SQL en una base desechable con pg_cron; cuatro generales quedaron
fuera de selección por la migración 023 vacía. Las cifras históricas
pertenecen a sus entregas y no se suman como una sola ejecución. Los controles
y límites de esta reorganización se registran en [validation.md](validation.md).

## Índice

- [MOD-01 · Identidad y acceso](#mod-01).
- [MOD-02 · Clientes](#mod-02).
- [MOD-03 · Membresías y pagos](#mod-03).
- [MOD-04 · Planes y promociones](#mod-04).
- [MOD-05 · Horarios y matrículas](#mod-05).
- [MOD-06 · Asistencias](#mod-06).
- [MOD-07 · Rutinas y progreso](#mod-07).
- [MOD-08 · Inventario y movimientos](#mod-08).
- [MOD-09 · Tienda y pedidos](#mod-09).
- [MOD-10 · Paneles y configuración](#mod-10).
- [MOD-11 · Notificaciones](#mod-11).
- [Transversal · Controles compartidos de los once módulos](#controles-compartidos).

<a id="mod-01"></a>

## MOD-01 · Identidad y acceso

Contrato: [01-identidad-acceso.md](../../base/modulos/01-identidad-acceso.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [test_security_utils.py](../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py) | Hash/verificación de contraseña, payload JWT, perfil y rol; son utilidades, no prueba de permisos HTTP. |
| [decode-jwt.test.js](../../../frontend/tests/identidad_acceso/unitarias/decode-jwt.test.js) | Decodificación de payload; no verifica firma del token. |
| [default-membership.test.js](../../../frontend/tests/identidad_acceso/unitarias/default-membership.test.js) | Perfil predeterminado del personal interno; no acredita acceso de clientes. |
| [format-user-data.test.js](../../../frontend/tests/identidad_acceso/unitarias/format-user-data.test.js) | Mapeo de identidad y correo de perfil. |
| [invalid-email.test.js](../../../frontend/tests/identidad_acceso/unitarias/invalid-email.test.js) | Correo sin arroba rechazado. |
| [user-role.test.js](../../../frontend/tests/identidad_acceso/unitarias/user-role.test.js) | Derivación local histórica de rol; el servidor conserva la autoridad. |
| [valid-email.test.js](../../../frontend/tests/identidad_acceso/unitarias/valid-email.test.js) | Correo válido en la utilidad histórica. |
| [valid-user.test.js](../../../frontend/tests/identidad_acceso/unitarias/valid-user.test.js) | Validación básica del usuario normalizado. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [public-navigation.test.js](../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js) | Guard del router con sesión en memoria, landing pública y restricciones de rol. |
| [session-validation.test.js](../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js) | Validación compartida, caché, cambio de token y logout durante una consulta. |

<a id="mod-02"></a>

## MOD-02 · Clientes

Contrato: [02-clientes.md](../../base/modulos/02-clientes.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [test_clients_lookup.py](../../../backend/tests/clientes/unitarias/test_clients_lookup.py) | Prioridad de identidad y rechazo de coincidencias ajenas. |
| [client-directory.test.js](../../../frontend/tests/clientes/unitarias/client-directory.test.js) | Filtros, búsqueda, orden, paginación y tres estados visibles. |
| [client-identity.test.js](../../../frontend/tests/clientes/unitarias/client-identity.test.js) | Identidad cliente/usuario, pertenencia de asistencia y día de semana; compartida con MOD-06. |
| [find-client.test.js](../../../frontend/tests/clientes/unitarias/find-client.test.js) | Búsqueda de cliente por identidad. |
| [normalizers.test.js](../../../frontend/tests/clientes/unitarias/normalizers.test.js) | Normalización de correo y DNI. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_admin_client_payment.py](../../../backend/tests/clientes/integracion/test_admin_client_payment.py) | Alta administrativa, pago manual/Stripe simulado, promociones, importe cero, permisos y reintentos; compartida con MOD-03/04. |
| [test_preregistration_gateway.py](../../../backend/tests/clientes/integracion/test_preregistration_gateway.py) | Claves de idempotencia, recuperación paginada y errores de búsqueda Stripe con transporte simulado; MOD-03. |
| [test_public_preregistrations.py](../../../backend/tests/clientes/integracion/test_public_preregistrations.py) | Solicitud privada, cotización, conversión al pagar, caducidad/reconciliación y carreras con repositorio/gateway dobles. |

### Pruebas PostgreSQL y concurrencia

| Archivo | Cobertura observada |
| --- | --- |
| [test_client_deletion_postgres.py](../../../backend/tests/clientes/postgres/test_client_deletion_postgres.py) | Borrar cuenta conservando venta, comprador y líneas; rollback y venta concurrente; MOD-09. |
| [test_public_preregistrations_postgres.py](../../../backend/tests/clientes/postgres/test_public_preregistrations_postgres.py) | Privacidad/RLS, rollback, confirmación y preparación concurrentes, caducidad frente a pago. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [client-catalog.test.js](../../../frontend/tests/clientes/interfaz/client-catalog.test.js) | Catálogo remoto, alta pública temporal, promociones, errores/borrador e importe histórico; MOD-04. |
| [client-flow-control.test.js](../../../frontend/tests/clientes/interfaz/client-flow-control.test.js) | Retorno de pago, identidad, verificación repetida, errores, pago manual y activación; MOD-03. |
| [formularios.test.js](../../../frontend/tests/clientes/interfaz/formularios.test.js) | Editor/detalle del cliente y registro público con validación de datos, pago y activación. |

### Procedimientos manuales

| Archivo | Cobertura observada |
| --- | --- |
| [register_client.py](../../../backend/tests/clientes/manuales/register_client.py) | Alta manual de cliente con membresía; usa la base configurada, no es pytest ni tiene ejecución nueva acreditada. |

<a id="mod-03"></a>

## MOD-03 · Membresías y pagos

Contrato: [03-membresias-pagos.md](../../base/modulos/03-membresias-pagos.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [admin-client-payment.test.js](../../../frontend/tests/membresias_pagos/unitarias/admin-client-payment.test.js) | Elegibilidad de pago administrativo según origen y estado. |
| [membership-payments.test.js](../../../frontend/tests/membresias_pagos/unitarias/membership-payments.test.js) | Totales confirmados, pendientes, filtros e historial. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_admin_membership_renewal.py](../../../backend/tests/membresias_pagos/integracion/test_admin_membership_renewal.py) | Renovación administrativa en efectivo/Stripe, permisos, ventana y doble envío concurrente con dobles; no es concurrencia SQL. |
| [test_membership_expiration.py](../../../backend/tests/membresias_pagos/integracion/test_membership_expiration.py) | Día final inclusivo en Lima, bloqueo de acceso, renovación vigente, Google y persistencia con doble remoto; MOD-01. |
| [test_membership_payments.py](../../../backend/tests/membresias_pagos/integracion/test_membership_payments.py) | Historial, descuentos guardados, idempotencia y permisos del personal. |
| [test_membership_renewal.py](../../../backend/tests/membresias_pagos/integracion/test_membership_renewal.py) | Enlace personal, precio, ventana de recompra, checkout reutilizado, activación y avisos; MOD-11. |
| [test_membership_states.py](../../../backend/tests/membresias_pagos/integracion/test_membership_states.py) | Tres estados, normalización histórica y bloqueo de activaciones falsas. |
| [test_stripe_checkout.py](../../../backend/tests/membresias_pagos/integracion/test_stripe_checkout.py) | Checkout, configuración, modo, firma y cuerpo original del webhook con Stripe simulado. |
| [test_stripe_confirmation.py](../../../backend/tests/membresias_pagos/integracion/test_stripe_confirmation.py) | Importe, metadatos, modo, titular, pago pendiente y activación idempotente. |
| [test_supabase_payment_safety.py](../../../backend/tests/membresias_pagos/integracion/test_supabase_payment_safety.py) | Esquema de pago ausente y distinción de fallo de conexión. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [admin-membership-renewal.test.js](../../../frontend/tests/membresias_pagos/interfaz/admin-membership-renewal.test.js) | Caja con recibo, compra Stripe pendiente, doble clic, estado del servidor y últimos siete días. |
| [membership-renewal.test.js](../../../frontend/tests/membresias_pagos/interfaz/membership-renewal.test.js) | Enlace personal, revisión sin cobrar, cambio de precio y respuesta obsoleta. |

### Procedimientos manuales

| Archivo | Cobertura observada |
| --- | --- |
| [fetch_memberships.py](../../../backend/tests/membresias_pagos/manuales/fetch_memberships.py) | Consulta de membresías sobre la configuración activa; sin evidencia de ejecución nueva. |
| [insert_membership.py](../../../backend/tests/membresias_pagos/manuales/insert_membership.py) | Inserción manual de ejemplo; escribe en la base configurada y no pertenece a pytest. |

<a id="mod-04"></a>

## MOD-04 · Planes y promociones

Contrato: [04-planes-promociones.md](../../base/modulos/04-planes-promociones.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [test_promocion_cupos.py](../../../backend/tests/planes_promociones/unitarias/test_promocion_cupos.py) | Agotamiento del límite de una promoción. |
| [test_promocion_navidad.py](../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py) | Solapamiento, vigencia pública y aplicación de promociones. |
| [membership-plan-form.test.js](../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js) | Duraciones, precio cero, obligatoriedad y longitud del nombre. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [formularios.test.js](../../../frontend/tests/planes_promociones/interfaz/formularios.test.js) | Guardado y borrado de promoción con confirmación, error y prevención de doble clic. |
| [plan-directory.test.js](../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js) | Búsqueda, orden por precio, disponibilidad, carga duplicada y reintento. |

<a id="mod-05"></a>

## MOD-05 · Horarios y matrículas

Contrato: [05-horarios-matriculas.md](../../base/modulos/05-horarios-matriculas.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [landing-schedules.test.js](../../../frontend/tests/horarios_matriculas/unitarias/landing-schedules.test.js) | Horarios públicos, normalización, orden y filtros de servicio. |
| [schedule-calendar.test.js](../../../frontend/tests/horarios_matriculas/unitarias/schedule-calendar.test.js) | Fechas concretas por semana, límites de mes/año y pertenencia por sesión; MOD-06. |
| [schedule-enrollment.test.js](../../../frontend/tests/horarios_matriculas/unitarias/schedule-enrollment.test.js) | Etiquetas, horas, identificación de ejercicios, matrículas propias y cupos. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_enrollment_errors.py](../../../backend/tests/horarios_matriculas/integracion/test_enrollment_errors.py) | Traducción de errores de matrícula sin ocultar fallos desconocidos. |
| [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py) | Catálogo, cupos, cancelación propia, identidad de sesión y RPC obligatoria; asignación de rutina en MOD-07. |
| [test_schedule_sessions.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_sessions.py) | Reserva/cancelación por fecha, vigencia, mapeo y consulta HTTP; MOD-06. |

### Pruebas PostgreSQL y concurrencia

| Archivo | Cobertura observada |
| --- | --- |
| [test_schedule_sessions_postgres.py](../../../backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py) | Cupos y duplicados por fecha, concurrencia, migración, privacidad y recordatorios; MOD-06/11. |

<a id="mod-06"></a>

## MOD-06 · Asistencias

Contrato: [06-asistencias.md](../../base/modulos/06-asistencias.md).

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_general_attendance.py](../../../backend/tests/asistencias/integracion/test_general_attendance.py) | DNI, reloj Lima, membresía, aforo, reintentos, bloqueo cruzado, privacidad, auditoría y cierre general con dobles. |
| [test_schedule_attendance.py](../../../backend/tests/asistencias/integracion/test_schedule_attendance.py) | Calendario/lista por fecha, margen de 30 minutos, entrada, salida tardía, plazo original y privacidad. |

### Pruebas PostgreSQL y concurrencia

| Archivo | Cobertura observada |
| --- | --- |
| [test_attendance_deadline_postgres.py](../../../backend/tests/asistencias/postgres/test_attendance_deadline_postgres.py) | RPC: reloj, límite inclusivo, tardanza, corrección, repetición de migración y permisos. |
| [test_attendance_enrollment_flow_postgres.py](../../../backend/tests/asistencias/postgres/test_attendance_enrollment_flow_postgres.py) | Matrícula → entrada admin → salida omitida, RPC/pg_cron y dos entradas de tipos distintos en paralelo. |
| [test_automatic_attendance_postgres.py](../../../backend/tests/asistencias/postgres/test_automatic_attendance_postgres.py) | Estado incompleto, reconciliación/cron, cierre general y carreras; la migración 023 vacía limita hoy su reproducibilidad. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [flujos.test.js](../../../frontend/tests/asistencias/interfaz/flujos.test.js) | Consulta, calendario, fecha, bloqueo cruzado, entrada/salida y cierre general con componentes y composables reales/SSR. |

<a id="mod-07"></a>

## MOD-07 · Rutinas y progreso

Contrato: [07-rutinas-progreso.md](../../base/modulos/07-rutinas-progreso.md).

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_trainer_exercises.py](../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py) | API, ejercicios, historial, serialización JSON y esquema obligatorio con adaptadores dobles. |
| [trainer-refresh-errors.test.js](../../../frontend/tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js) | Guardar/desasignar/progreso confirmado seguido de refresco fallido; evita repetir una escritura ya confirmada. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [flujos.test.js](../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js) | Asignación/desasignación, progreso, diálogos y descanso; borrador conservado y temporizador liberado al desmontar. |

<a id="mod-08"></a>

## MOD-08 · Inventario y movimientos

Contrato: [08-inventario.md](../../base/modulos/08-inventario.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [test_inventory_quantities.py](../../../backend/tests/inventario/unitarias/test_inventory_quantities.py) | Cantidades inválidas, stock cero, movimiento positivo y ausencia de mutaciones; MOD-09. |
| [inventario-teclado-limites.test.js](../../../frontend/tests/inventario/unitarias/inventario-teclado-limites.test.js) | Límites de texto, dígitos, Enter/flechas/espacio, textarea, fecha e IME. |
| [quantities.test.js](../../../frontend/tests/inventario/unitarias/quantities.test.js) | Fronteras numéricas y clasificación visual de avisos/errores. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_inventario_tienda_stock.py](../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py) | Reserva/reposición, correcciones, estados, ventas, papelera y rollback con doble Supabase; MOD-09. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [formularios.test.js](../../../frontend/tests/inventario/interfaz/formularios.test.js) | Formulario, movimientos, cantidades, stock mínimo cero, avisos en vivo, búsqueda y errores con borrador conservado. |

<a id="mod-09"></a>

## MOD-09 · Tienda y pedidos

Contrato: [09-tienda-pedidos.md](../../base/modulos/09-tienda-pedidos.md).

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_store_images.py](../../../backend/tests/tienda_pedidos/integracion/test_store_images.py) | Subida/listado y validación previa al almacenamiento, sin publicar en proveedor real. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [formularios.test.js](../../../frontend/tests/tienda_pedidos/interfaz/formularios.test.js) | Producto, imágenes, Papelera, pedidos, carrito, cantidades y checkout; errores y doble envío en componentes reales/SSR. |

<a id="mod-10"></a>

## MOD-10 · Paneles y configuración

Contrato: [10-paneles-configuracion.md](../../base/modulos/10-paneles-configuracion.md).

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [client-dashboard.test.js](../../../frontend/tests/paneles_configuracion/unitarias/client-dashboard.test.js) | Contadores por pago/activación/vencimiento y serie de siete días en Lima. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_supabase_refresh.py](../../../backend/tests/paneles_configuracion/integracion/test_supabase_refresh.py) | Recursos por sección, caché/TTL, permisos, fallos parciales, health y datos conservados con transporte simulado. |
| [application-context.test.js](../../../frontend/tests/paneles_configuracion/integracion/application-context.test.js) | Adaptadores y sesiones separados por aplicación/Pinia. |
| [module-navigation.test.js](../../../frontend/tests/paneles_configuracion/integracion/module-navigation.test.js) | Carga y navegación por rol, temporizador, consultas lentas y descarte de finalizaciones antiguas. |
| [scoped-gym-modules.test.js](../../../frontend/tests/paneles_configuracion/integracion/scoped-gym-modules.test.js) | Instancias de módulos aisladas, capacidades declaradas y generación del entrenador; MOD-03/07. |
| [sync-resources.test.js](../../../frontend/tests/paneles_configuracion/integracion/sync-resources.test.js) | Tres lecturas concurrentes como máximo y errores por sección. |

<a id="mod-11"></a>

## MOD-11 · Notificaciones

Contrato: [11-notificaciones.md](../../base/modulos/11-notificaciones.md).

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_resend_email.py](../../../backend/tests/notificaciones/integracion/test_resend_email.py) | Colas, timeout, ID de proveedor, datos seguros, remitente, contexto obsoleto y configuración con Resend simulado. |
| [test_schedule_calendar.py](../../../backend/tests/notificaciones/integracion/test_schedule_calendar.py) | Semana por cliente/fecha y enlace/correo con fecha Lima; MOD-05/06. |

### Pruebas PostgreSQL y concurrencia

| Archivo | Cobertura observada |
| --- | --- |
| [test_membership_renewal_postgres.py](../../../backend/tests/notificaciones/postgres/test_membership_renewal_postgres.py) | Aviso de renovación deduplicado/reclamado una vez, eventos válidos y permisos de cola; MOD-03. |

### Pruebas de la Edge Function

| Archivo | Cobertura observada |
| --- | --- |
| [resend_email_test.ts](../../../supabase/tests/resend_email_test.ts) | Siete casos Deno: fecha única, destinatario/idempotencia, errores privados, ID obligatorio, reintento, dry run/autorización y configuración. |

<a id="controles-compartidos"></a>

## Controles compartidos

### Pruebas unitarias

| Archivo | Cobertura observada |
| --- | --- |
| [input-rules.test.js](../../../frontend/tests/transversales/unitarias/input-rules.test.js) | Búsqueda, orden, campos requeridos, cantidades y favoritos por usuario; MOD-02/04/08/09. |
| [priority-money-dates.test.js](../../../frontend/tests/transversales/unitarias/priority-money-dates.test.js) | Céntimos, redondeo, descuentos, duración y reloj Lima; MOD-03/04/09/10. |

### Pruebas de integración

| Archivo | Cobertura observada |
| --- | --- |
| [test_basic_form_validation.py](../../../backend/tests/transversales/integracion/test_basic_form_validation.py) | Correo, identidad, duplicados, errores por campo y precios; MOD-01/02/04/09. |
| [test_client_flow_control.py](../../../backend/tests/transversales/integracion/test_client_flow_control.py) | Borrado y errores HTTP, edición protegida y recorrido de registro a vencimiento; compartida con MOD-03/05/06. |
| [test_form_limits.py](../../../backend/tests/transversales/integracion/test_form_limits.py) | Límite y límite+1 en modelos/comandos de cuentas, planes, promociones, horarios, inventario y asistencia. |
| [test_maintainability_fixes.py](../../../backend/tests/transversales/integracion/test_maintainability_fixes.py) | Validación, ceros, esquema/transportes, errores HTTP y política de imagen. |
| [test_module_error_control.py](../../../backend/tests/transversales/integracion/test_module_error_control.py) | Matriz HTTP de módulos, estados de error, validación privada y capacidad inválida. |
| [test_partial_smell_fixes.py](../../../backend/tests/transversales/integracion/test_partial_smell_fixes.py) | Cancelación de checkout y carrera con pago, error HTTP, unidad de trabajo/caché; pesos y ejercicios de MOD-07. |
| [test_priority_fixes.py](../../../backend/tests/transversales/integracion/test_priority_fixes.py) | Matriz de roles/actor, privacidad, ID, campos, dinero, Lima, webhook asíncrono y falta de RPC atómica. |
| [test_remaining_smells.py](../../../backend/tests/transversales/integracion/test_remaining_smells.py) | Resumen mediante conteos, consultas paginadas y recursos mínimos; rutina, matrícula y pedido sin cargar áreas ajenas. |
| [test_review_regressions.py](../../../backend/tests/transversales/integracion/test_review_regressions.py) | Revocación de cuentas internas, Google y tokens; también clientes (MOD-02), actor de progreso (MOD-07), pedidos (MOD-09) y resumen (MOD-10). |
| [test_scoped_operations.py](../../../backend/tests/transversales/integracion/test_scoped_operations.py) | Historial paginado y alcance por cliente; también límites de comandos, cascada de clientes y rollback transversales. |
| [api-response.test.js](../../../frontend/tests/transversales/integracion/api-response.test.js) | Errores HTML de gateway, autenticación, configuración y JSON inválido. |
| [data-repositories.test.js](../../../frontend/tests/transversales/integracion/data-repositories.test.js) | Repositorios por módulo, identidades, ceros, borrado/papelera y refresco posterior a una escritura. |
| [form-validation.test.js](../../../frontend/tests/transversales/integracion/form-validation.test.js) | Validación reactiva por campo, correos .com, identidad, precios, promociones y longitudes. |
| [http-error-control.test.js](../../../frontend/tests/transversales/integracion/http-error-control.test.js) | Red/timeout/cancelación, cuerpo demorado, JSON, 204 y resultado incierto sin reintento automático. |
| [module-error-control.test.js](../../../frontend/tests/transversales/integracion/module-error-control.test.js) | Lecturas/escrituras/borrados fallidos, carrito/stock/aforo y respuestas anteriores a guardar/cancelar. |
| [navigation-stores.test.js](../../../frontend/tests/transversales/integracion/navigation-stores.test.js) | Usuarios/configuración, carga por sección, revalidación, logout y escrituras confirmadas; afecta a los módulos que consumen gymStore. |
| [response-identifiers.test.js](../../../frontend/tests/transversales/integracion/response-identifiers.test.js) | IDs positivos seguros, formatos rechazados y ausencia de publicación con ID inválido. |

### Pruebas PostgreSQL y concurrencia

| Archivo | Cobertura observada |
| --- | --- |
| [test_atomic_transactions_postgres.py](../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py) | Rollback, snapshot obsoleto, RPC privada, ventas concurrentes, IDs, asociaciones y recarga; MOD-01/02/03/04/07/09. |

### Pruebas de interfaz y flujos Vue/Pinia

| Archivo | Cobertura observada |
| --- | --- |
| [formularios.test.js](../../../frontend/tests/transversales/interfaz/formularios.test.js) | Validación compartida de los editores de cliente y usuario; conserva borradores inválidos sin enviar solicitudes. |
| [table-pagination-views.test.js](../../../frontend/tests/transversales/interfaz/table-pagination-views.test.js) | Filas, última página y paginador de inventario y tienda; MOD-09. |
| [table-pagination.test.js](../../../frontend/tests/transversales/interfaz/table-pagination.test.js) | Tamaño 1–100, navegación, filas, claves de almacenamiento independientes y degradación de storage; incluye controles estáticos. |

### Pruebas de arquitectura y documentación

| Archivo | Cobertura observada |
| --- | --- |
| [test_integration.py](../../tests/test_integration.py) | Trece pruebas del flujo documental: enlaces, contratos, scripts, hooks y descubrimiento de skills; no valida negocio. |
| [test_layer_boundaries.py](../../../backend/tests/transversales/arquitectura/test_layer_boundaries.py) | Imports por capas y pruebas de inyección, copias, fallo de commit y expiración de pedido impago. |
| [layer-boundaries.test.js](../../../frontend/tests/transversales/arquitectura/layer-boundaries.test.js) | Dependencias por capas, vistas ≤500 líneas e inyección de servicios/repositorios. |

## Preparación compartida

- Backend: [doble atómico](../../../backend/tests/soporte/atomic_fake.py) y
  [fixture SQL](../../../backend/tests/soporte/fixtures/priority_schema.sql).
- Frontend: [entorno de vistas](../../../frontend/tests/soporte/entorno-vistas.js) y
  [entorno de formularios](../../../frontend/tests/soporte/entorno-formularios.js).
- Los módulos sin una suite exclusiva de un tipo usan los controles compartidos
  de `transversales`; no se crean carpetas vacías ni copias de pruebas.

## Ejecuciones históricas y evidencia por módulo y tipo

Estas filas indexan todos los informes de validación existentes en la base.
Las cifras se transcriben del registro enlazado y conservan sus omisiones/fallos.
Cuando un informe tiene varias revisiones se indica la revisión pertinente.

| Módulo | Tipo | Registro y alcance | Resultado histórico y límite |
| --- | --- | --- | --- |
| MOD-01 | Navegador/router | [navegacion-publica](../../base/validaciones/navegacion-publica/validation.md): Landing con los cuatro roles y sesión vencida. | Ocho casos de router en esa entrega y recorrido Chromium con API sintética. |
| MOD-02 / MOD-09 | Dominio y PostgreSQL | [borrado-clientes-con-ventas](../../base/validaciones/borrado-clientes-con-ventas/validation.md): Borrado conservando comprador, venta y líneas. | Backend: 733 correctas/49 omitidas; 18 SQL correctas. Migración 025 pendiente en la base externa según el informe. |
| MOD-02 | HTTP, interfaz y navegador | [borrado-preregistros](../../base/validaciones/borrado-preregistros/validation.md): DELETE 204, conflicto real y pago abandonado. | Backend: 629 correctas/28 omitidas; cinco escenarios de navegador sintético; sin borrado remoto. |
| MOD-02 | HTTP, PostgreSQL y navegador | [preregistros-separados](../../base/validaciones/preregistros-separados/validation.md): Preregistro privado y conversión tras pago. | Backend: 658 correctas/33 SQL omitidas en esa ejecución; integración SQL y cuatro escenarios sintéticos descritos aparte. |
| MOD-02 | Interfaz, navegador y lectura de catálogo | [catalogo-clientes](../../base/validaciones/catalogo-clientes/validation.md): Planes/promociones remotos en alta y edición. | Frontend: 288 correctas; cinco escenarios sintéticos. Lectura real de catálogo sin clientes ni escrituras. |
| MOD-02 | Regresión de interfaz | [limites-cliente](../../base/validaciones/limites-cliente/validation.md): DNI de 8 y teléfono de 9 al escribir/pegar. | Frontend: 293 aprobadas y build; no aporta capturas de revisión visual propia. |
| MOD-03 / MOD-11 | Aplicación, PostgreSQL, interfaz y navegador | [renovacion-membresia](../../base/validaciones/renovacion-membresia/validation.md): Renovación pública/admin, avisos, activación automática y ventana. | Última revisión: backend 731 aprobadas/46 omitidas, frontend 367 aprobadas. Dos SQL de avisos verificadas en una revisión anterior. |
| MOD-04 | Interfaz y navegador | [formulario-planes](../../base/validaciones/formulario-planes/validation.md): Selector de duración y validación. | Frontend: 298 aprobadas, cuatro dirigidas y seis escenarios sintéticos. |
| MOD-04 | Interfaz y navegador | [diseno-membresias](../../base/validaciones/diseno-membresias/validation.md): Tarjetas, filtros, formulario, borrado y temas. | Frontend: 302 aprobadas; siete escenarios nuevos y seis del formulario, todos sintéticos. |
| MOD-05 / MOD-06 / MOD-11 | HTTP, SQL, Deno y navegador | [matriculas-sesiones](../../base/validaciones/matriculas-sesiones/validation.md): Cupos, asistencia y recordatorios por fecha. | Backend: 655 aprobadas/0 omitidas con SQL; frontend 270; Deno 7. UI sintética; migración 019 pendiente externa en esa entrega. |
| MOD-05 | Interfaz y navegador | [horarios-cliente](../../base/validaciones/horarios-cliente/validation.md): Foco, intervalo y descarte de matrículas obsoletas. | Frontend: 265 aprobadas; validación de actualización con API sintética. |
| MOD-05 / MOD-06 | Recorrido conectado, RPC y cron | [prueba-asistencia-horario](../../base/validaciones/prueba-asistencia-horario/validation.md): Matrícula propia, entrada administrativa, salida omitida y privacidad. | 79 backend y 15 SQL con pg_cron; variante Alpine: una aprobada/una omitida. Recorrido conectado histórico, sin capturas reales versionadas; no acredita cierre general. |
| MOD-06 | Aplicación, SQL y navegador | [asistencia-automatica](../../base/validaciones/asistencia-automatica/validation.md): Incompleta de clase y cierre general a tres horas. | Registro: backend 698 aprobadas/44 omitidas, 43 SQL aparte y frontend 353. Evidencia histórica: actualmente 023 está vacía. |
| MOD-06 | Aplicación, SQL y navegador | [bloqueo-asistencia](../../base/validaciones/bloqueo-asistencia/validation.md): Bloqueo cruzado y margen de 30 minutos. | Última revisión: backend 751 aprobadas/54 omitidas, frontend 372; SQL y recorridos sintéticos separados. No valida cierre general SQL. |
| MOD-06 | HTTP, SQL y navegador | [asistencias](../../base/validaciones/asistencias/validation.md): Entradas/salidas, privacidad, plazo de clase y calendario. | Backend: 634 aprobadas con SQL; frontend 262, luego 268 al revisar calendario. API sintética en capturas. |
| MOD-06 | Regresión temporal y SQL | [relojes-asistencia](../../base/validaciones/relojes-asistencia/validation.md): Reloj unificado de membresías/asistencia. | Backend: 680 aprobadas/33 omitidas sin SQL; 713 aprobadas con 33 SQL incluidas en ese estado. |
| TR | Arquitectura, interfaz y comparación visual | [views-modulares](../../base/validaciones/views-modulares/validation.md): Extracción de vistas y conservación de formularios. | Frontend: 271 aprobadas; 14 casos Chromium y comparación de capturas, con API sintética. |
| TR | Fronteras, HTTP, interfaz y navegador | [limites-formularios](../../base/validaciones/limites-formularios/validation.md): Longitudes compartidas y comandos directos. | 82 backend dirigidas; completa: 640 aprobadas/39 fallidas/33 omitidas; frontend 294 y 17 comprobaciones Chromium. Fallos históricos comparados con baseline, no ocultarlos. |
| TR | Interfaz y navegador | [ortografia](../../base/validaciones/ortografia/validation.md): Textos de siete pantallas y etiquetas de horarios. | Frontend: 280 correctas; siete recorridos sintéticos; sin alterar contratos API. |
| TR | Regresión y compilación | [pr-103](../../base/validaciones/pr-103/validation.md): Conflictos, avisos en vivo y Papelera. | Backend con SQL: 718 aprobadas/0 omitidas; frontend 305; 55 dirigidas. Sin nueva revisión visual. |

### Specs y demostración fuera de la base implementada

| Módulos relacionados | Tipo | Fuente | Interpretación |
| --- | --- | --- | --- |
| Transversal | Validación documental | [Adopción 000](validation.md) | Ejecución histórica de enlaces/contratos; incluye comprobación dirigida posterior de correo. No certifica todas las suites del producto. |
| MOD-02/03/05/06 | HTTP, reglas, SSR y navegador | [Control de flujo 001](../001-control-flujo-clientes/validation.md) | Registro de criterios CA-01…CA-09, comandos, recorridos simulados y límites de esa feature. |
| MOD-01/02/03/04/05, propuesta 002 | Prototipo navegable | [Validación de prototipos](../002-chatbot-clientes/prototipos/validation.md), [resultados](../002-chatbot-clientes/prototipos/resultados.json), [script](../002-chatbot-clientes/prototipos/revision.cjs) | 18 comprobaciones y 16 capturas con datos fijos, sin llamadas API. No es aceptación de un chatbot integrado. |
| MOD-01/02/04/05, propuesta 002 | Casos de aceptación pendientes | [E1–E9 del chatbot](../002-chatbot-clientes/quickstart.md), [tres casos de uso](../002-chatbot-clientes/casos-de-uso.md) | Escenarios previstos, no pruebas ejecutadas del producto. |
| MOD-06 | Casos de uso documentales | [ECUS 14](../../base/ecus/SilverGym_ECUS14_Registrar_Asistencia_General_v1.2.docx), [ECUS 15](../../base/ecus/SilverGym_ECUS15_Registrar_Asistencia_Por_Horarios_v1.2.docx), [ECUS 16](../../base/ecus/SilverGym_ECUS16_Gestionar_Asistencia_v1.2.docx), [ECUS 17](../../base/ecus/SilverGym_ECUS17_Gestionar_Asistencia_Del_Usuario_v1.2.docx) | Especificaciones de asistencia e historial; un documento Word no es resultado de ejecución. |

## Reproducir las comprobaciones

Ejecutar desde la raíz y con las dependencias del componente preparadas:

```bash
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
(cd backend && python -m pytest tests/ -q)
(cd frontend && npm test)
(cd frontend && npm run build)
deno check supabase/functions/schedule-emails/index.ts
deno test supabase/tests/
```

Para un módulo, seleccionar los archivos de su tabla; por ejemplo:

```bash
(cd backend && python -m pytest tests/horarios_matriculas/integracion/test_schedule_sessions.py tests/asistencias/integracion/test_schedule_attendance.py -q)
(cd frontend && node --test tests/horarios_matriculas/unitarias/schedule-calendar.test.js tests/asistencias/interfaz/flujos.test.js tests/rutinas_progreso/interfaz/flujos.test.js)
```

La sesión backend necesita una `AUTH_SECRET_KEY` sintética válida. PostgreSQL
se ejecuta solo con `GYM_TEST_POSTGRES_CONTAINER` apuntando a un contenedor
**desechable**; sus fixtures modifican/truncan tablas. Sin la variable hay
omisiones, y sin pg_cron se omiten sus variantes de programación real.
Consultar [DoD](../../docs/DoD.md) y [CI](../../../.github/workflows/pr-validation.yml)
para preparar el entorno; el job SQL actual enumera seis suites y no incluye
las suites de borrado de clientes ni avisos de renovación. No asumir que CI
verifica cada archivo PostgreSQL del inventario.

Los scripts manuales se explican en [su guía](../../../backend/tests/soporte/manuales.md).
Los recorridos Chromium se repiten con el arranque, datos sintéticos y dependencias
indicados en cada validación; los scripts de revisión no pertenecen a `npm test`.
Build, flake8 y servicios saludables se registran como controles complementarios,
no como casos de uso aprobados.

## Brechas que afectan a la batería

- [023_general_attendance_three_hour_close.sql](../../../backend/migrations/023_general_attendance_three_hour_close.sql)
  tiene **0 bytes** en esta referencia. El informe de asistencia automática describe
  resultados anteriores; la prueba conectada posterior ya declaró esta incidencia.
  Las pruebas unitarias/con dobles de cierre general no sustituyen una RPC/cron
  reproducible con la migración actual. Los casos SQL de cierre general quedan
  pendientes de validar y pueden fallar al prepararse el esquema.
- La instalación externa de migraciones/cron, Stripe, Google y la entrega real
  de correo no se acredita por resultados locales. El borrado con ventas requiere
  025; su informe conserva la aplicación externa pendiente.
- El prototipo 002 continúa sin integración productiva ni UAT documentada.
- No hay mediciones de carga, rendimiento sostenido o penetración en este
  inventario; la concurrencia de cupos/stock no debe presentarse como prueba de carga.
