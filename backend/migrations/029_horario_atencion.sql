-- Aplicar después de 019_schedule_sessions.sql y de la instalación de
-- commit_gym_transaction y gym_identity_counters (015, o su versión posterior).
-- Conserva los horarios vinculados como inactivos. Respaldar HORARIOS_SERVICIO
-- antes de aplicar si se requiere recuperar las filas eliminadas.
begin;

create or replace function public.horario_servicio_en_atencion(
  p_dia text, p_inicio text, p_fin text
) returns boolean language plpgsql immutable set search_path = pg_catalog as $$
declare
  dia text := translate(lower(btrim(p_dia)), 'áéíóú', 'aeiou');
  apertura time;
  cierre time;
  inicio time;
  fin time;
begin
  if dia in ('lunes', 'martes', 'miercoles', 'jueves', 'viernes') then
    apertura := time '06:00';
    cierre := time '22:00';
  elsif dia in ('sabado', 'domingo') then
    apertura := time '07:00';
    cierre := time '18:00';
  else
    return false;
  end if;

  -- Admite horas históricas con AM/PM, incluidas «7 a. m.» y «7 PM».
  inicio := regexp_replace(regexp_replace(lower(btrim(p_inicio)), '([ap])\.\s*m\.?', '\1m'),
                           '^([0-9]{1,2})(\s*[ap]m)?$', '\1:00\2')::time;
  fin := regexp_replace(regexp_replace(lower(btrim(p_fin)), '([ap])\.\s*m\.?', '\1m'),
                        '^([0-9]{1,2})(\s*[ap]m)?$', '\1:00\2')::time;
  return coalesce(apertura <= inicio and inicio < fin and fin <= cierre, false);
exception when invalid_datetime_format or datetime_field_overflow then
  return false;
end;
$$;

revoke all on function public.horario_servicio_en_atencion(text, text, text) from public, anon, authenticated;
grant execute on function public.horario_servicio_en_atencion(text, text, text) to service_role;

lock table public."ASISTENCIA", public."HORARIOS_SERVICIO", public."MATRICULAS_HORARIO"
  in share row exclusive mode;

with retirados as (
  delete from public."HORARIOS_SERVICIO" h
  where not public.horario_servicio_en_atencion(h.dia::text, h.hora_inicio::text, h.hora_fin::text)
    and not exists (select 1 from public."MATRICULAS_HORARIO" m where m.id_horario_servicio = h.id_horario_servicio)
    and not exists (select 1 from public."ASISTENCIA" a where a.id_horario_servicio = h.id_horario_servicio)
    -- Una referencia adicional del esquema podría tener un borrado en cascada.
    and not exists (
      select 1 from pg_constraint
      where contype = 'f' and confrelid = 'public."HORARIOS_SERVICIO"'::regclass
        and conrelid not in ('public."MATRICULAS_HORARIO"'::regclass, 'public."ASISTENCIA"'::regclass)
    )
  returning h.id_horario_servicio
)
insert into public.gym_identity_counters as c (table_name, last_id)
select 'HORARIOS_SERVICIO', max(id_horario_servicio) from retirados having count(*) > 0
on conflict (table_name) do update set last_id = greatest(c.last_id, excluded.last_id);

update public."HORARIOS_SERVICIO"
set activo = false
where activo is distinct from false
  and not public.horario_servicio_en_atencion(dia::text, hora_inicio::text, hora_fin::text);

alter table public."HORARIOS_SERVICIO"
  drop constraint if exists horario_servicio_dentro_de_atencion,
  add constraint horario_servicio_dentro_de_atencion check (
    activo is false or public.horario_servicio_en_atencion(dia::text, hora_inicio::text, hora_fin::text)
  );

notify pgrst, 'reload schema';
commit;
