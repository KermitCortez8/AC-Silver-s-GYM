# Modelo de datos conservado

CLIENTES tiene identidad estable, estado y credenciales privadas. MEMBRESIA pertenece
al cliente y al plan; conserva monto_pago, estado_pago, referencia, método y fecha de pago.
Transiciones: EN_TRAMITE/PENDIENTE -> EN_TRAMITE/PAGADO -> ACTIVO/PAGADO -> VENCIDA/PAGADO.
Pago y activación tienen comandos separados. La edición genérica no reemplaza compras
confirmadas ni cambia propietario. Una pendiente editada conserva fechas vacías.

HORARIOS_SERVICIO utiliza un día de lunes a domingo, horas canónicas HH:MM y duración
exacta de 60 o 120 minutos. MATRICULAS_HORARIO ocupa y libera cupos con RPC existente.
ASISTENCIA usa membresía vigente y el reloj del servidor en America/Lima.
No se añaden columnas, tablas, índices ni migraciones.
