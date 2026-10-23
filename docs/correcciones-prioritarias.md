# Corrección de los 12 hallazgos prioritarios

Fuente: [auditoría completa](auditoria-code-smells.md). Esta entrega corrige los hallazgos 01–12; 13–42 quedan documentados para otra entrega. El PR se mantiene abierto, sin fusionar.

| Hallazgo | Corrección prevista | Estado |
| --- | --- | --- |
| 01 | Permisos en escrituras y pedidos propios del usuario | En curso |
| 02 | Identidad única y estable del usuario, independiente del rol | Pendiente |
| 03 | Persistencia completa de promociones y membresías | Pendiente |
| 04 | Persistencia completa de inventario y productos | Pendiente |
| 05 | Actualizar listas solamente tras confirmar un borrado | Pendiente |
| 06 | Vaciar estado de negocio y descartar respuestas de otra sesión | Pendiente |
| 07 | Precisión monetaria y descuentos consistentes | Pendiente |
| 08 | Calendario y hora civil de Lima | Pendiente |
| 09 | Duración explícita del plan durante la activación | Pendiente |
| 10 | Escrituras atómicas incluyendo borrados y detalles de ventas | Pendiente |
| 11 | Ejecutar IO síncrona fuera del bucle de eventos | Pendiente |
| 12 | Conflictos entre procesos resueltos en la base de datos | Pendiente |

## Aplicación de cambios de base de datos

Se prepararán migraciones SQL y comprobaciones locales. No se aplican cambios a la base de producción desde esta tarea. Aquí se documentarán el orden de despliegue, los requisitos y la validación efectuada.
