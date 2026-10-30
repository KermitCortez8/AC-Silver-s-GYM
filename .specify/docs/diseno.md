# Diseño de la interfaz existente

Base observada: 2026-10-29. Este documento describe patrones presentes en el
código; no constituye una evaluación nueva de accesibilidad o de apariencia.

## Navegación y áreas

La navegación está en [router/index.js](../../frontend/src/presentation/router/index.js).
Hay páginas públicas de inicio, nosotros, preguntas frecuentes, registro y pago;
`/auth/callback` resuelve el retorno de autenticación. `/tp-remix` es una ruta
pública adicional existente, sin reglas de negocio propias en el backend.

| Área | Pantallas y acceso visual |
| --- | --- |
| `/admin` | Panel, usuarios, clientes, planes, promociones, pagos, horarios, matrículas, inventario, tienda y pedidos. `staff` comparte el panel según sus guards. |
| `/admin/attendance` | Control administrativo de asistencia, restringido a `admin`. |
| `/trainer` | Resumen, catálogo de rutinas y monitor de asignación/progreso. |
| `/user` | Panel personal, tienda/pago, horarios/matrículas e historial de asistencia. |

Los guards visuales ayudan a navegar; la autorización efectiva se define en
el [servidor](../.codex/rules/seguridad.md). Los redirects históricos de inventario, configuración
y matrículas se conservan en el router.

## Componentes y patrones a reutilizar

- [AppShell.vue](../../frontend/src/presentation/components/AppShell.vue): marco de paneles.
- [WorkspaceDialog.vue](../../frontend/src/presentation/components/WorkspaceDialog.vue)
  y [ConfirmDialog.vue](../../frontend/src/presentation/components/ConfirmDialog.vue):
  diálogos y confirmaciones.
- [StatCard.vue](../../frontend/src/presentation/components/StatCard.vue): indicadores.
- Componentes especializados en `components/attendance/`, `clients/`, `inventory/`,
  `store/` y `trainer/`, con composables de presentación para formularios y acciones.
- [ScheduleWeekPicker.vue](../../frontend/src/presentation/components/ScheduleWeekPicker.vue),
  [ScheduleTimeGrid.vue](../../frontend/src/presentation/components/ScheduleTimeGrid.vue)
  y [ExcelScheduleGrid.vue](../../frontend/src/presentation/components/ExcelScheduleGrid.vue):
  selección semanal y visualización de horarios.

Los servicios de aplicación coordinan cargas y mutaciones. La infraestructura
resuelve HTTP y almacenamiento. Una vista nueva debe seguir ese mecanismo y
reflejar carga, vacío, éxito y error según el comportamiento solicitado.

## Colores y temas

Los tokens globales están en [style.css](../../frontend/src/presentation/style.css):

| Token | Tema oscuro | Tema claro |
| --- | --- | --- |
| `--app-canvas` | `#151515` | `#f1f5f9` |
| `--app-text` | `#fafafa` | `#0f172a` |
| `--app-accent` | `#dc2626` | `#dc2626` |
| `--app-accent-hover` | `#b91c1c` | `#b91c1c` |

`data-theme` selecciona el tema; las páginas públicas fuerzan su esquema claro.
[workspace.css](../../frontend/src/presentation/styles/workspace.css) aporta los
tokens `--ws-*` y estados semánticos de paneles. Los estilos de asistencia,
clientes, tienda y entrenador mantienen su alcance por pantalla.

## Verificación de cambios visuales

Conservar los patrones de temas, adaptación móvil y diálogos existentes.
Verificar la pantalla afectada en escritorio/móvil y claro/oscuro cuando aplique.
Registrar las dimensiones y capturas del cambio. Las pruebas SSR de flujos
no sustituyen una revisión en navegador.
