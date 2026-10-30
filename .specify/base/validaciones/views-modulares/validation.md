# Validación de vistas modulares

Fecha: 2026-10-30.

Petición: reducir las vistas a un máximo de 500 líneas separando sus responsabilidades.
La separación conserva los cambios previos de calendario de asistencia y matrículas
por fecha. No cambia contratos de API ni requiere migraciones adicionales.

## Separación

Las 31 vistas cumplen el límite. Las 13 que lo superaban delegan su estado y sus
acciones en composables de presentación por módulo. El panel separa también sus
gráficos. Los editores de rutinas y promociones y los listados de tienda tienen
componentes propios con props y eventos. Los estilos extraídos conservan el alcance
de Vue y se comparten con sus componentes cuando corresponde.

| Vista | Antes | Después |
| --- | ---: | ---: |
| ClientsView | 669 | 490 |
| EnrollmentView | 670 | 340 |
| HomeView | 821 | 307 |
| InventoryMovementsView | 856 | 479 |
| InventoryView | 765 | 448 |
| LandingView | 728 | 416 |
| LoginView | 601 | 301 |
| PromotionsView | 823 | 268 |
| RegisterView | 761 | 385 |
| ServiceSchedulesView | 785 | 380 |
| StoreView | 997 | 335 |
| TrainerRoutinesView | 975 | 276 |
| UsersView | 659 | 428 |

El recuento incluye líneas vacías. La prueba de arquitectura
`frontend/tests/23-layer-boundaries.test.js` comprueba el límite en todas las vistas.
Los componentes y composables nuevos también quedan por debajo de 500 líneas.

## Comprobaciones

- `npm test` en `frontend`: 271 pruebas correctas, incluidas las pruebas existentes
  de formularios, errores, calendario, matrículas y asistencia y el nuevo límite.
- `npm run build` en `frontend`: compilación correcta.
- `git diff --check`: sin errores de formato.
- `python .specify/.codex/hooks/validate.py`: documentación válida.
- `python -B -m unittest discover -s .specify/tests -v`: 13 pruebas correctas.

## Revisión en navegador

El [recorrido reproducible](evidence/browser-review.cjs) usa Chromium, reloj fijo,
sesiones y respuestas API sintéticas. Bloquea solicitudes a servicios externos.
Compara el contenido visible y captura las 13 vistas antes y después; tienda se
revisa con roles administrador y cliente (14 casos). La vista histórica de movimientos,
cuya ruta habitual redirige a inventario, se monta en una ruta temporal de revisión.
El contenido visible coincide en los 14 casos. Trece pares de capturas son PNG
idénticos; en clientes solo difieren diez píxeles del borde de paginación, con una
unidad de intensidad por canal. Los hashes y diferencias quedan en
[la comparación visual](evidence/visual-comparison.json).

Los recorridos interactivos comprueban búsqueda y editor de productos, favoritos,
cantidades y vaciado del carrito móvil, guardado de una rutina con ejercicio y
guardado de una promoción. Comprueban también errores de página, avisos de Vue sobre
props y ausencia de desbordamiento horizontal en el carrito móvil. Las escrituras
se inspeccionan sobre la API simulada; no acreditan integraciones externas.
El [resultado del recorrido](evidence/browser-results.json) registra 14 casos
correctos, ambas escrituras simuladas y ningún error de página ni aviso de Vue.
Se conservan capturas del [editor de tienda](evidence/tienda-editor.png),
el [carrito móvil](evidence/tienda-cliente-movil.png), el
[editor de rutinas](evidence/rutina-editor.png) y el
[editor de promociones](evidence/promocion-editor.png).

Para repetir con las dependencias del frontend instaladas:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
```

En otra terminal, con Playwright/Chromium instalado fuera del repositorio:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/views-modulares/evidence/browser-review.cjs
```

La comparación requiere una copia de las vistas previa a la separación, guardada
fuera del repositorio. Configurar `GYM_VIEWS_BASELINE_DIR` al arrancar el servidor y
`GYM_VIEWS_BASELINE_URL=http://127.0.0.1:5175` al ejecutar el recorrido. Sin esa copia,
se ejecutan las comprobaciones sobre el código actual. Las capturas comparadas
se guardan en `/tmp/gym-views-visual`.
