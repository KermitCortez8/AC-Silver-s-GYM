# Comprobación visual de las vistas refactorizadas

Fecha: 2026-10-23 (America/Lima). Código local actual, navegador Chromium con Playwright.

## Resultado y alcance

El acceso normal de administrador y entrenador y las lecturas de las dos
pantallas se comprobaron con las cuentas existentes proporcionadas por el usuario
y la API real. Ambas autenticaciones respondieron HTTP 200 y recuperaron el rol
correcto. Los 13 estados capturados no registraron excepciones de JavaScript,
errores de API ni desbordamientos horizontales en las páginas y diálogos.

También se comprobaron los recorridos con datos sintéticos en ocho combinaciones:
administrador/entrenador, escritorio/móvil y tema oscuro/claro. Se capturaron 28
estados y se inspeccionaron capturas representativas. No hubo excepciones de
JavaScript ni desbordamientos horizontales en la página o los diálogos. En móvil
se habilitaron emulación de dispositivo y eventos táctiles; el diálogo de progreso
permite desplazamiento vertical para alcanzar las acciones.

No se crearon cuentas nuevas ni se guardaron cambios en clientes, matrículas,
rutinas o asistencia. La revisión autenticada usa lecturas y cambios locales del
formulario. Los envíos de prueba con datos sintéticos se interceptaron
exclusivamente en el navegador y no llegaron al backend real.

## Comprobaciones con los `.env` reales

- Se comprobó que la aplicación ya iniciada responde y conecta con Supabase.
- Para verificar el código del árbol de trabajo se iniciaron procesos separados
  en 8001 y 5174, sin reiniciar los contenedores existentes. El worker de correos
  no se inició en el backend de comprobación.
- Salud y catálogo respondieron HTTP 200. La consulta especializada de resumen de
  asistencia se ejecutó correctamente contra Supabase con la fecha de negocio.
- Se inspeccionó el acceso público en 1440 × 1000 y 390 × 844, con ambos campos
  visibles y sin desbordamiento horizontal. Sin sesión, `/admin/attendance`
  redirige a `/login`. No se completó el acceso con Google; hubo respuestas 403
  del proveedor para su botón en el origen de comprobación.
- El alta autorizada de personal falló con `42501: permission denied for sequence
  USUARIO_id_usuario_seq`. La transacción revirtió la inserción y no creó ninguna
  cuenta. No se intentó dar de alta clientes.

El usuario sustituyó la creación de cuentas por el uso de dos cuentas existentes.
Se completó el acceso real mediante el formulario de contraseña, sin simular la
autenticación ni inyectar sesiones. Las credenciales no se incorporaron al código,
a este informe ni a las capturas de evidencia.

## Recorridos autenticados con la API real

| Cuenta | Comprobación |
| --- | --- |
| Administrador | Acceso, resumen de asistencia, búsqueda de un cliente existente, ficha y horario, acceso general, historial y presentación móvil en ambos temas. |
| Entrenador | Acceso, supervisión, búsqueda de un cliente existente, ficha de matrícula, apertura y cancelación del diálogo de asignación y apertura del diálogo de progreso en escritorio y móvil; vista móvil en ambos temas. |

La rutina seleccionada para el recorrido real no contenía ejercicios. El diálogo
se mostró correctamente sin controles de ejercicios; el temporizador y los
controles se validaron con los datos sintéticos del apartado siguiente. No se
añadieron ejercicios ni se guardó progreso en la base para ampliar esta prueba.

La corrección está en
[016_transaction_sequence_permissions.sql](../backend/migrations/016_transaction_sequence_permissions.sql).
Concede los permisos necesarios a `service_role` sobre las secuencias de las
tablas admitidas por la transacción. No se aplicó automáticamente a Supabase:
requiere SQL Editor o una conexión como propietario. La clave REST no permite
ejecutar `GRANT`.

## Recorridos de interfaz con datos sintéticos

| Pantalla | Estados y acciones comprobados |
| --- | --- |
| Asistencias | Resumen inicial, búsqueda automática por DNI, ficha y horarios, cambio a gimnasio general, registro de entrada y salida y apertura del historial. |
| Seguimiento | Búsqueda de cliente, ficha de matrícula, diálogo de asignación, selección y envío de rutina, diálogo de ejercicios, inicio del descanso, observaciones y envío de progreso una sola vez. |

Los envíos de esta tabla usan respuestas de prueba controladas. Comprueban el
ensamblaje real de Vue, sus eventos, formularios y presentación, pero no acreditan
persistencia de esas operaciones en Supabase.

## Problema visual corregido

En 390 px, las sugerencias del DNI del entrenador se superponían al botón
«Buscar Cliente» e interceptaban el toque. Se cambió el desplegable para ocupar
espacio en móvil y conservar su posición flotante desde `sm`. Al mover el foco
al botón del mismo formulario, las sugerencias permanecen hasta el envío para
evitar que el botón cambie de posición entre pulsación y clic.

El fallo se reprodujo en ambos temas y el recorrido se repitió después con toque
táctil: las dos variantes móviles completan búsqueda, asignación y progreso.
También se repitieron las variantes de escritorio.

## Evidencias sin datos personales reales

| Caso con datos sintéticos | Captura |
| --- | --- |
| Asistencias, escritorio oscuro | [Ver captura](evidencias/2026-10-24/asistencias-escritorio-oscuro.png) |
| Asistencias, móvil claro | [Ver captura](evidencias/2026-10-24/asistencias-movil-claro.png) |
| Progreso, escritorio claro | [Ver captura](evidencias/2026-10-24/rutinas-escritorio-claro.png) |
| Progreso, móvil claro | [Ver captura](evidencias/2026-10-24/rutinas-movil-claro.png) |

| Caso con acceso real y datos personales ocultos | Captura |
| --- | --- |
| Asistencias, escritorio | [Ver captura](evidencias/2026-10-23/real-asistencias-escritorio.png) |
| Asistencias, móvil claro | [Ver captura](evidencias/2026-10-23/real-asistencias-movil.png) |
| Asignación de rutina | [Ver captura](evidencias/2026-10-23/real-asignacion-rutina.png) |
| Progreso, móvil | [Ver captura](evidencias/2026-10-23/real-progreso-movil.png) |

Las zonas grises ocultan datos personales. Las capturas de diálogos se limitan al
propio diálogo para evitar publicar la ficha del cliente que queda detrás.

Verificación adicional: **137 pruebas de frontend pasan**, compilación Vite de
producción correcta y lint Python seleccionado sin errores. **15 pruebas de
PostgreSQL 16 aislado pasan**, incluida la reproducción del permiso faltante, su
rollback, la aplicación idempotente de 016 y el alcance de los permisos.

La comprobación visual autenticada queda completada para este alcance de lectura.
La migración 016 sigue pendiente de aplicación para corregir el alta de personal;
el acceso con cuentas existentes no demuestra que ese fallo de escritura esté
resuelto. La persistencia de cambios y el acceso con Google no se validaron en la
base configurada.
