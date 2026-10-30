# Decisiones de investigación

- Decisión: reutilizar membership_current para asistencia. Motivo: autenticación ya valida
  fechas civiles; comparar texto acepta fechas imposibles. Alternativa descartada: otro parser.
- Decisión: rechazar edición genérica de compra confirmada. Motivo: el reemplazo borra
  pago e importe y permite cambiar dueño. Las renovaciones son registros nuevos.
- Decisión: conservar formatos AM/PM al leer, canonizar al guardar. Motivo: las asistencias
  consumen time.fromisoformat. La validación HTTP actual no cubre llamadas directas de dominio.
- Decisión: no sustituir cero por precio actual. Motivo: preservar importe contratado;
  conservar fallback solo para importe histórico ausente o null.
- Decisión: pruebas locales con reloj fijo y adaptadores en memoria. Motivo: reproducibilidad
  sin secretos ni efectos externos. No hay ambigüedades de aceptación por resolver.
