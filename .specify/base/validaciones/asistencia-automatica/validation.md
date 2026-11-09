# Asistencia incompleta y cierre general automático

## Síntoma y criterios

La clase sin salida superaba su fin más una hora y mostraba Incompleta al leer,
pero no guardaba por sí sola el estado. Las visitas generales podían permanecer
abiertas indefinidamente. El usuario definió dos reglas distintas:

- Clases: después del fin original más una hora sin salida, guardar Incompleta;
  mantener la visita abierta y su aforo ocupado hasta registrar la salida real.
- Gimnasio general: después de tres horas desde la entrada sin salida, cerrar
  automáticamente como Incompleta y liberar aforo. Exactamente a las tres horas
  todavía permite una salida manual completada.

## Implementación

021 añade el estado persistido y el trigger de coherencia. 022 programa la revisión
cada diez segundos, independiente del navegador y del backend. 023 añade
`cierre_automatico` y fija el plazo general desde la entrada; recupera también
las generales históricas abiertas, incluidas las que cruzan medianoche.
Las generales históricas ya cerradas conservan su clasificación.

El cierre general guarda la fecha y hora límite como cierre administrativo, no
como una salida real observada. Registra al Sistema como responsable e incrementa
la versión porque cambia la salida y el aforo. Reintentar una salida devuelve la
primera salida guardada; una solicitud de ingreso nueva permite otra visita.
La corrección con motivo reconstruye la salida real y conserva el evento anterior.

Los dos procesos usan el bloqueo de `guardar_asistencia`. La transición de estado
de clase no altera su versión de edición; el cierre general sí. Consultas y
operaciones reconcilian mediante la misma función privada y el reloj de la base.
Después de reconciliar se invalida únicamente la caché de asistencia, incluso si
el cron ya cerró la visita y la llamada devuelve cero; no se conserva una tarjeta
abierta obsoleta ni se recargan módulos ajenos.

El historial, Excel, la ficha general y la semana del cliente identifican el cierre
automático. El cliente sigue limitado a sus registros, sin edición ni auditoría interna.

## Aplicación y recuperación

Orden por nombre de dependencias: 005_harden_attendance.sql,
013_general_attendance.sql, 018_attendance_schedule_exit_deadline.sql,
019_schedule_sessions.sql (si se usan sesiones por fecha),
021_persist_attendance_status.sql, 022_attendance_status_cron.sql y
023_general_attendance_three_hour_close.sql. No aplicar los SQL indiscriminadamente
por orden alfabético. El despliegue repetido no duplica cierres ni trabajos de cron.

La ejecución automática requiere pg_cron y la base operativos. No requiere backend
ni pantalla abiertos. Se materializa en la primera revisión posterior al plazo,
con una frecuencia de diez segundos; una consulta también reconcilia lo vencido.

Recuperación: pausar o eliminar solo `silver-gym-incomplete-attendance` para detener
la automatización. Conservar el backend compatible con `cierre_automatico`, las horas
ya guardadas y la auditoría. Si se restaura la función de 021, conservar ese campo
para distinguir los cierres existentes. No convertir sus horas en salidas reales
ni restaurar un backend que ignore ese indicador sin una adaptación previa.

## Verificación local

- Backend completo: 698 aprobadas y 44 omitidas. Las omitidas son pruebas SQL
  optativas sin la variable de contenedor; se ejecutaron aparte.
- Cinco módulos PostgreSQL juntos: 43 aprobadas en un contenedor desechable sin red.
  Incluyen ejecución real de pg_cron sin navegador, clases y cierre general.
- Regresiones de asistencia general y automatización, incluido el caso adicional
  de carrera entre cierre y salida manual: 48 aprobadas. Se añadió y comprobó
  además la invalidación de caché cuando el cron ya procesó el cierre; esa revisión
  junto con asistencia y refresco Supabase obtuvo 79 aprobadas.
- Frontend: 353 aprobadas y compilación de producción aprobada.
- Control Python E9/F63/F7/F82: 0 errores. Validador documental: 87 archivos válidos.
  Pruebas aisladas del flujo: 13 aprobadas. `git diff --check`: aprobado.
- Word: versiones 1.2 de ECUS 14–17 con filas alternadas; índice y páginas revisados
  mediante renderizado, con capturas actuales y datos ficticios.

Evidencia visual de la interfaz real con respuestas simuladas:
[ficha cerrada](evidence/general-cierre-tres-horas.png),
[aforo liberado](evidence/general-aforo-liberado.png),
[historial administrativo](evidence/general-historial-cierre.png),
[corrección](evidence/general-corregir-cierre.png),
[historial del cliente](evidence/cliente-historial-cierre.png),
[semana del cliente](evidence/cliente-semana-cierre.png) y
[resultado](evidence/three-hour-browser-results.json).

Las capturas previas de visitas generales aún abiertas con estado sintético
incompleto se sustituyeron al definirse la regla final de cierre a las tres horas.
No se aplicaron migraciones ni cambios a una base de producción.

Referencia del programador:
[Supabase Cron](https://supabase.com/docs/guides/cron/quickstart).
