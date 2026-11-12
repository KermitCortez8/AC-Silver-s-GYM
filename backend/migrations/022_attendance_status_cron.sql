-- Dependencia: 021_persist_attendance_status.sql; PostgreSQL con pg_cron disponible.
-- Ejecutar con el propietario de la BD después de 021. No requiere una pantalla,
-- peticiones HTTP ni que el backend permanezca encendido.
-- Recuperación: select cron.unschedule('silver-gym-incomplete-attendance');
-- Conservar la función, el estado persistido y sus auditorías.
begin;
create extension if not exists pg_cron;
select cron.schedule('silver-gym-incomplete-attendance', '10 seconds',
  'select public.marcar_asistencias_incompletas();');
commit;
