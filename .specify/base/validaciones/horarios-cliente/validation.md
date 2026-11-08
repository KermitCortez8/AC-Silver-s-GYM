# Validación de actualización de horarios del cliente

Fecha: 2026-10-29. Corrección directa de MOD-05; no se activó Spec Kit.

## Síntoma y corrección

El portal consultaba las matrículas al montar /user/schedule (EnrollmentView),
pero no mientras permanecía abierto. El panel /user/dashboard podía reutilizar
respuestas durante los 30 segundos de caché. Además, una lectura comenzada antes
de guardar/cancelar podía sobrescribir el cambio confirmado al llegar después.

Se reutilizan las operaciones existentes: la vista del cliente consulta al montar,
recuperar foco/visibilidad y cada 30 segundos mientras esté visible. El panel fuerza
la lectura al regresar; el control de matrículas descarta lecturas anteriores a
cambios confirmados o a una consulta más reciente. No se recarga la página.
No se consulta automáticamente con pestaña oculta, durante una operación o mientras
está abierto el selector; los eventos y temporizadores se eliminan al desmontar.
Administración mantiene su carga inicial y actualización manual.

Si falla una lectura, se mantiene el último horario válido y se muestra el error
existente. Se conserva el alcance por cliente de la API y el límite de sesión.
No cambian rutas, filtros de calendario, SQL ni contratos HTTP.

## Pruebas

- 31-module-error-control.test.js: 39 aprobados, incluidas tres regresiones nuevas
  para guardar/cancelar con lectura pendiente y respuestas fuera de orden.
- npm test: 265 aprobados, 0 fallos, 0 omitidos.
- npm run build: compilación correcta.
- Validador documental: 60 archivos y 13 contratos válidos; git diff --check sin errores.
- Se conserva la advertencia de antigüedad de Browserslist y avisos de contexto
  Pinia/rutas en pruebas. No se modificaron dependencias.
- Backend no se vuelve a ejecutar: esta corrección solo modifica frontend.

## Revisión de navegador

Chromium/Playwright sobre las rutas reales /user/dashboard y /user/schedule,
con sesión y API sintéticas interceptadas localmente, sin proveedores externos.
El reloj controlado permite comprobar 31 segundos de refresco sin esperas reales.

Se verifica agregar una matrícula fuera de la sesión visible, recuperar foco y
ver la clase; regresar al panel antes de vencer su caché con otra clase agregada;
cancelar fuera de la sesión y actualizar por intervalo; mantener el último horario
ante HTTP 503. Sin errores de página ni desbordamiento horizontal en móvil.

- [Horario actualizado, escritorio oscuro 1440×1000](evidence/horario-actualizado-escritorio.png).
- [Horario actualizado, móvil claro 390×844](evidence/horario-actualizado-movil.png).
- [Resultados](evidence/browser-results.json) y [script](evidence/browser-review.cjs).

Para reproducir: Vite en 127.0.0.1:5173 con VITE_AUTH_API_BASE_URL=/api; ejecutar
el script con Playwright instalado fuera del repositorio en
/tmp/gym-attendance-browser/node_modules/playwright o mediante GYM_PLAYWRIGHT_MODULE.
No se necesita una migración adicional para esta corrección. La caché del backend
mantiene su TTL de cinco segundos; no se certifican datos ni despliegues remotos.
El servidor Vite utilizado para revisar se detuvo al terminar.
