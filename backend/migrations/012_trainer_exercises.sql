-- Persistencia de ejercicios del catálogo y detalle de las sesiones de rutina.
-- Ejecutar en Supabase antes de usar el editor y el seguimiento de ejercicios.
-- IF NOT EXISTS conserva las columnas y los datos de instalaciones ya actualizadas.
begin;

alter table public."CATALOGO_RUTINA"
    add column if not exists ejercicios jsonb not null default '[]'::jsonb;

alter table public."RUTINA_PROGRESO"
    add column if not exists ejercicios_detalle jsonb not null default '[]'::jsonb;

notify pgrst, 'reload schema';
commit;
