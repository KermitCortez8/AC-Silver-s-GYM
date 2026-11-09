# Bloqueo entre asistencia por horarios y general

Fecha: 2026-11-09.

## Pedido y comportamiento

Una entrada sin salida debe impedir otra entrada del mismo cliente, tanto de
horarios a general como de general a horarios. Guardar la salida anterior vuelve
a permitir una nueva visita que cumpla los demás requisitos de admisión. Una
asistencia incompleta de clase sin salida conserva el bloqueo.

El servicio y la RPC ya comprobaban todas las visitas abiertas del cliente.
La corrección hace explícito el origen en el mensaje de conflicto y devuelve
409 en la comprobación de aplicación. La ficha general muestra el aviso y el
origen por horarios/general, con acción de salida. La lista del horario conserva
la entrada deshabilitada e incorpora **Registrar salida pendiente** para cerrar
la visita de otro tipo sin cambiar de pestaña.

No se cambian tablas, membresías, horarios contratados, idempotencia de entradas
o reintentos de salida. Se conservan las reglas de clases por fecha y el cierre
general existente: una visita cerrada deja de bloquear; un estado incompleto sin
hora de salida sigue bloqueando. No se aplican migraciones a Supabase.

## Regresiones

- [test_general_attendance.py](../../../../backend/tests/test_general_attendance.py):
  ambos sentidos, HTTP 409 sin escritura parcial, motivo con origen, proyección
  del bloqueo y nuevo ingreso después de salir; clase incompleta sin salida.
- [test_attendance_enrollment_flow_postgres.py](../../../../backend/tests/test_attendance_enrollment_flow_postgres.py):
  RPC real bloquea ambos sentidos y permite cambiar de tipo tras la salida;
  dos solicitudes concurrentes de tipos distintos solo guardan una visita.
  Se utiliza exclusivamente PostgreSQL desechable explícito.
- [29-view-flows.test.js](../../../../frontend/tests/29-view-flows.test.js):
  general muestra la entrada de horario y solo su salida; horario muestra el
  bloqueo general, cierra la visita pendiente y actualiza la disponibilidad;
  un conflicto tras una consulta obsoleta conserva el aviso sin éxito falso.

Las pruebas SQL de este control utilizan el contrato compartido de clases y
general de 019/021. No certifican la instalación del cron externo ni reconstruyen
la migración 023 vacía, incidencia ya registrada en la prueba anterior.

## Resultados

- Backend completo: **736 aprobadas, 54 omitidas** por requerir PostgreSQL explícito.
- PostgreSQL desechable: **5 aprobadas** en el módulo de recorrido de matrícula y
  asistencia, incluyendo ambos sentidos, concurrencia y cron de clases.
- Frontend completo: **370 aprobadas**; compilación de producción correcta al
  construir la imagen Docker. Flake8 crítico: **0 errores**.
- [Recorrido Chromium](evidence/browser-review.cjs): **4 escenarios aprobados**,
  escritorio 1440 px en tema claro y móvil 390 px en tema oscuro. Las sesiones
  y todas las respuestas API son sintéticas; se bloquea acceso a otros orígenes.
  Se verifica entrada bloqueada, una salida pendiente y exactamente una nueva
  entrada habilitada después de cerrarla, sin errores de página.
- Capturas revisadas de [horario a general en escritorio](evidence/horario-bloquea-general-escritorio.png),
  [general a horario en escritorio](evidence/general-bloquea-horario-escritorio.png),
  [horario a general en móvil](evidence/horario-bloquea-general-movil.png) y
  [general a horario en móvil](evidence/general-bloquea-horario-movil.png).
  [Resultados del navegador](evidence/browser-results.json).
- Validador documental: **91 archivos, 14 contratos**; pruebas del flujo documental:
  **13 aprobadas**. `git diff --check` correcto.
- Imágenes backend/frontend actualizadas; ambos servicios Compose saludables.
  No se crearon ni cerraron asistencias reales durante esta corrección.

## Ajuste de la coincidencia temporal

El usuario precisó que el aviso se muestra cuando los ingresos coinciden o tienen
horarios parecidos y eligió un margen de **30 minutos**. Se compara el instante
actual con la franja de la clase, ampliada 30 minutos antes y después de manera
inclusiva. La coincidencia exige una visita pendiente, no una visita con salida.
Registrar la salida libera el ingreso sin un tiempo de espera adicional.

La consulta de matriculados antes ofrecía la salida pendiente de cualquier visita
actual al seleccionar una clase futura o ya terminada. Ahora solo publica esa
acción si la franja ampliada corresponde al instante actual. Cerca de una clase
que todavía no empieza o acaba de terminar, muestra también el motivo temporal
de admisión; el margen no autoriza entradas fuera de la clase. En general se usa
el fin original de la visita de horario, recuperado desde el límite de salida
guardado menos una hora, para que editar el catálogo no desplace el aviso.
Fuera del margen se oculta el aviso cruzado, conservando la visita pendiente y
su acción de salida. Los controles de persistencia y aforo se mantienen.

Regresión adicional en
[test_schedule_attendance.py](../../../../backend/tests/test_schedule_attendance.py):
30 minutos antes/después inclusive, un segundo fuera de cada extremo, inicio,
fin, clase de otra semana, cruce de medianoche y horario editado. La
regresión SSR comprueba que otra fecha no ofrece salida pendiente ni una nueva
entrada habilitada. Las pruebas previas verifican el nuevo ingreso después de
una salida y el bloqueo de una clase incompleta que sigue sin salida.

Verificación del ajuste de 30 minutos:

- Backend completo: **751 aprobadas, 54 omitidas** (integración SQL optativa).
- Frontend completo: **372 aprobadas**; compilación de ambas imágenes correcta.
- Flake8 crítico: **0 errores**; validador: **91 archivos y 14 contratos**;
  pruebas del flujo documental: **13 aprobadas**; `git diff --check` correcto.
- [Revisión visual adicional](evidence/browser-window-review.cjs): cuatro
  escenarios aprobados con API sintética y cero escrituras: otra semana, clase
  terminada y lejana, clase dentro del margen y general fuera del margen.
  [Resultados](evidence/browser-window-results.json),
  [aviso dentro de los 30 minutos](evidence/aviso-margen-30min.png) y
  [sin aviso cruzado fuera del margen](evidence/sin-aviso-general-fuera30.png).
  El primer intento de navegador coincidió con la recreación de Compose y falló
  al conectar; se repitió con ambos servicios saludables y pasó.
- Backend/frontend locales actualizados. No se alteraron horarios, membresías
  o asistencias remotas para verificar el cambio.
