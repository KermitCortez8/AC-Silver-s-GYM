# Diseño de la gestión de membresías

## Alcance

Se rediseñó `/admin/plans` sobre los componentes, colores y variables de tema del
panel. El encabezado resume planes registrados, activos e inactivos. Las tarjetas
presentan nombre, disponibilidad, duración, importe en soles, descripción y
beneficios, con acciones de editar y eliminar. La disposición se adapta a móvil
y escritorio, con temas claro y oscuro y foco visible para teclado.

La búsqueda local ignora tildes y consulta nombre, duración, descripción y
beneficios; se combina con filtros de disponibilidad y orden por nombre o precio.
Ordenar conserva los precios cero y no altera el catálogo guardado. Los controles
utilizan `SearchInput` y los límites silenciosos existentes.

Se añadieron estados de espera, error con reintento, catálogo vacío y búsqueda sin
coincidencias. Un error de lectura conserva los planes ya disponibles. El borrado
mantiene la confirmación y bloquea nuevas solicitudes mientras está en curso; un
fallo conserva la tarjeta y una confirmación del servidor la retira.

El formulario conserva el selector de duración, las duraciones históricas, precio
cero y validación de campos. Se armonizaron sus colores con el resto de la página.
No se modificaron rutas, permisos, API, reglas económicas ni membresías contratadas.

## Comprobaciones

- `npm test --prefix frontend`: **302 pruebas aprobadas**. Incluye cuatro nuevas
  de búsqueda/filtros, orden con importe cero, control de consultas duplicadas y
  conservación de catálogo/reintento ante fallos.
- `npm run build --prefix frontend`: **aprobado**.
- `node .specify/base/validaciones/diseno-membresias/evidence/browser-review.cjs`:
  **7 escenarios aprobados**, sin errores de JavaScript.
- `node .specify/base/validaciones/formulario-planes/evidence/browser-review.cjs`:
  **6 escenarios aprobados**, sin errores de JavaScript. Conserva el recorrido de
  creación, edición, validación, guardado duplicado y recuperación de error.
- `python .specify/.codex/hooks/validate.py`,
  `python -B -m unittest discover -s .specify/tests -v` y `git diff --check`:
  **aprobados**, con 13 pruebas de integración documental correctas.

La revisión de navegador usa la vista real en Vite y Chromium, API interceptada,
planes y cuentas sintéticas. Se bloquearon conexiones a servicios externos. Las
pruebas de eliminación operan exclusivamente sobre el catálogo simulado.

## Evidencia

[Script reproducible](evidence/browser-review.cjs) y
[resultados de interacción](evidence/browser-results.json). Para repetirlo,
arrancar Vite en `127.0.0.1:5174` con `VITE_AUTH_API_BASE_URL=/api` y disponer de
Playwright/Chromium; el script admite `GYM_FRONTEND_URL` y `GYM_PLAYWRIGHT_MODULE`.

Capturas propias revisadas:

- [Catálogo en escritorio](evidence/catalogo-escritorio.png).
- [Tema oscuro](evidence/catalogo-oscuro.png).
- [Catálogo móvil](evidence/catalogo-movil.png) y [tarjeta móvil](evidence/tarjeta-movil.png).
- [Sin coincidencias](evidence/sin-resultados.png).
- [Error de lectura](evidence/error-carga.png).
- [Catálogo vacío](evidence/catalogo-vacio.png).

Se comprobó además que un nombre de 50 caracteres y descripciones/beneficios de
150 caracteres sin espacios no desbordan las tarjetas en móvil.
La suite backend no se repitió para este cambio de presentación; la comprobación
anterior consta en [relojes y PostgreSQL](../relojes-asistencia/validation.md).
