# Frontend

Consultar [diseño](../../docs/diseno.md), [arquitectura](../../docs/arquitectura.md)
y los [módulos](../../base/modulos/README.md).

- Reutilizar componentes y composables de presentación, servicios de aplicación,
  reglas de dominio y repositorios de infraestructura.
- Instalar adaptadores por instancia de Pinia mediante `src/bootstrap.js`.
  Conservar limpieza de datos/cachés y descarte de respuestas al cambiar de sesión.
- Las vistas coordinan interacción mediante capacidades de aplicación; no
  determinan permisos, actor ni confirmación de pagos.
- Mantener navegación, temas, formularios y estados de error/carga existentes.
- Las variables `VITE_*` son públicas y se fijan al compilar. El contenedor
  frontend compila con Node y sirve la web con Nginx; conservar proxy y rutas SPA.
- Verificar comportamiento afectado, build y revisión visual cuando cambie la UI.
