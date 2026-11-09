# Borrado de clientes con ventas vinculadas

Fecha: 2026-11-09.

## Síntoma y causa

El borrado devolvía 409 por historial relacionado. La consulta de la cuenta
indicada encontró una venta pagada y una asistencia; no había membresías ni
matrículas. No se modificaron sus datos durante la investigación. El comando
borraba las dependencias de asistencia/membresía, pero dejaba la referencia
de `VENTAS.id_cliente`, que bloqueaba la eliminación de la cuenta.

## Corrección

El comando declara también pedidos, conserva los datos del comprador y
desvincula la cuenta, sin eliminar ventas ni líneas. La migración
[025](../../../../backend/migrations/025_delete_clients_preserve_sales.sql)
añade las copias del comprador que faltaban en el esquema consultado y un
trigger que desvincula las ventas antes del DELETE de cliente. Mantiene la FK
existente: no desactiva su validación. La RPC sigue comprobando las instantáneas,
bloqueando los recursos y revirtiendo todos los cambios si ocurre un fallo.

Los updates de ventas escriben solo campos modificados para no sustituir fechas
o valores históricos nulos por valores normalizados. Las compras conservan
importe, pago, estado, referencias y detalles; el stock no cambia. Una copia
existente del comprador se conserva. El borrado retira las dependencias de la
cuenta contempladas por el comando; no es anonimización del historial comercial.

## Comprobaciones

- [Regresión de dominio](../../../../backend/tests/test_review_regressions.py):
  ventas pagadas y pendientes, comprador histórico, cliente ajeno y reintento.
- [Integración PostgreSQL](../../../../backend/tests/test_client_deletion_postgres.py):
  esquema sin copias y con FK restrictiva, migración repetible, conservación
  exacta de venta/detalles/stock, rollback íntegro y venta concurrente.
- Sin cambios de interfaz: se reutiliza el botón y la confirmación de borrado.

Resultados:

- Suite backend: **733 correctas, 49 omitidas** por requerir PostgreSQL explícito.
- PostgreSQL 16 desechable: **18 correctas**, combinando transacciones existentes
  y las tres regresiones nuevas. Un primer intento encontró dos columnas de
  asistencia ausentes en el fixture; se completó su esquema. La comparación
  exacta detectó también una reescritura de valores históricos normalizados;
  se corrigió para escribir solo los campos modificados y volvió a comprobarse.
- Flake8 crítico: **0 errores**. Validador documental: **89 archivos y 14 contratos**.
- Pruebas del flujo documental: **13 correctas**; `git diff --check` correcto.
- Imagen backend compilada y servicios Compose recreados con el ajuste.
- Diagnóstico del caso externo con el envío de transacciones bloqueado:
  se obtiene `SchemaNotReady` de la migración 025 antes de cualquier escritura.
  No se enviaron correos ni cobros durante estas comprobaciones.

## Aplicación pendiente

La configuración disponible permite usar REST/RPC en Supabase, pero no ejecutar
DDL. La migración 025 debe ejecutarse en su SQL Editor antes de reintentar el
botón de eliminar. Instalarla no borra cuentas ni ventas. No se ha eliminado
el cliente real ni aplicado la migración en la base externa.
