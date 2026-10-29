# Datos, dominio y Supabase

Consultar [arquitectura](../../docs/arquitectura.md), [constitución](../../memory/constitution.md)
y [DoD](../../docs/DoD.md).

- Preservar reglas, modelos, identidad estable, historial de pagos e importes
  guardados, incluso cuando sean cero. Mantener redondeo e idempotencia existentes.
- Usar fechas de negocio `America/Lima`, con vigencia inclusiva del día final.
- Mantener RPC especializadas de matrículas/asistencia y `commit_gym_transaction`
  para las demás operaciones soportadas. Un fallo no habilita escrituras REST parciales.
- Declarar recursos de lectura/escritura y conservar control de concurrencia,
  recarga y mappers completos; no utilizar atributos privados entre servicios.
- Toda migración identifica esquema previo, dependencias por nombre, orden,
  recuperación y prueba aislada. No ejecutar todos los SQL por orden alfabético.
- Supabase es externo al Compose de aplicación. El volumen de imágenes locales
  no es copia de la base. Los cambios SQL y despliegues de Edge se gestionan aparte.
