-- Requiere HORARIOS_SERVICIO y su persistencia con commit_gym_transaction.
-- Las clases previas quedan pendientes de asignar sala. La columna se puede
-- conservar al revertir la aplicación para recuperar las asignaciones.
begin;

alter table public."HORARIOS_SERVICIO"
  add column if not exists sala text
    check (sala = btrim(sala) and char_length(sala) between 1 and 50);

notify pgrst, 'reload schema';
commit;
