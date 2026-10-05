-- Datos ficticios de prueba. Ejecutar después de 008 en Supabase > SQL Editor.
-- Agrega únicamente nombres que no existan; no reajusta precios ni repone stock al repetir.
-- El precio se guarda en TIENDA_PRODUCTOS, según el esquema remoto existente.
begin;
lock table public."INVENTARIO", public."TIENDA_PRODUCTOS", public."MOV_INV" in share row exclusive mode;
do $$
declare
  producto record;
  nuevo_item bigint;
  nuevo_producto bigint;
  nuevo_mov bigint;
  nuevo_activo bigint;
  secuencia text;
  tabla text;
  columna text;
begin
  for producto in
    select * from (values
      ('Agua mineral 625 ml', 'Bebidas', 2.50, 60),
      ('Bebida isotónica 500 ml', 'Bebidas', 5.00, 36),
      ('Barra proteica 60 g', 'Snacks', 8.00, 30),
      ('Proteína whey 1 kg', 'Suplementos', 150.00, 8),
      ('Creatina monohidratada 300 g', 'Suplementos', 85.00, 10),
      ('Shaker 600 ml', 'Accesorios', 20.00, 20),
      ('Toalla deportiva de microfibra', 'Accesorios', 18.00, 25),
      ('Guantes de entrenamiento', 'Accesorios', 35.00, 15),
      ('Banda elástica de resistencia', 'Accesorios', 25.00, 18),
      ('Cuerda para saltar', 'Accesorios', 22.00, 15)
    ) as datos(nombre, categoria, precio, stock)
  loop
    if exists (select 1 from public."TIENDA_PRODUCTOS" where lower(btrim("nombre_Producto")) = lower(producto.nombre)) then
      continue;
    end if;
    -- No reutiliza un ítem ambiguo o un equipo del gimnasio por coincidencia de nombre.
    if exists (select 1 from public."INVENTARIO" where lower(btrim("Nombre_item")) = lower(producto.nombre)) then
      raise notice 'Omitido: % ya existe en Inventario. Vincular desde Tienda.', producto.nombre;
      continue;
    end if;
    select coalesce(max(id_item),0)+1, coalesce(max("N_ACTIVO"),0)+1 into nuevo_item, nuevo_activo from public."INVENTARIO";
    select coalesce(max(id_producto),0)+1 into nuevo_producto from public."TIENDA_PRODUCTOS";
    select coalesce(max(id_mov),0)+1 into nuevo_mov from public."MOV_INV";
    insert into public."INVENTARIO" (id_item, "Nombre_item", "Tipo", "Cantidad_Stock_E", "Estado", "N_ACTIVO")
    values (nuevo_item, producto.nombre, 'Tienda', producto.stock, 'Disponible', nuevo_activo);
    insert into public."TIENDA_PRODUCTOS" (id_producto, id_item, "nombre_Producto", categoria, "precio_Venta", cantidad_stock, stock_minimo, imagen_url)
    values (nuevo_producto, nuevo_item, producto.nombre, producto.categoria, producto.precio, producto.stock, 5, '');
    insert into public."MOV_INV" (id_mov, id_item, id_usuario, tipo_movimiento, fecha_movimiento, descripcion, cantidad)
    values (nuevo_mov, nuevo_item, null, 'entrada', current_date, '[009] Productos de prueba: saldo inicial', producto.stock);
  end loop;
  for tabla, columna in select * from (values ('INVENTARIO','id_item'), ('TIENDA_PRODUCTOS','id_producto'), ('MOV_INV','id_mov')) as claves(tabla,columna)
  loop
    secuencia := pg_get_serial_sequence(format('public.%I', tabla), columna);
    if secuencia is not null then
      execute format('select setval(%L, greatest(coalesce(max(%I),0),1)) from public.%I', secuencia, columna, tabla);
    end if;
  end loop;
end
$$;
commit;
