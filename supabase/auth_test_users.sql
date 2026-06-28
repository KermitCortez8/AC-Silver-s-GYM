-- Ejecutar completo en Supabase SQL Editor.
-- Crea columnas necesarias para login por correo/password y agrega usuarios de prueba.

alter table public."CLIENTES"
  add column if not exists password_hash text not null default '';

alter table public."USUARIO"
  add column if not exists "Nombre" text not null default '',
  add column if not exists "Correo" text not null default '',
  add column if not exists "Telefono" text not null default '';

create index if not exists "CLIENTES_Correo_idx" on public."CLIENTES" ("Correo");
create index if not exists "USUARIO_Correo_idx" on public."USUARIO" ("Correo");

select setval(
  pg_get_serial_sequence('public."CLIENTES"', 'id_cliente'),
  greatest((select coalesce(max("id_cliente"), 0) from public."CLIENTES"), 1),
  true
);

select setval(
  pg_get_serial_sequence('public."MEMBRESIA"', 'id_membresia'),
  greatest((select coalesce(max("id_membresia"), 0) from public."MEMBRESIA"), 1),
  true
);

select setval(
  pg_get_serial_sequence('public."USUARIO"', 'id_usuario'),
  greatest((select coalesce(max("id_usuario"), 0) from public."USUARIO"), 1),
  true
);

delete from public."MEMBRESIA"
where "id_cliente" in (
  select "id_cliente"
  from public."CLIENTES"
  where "DNI" = '99999991'
     or lower("Correo") = lower('cliente.prueba@acsilversgym.com')
     or lower("Email") = lower('cliente.prueba@acsilversgym.com')
);

delete from public."CLIENTES"
where "DNI" = '99999991'
   or lower("Correo") = lower('cliente.prueba@acsilversgym.com')
   or lower("Email") = lower('cliente.prueba@acsilversgym.com');

delete from public."USUARIO"
where "DNI" = '99999990'
   or lower("Correo") = lower('admin.prueba@urp.edu.pe');

insert into public."PLANES_MEMBRESIA" ("Nombre_Plan", "Duración", "Precio", "Activo")
values ('MENSUAL', '30 dias', 80, true)
on conflict ("Nombre_Plan") do update set
  "Duración" = excluded."Duración",
  "Precio" = excluded."Precio",
  "Activo" = excluded."Activo";

with nuevo_cliente as (
  insert into public."CLIENTES" (
    "Nombres",
    "Apellidos",
    "DNI",
    "Telefono",
    "Email",
    "Correo",
    password_hash,
    "Fecha_Registro",
    "Estado",
    "Plan"
  )
  values (
    'Cliente',
    'Prueba',
    '99999991',
    999999991,
    'cliente.prueba@acsilversgym.com',
    'cliente.prueba@acsilversgym.com',
    'pbkdf2_sha256$11111111111111111111111111111111$854384651f94973159da3dcda5b3113160a92c1f032144a8ef9f36254e902426',
    current_date,
    true,
    'MENSUAL'
  )
  returning "id_cliente"
),
plan_mensual as (
  select "id_PM"
  from public."PLANES_MEMBRESIA"
  where "Nombre_Plan" = 'MENSUAL'
  limit 1
)
insert into public."MEMBRESIA" (
  "Fecha_Inicio",
  "Fecha_Fin",
  "Estado",
  "id_cliente",
  "id_PM"
)
select
  current_date,
  current_date + interval '30 days',
  'Activa',
  nuevo_cliente."id_cliente",
  plan_mensual."id_PM"
from nuevo_cliente, plan_mensual;

insert into public."USUARIO" (
  "Nombre",
  "Correo",
  "Telefono",
  "DNI",
  "Contraseña",
  "Rol",
  "Estado"
)
values (
  'Admin Prueba',
  'admin.prueba@urp.edu.pe',
  '999999990',
  '99999990',
  'pbkdf2_sha256$22222222222222222222222222222222$7e8a18f1cc65e5cf0bf9500753c5e3cbd0689c02e56278d5f63dceac1d530520',
  'admin',
  true
);
