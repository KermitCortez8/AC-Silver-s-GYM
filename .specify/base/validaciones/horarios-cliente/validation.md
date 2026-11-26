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

## Rendimiento de Horarios y Matrículas · 2026-11-26

El panel exterior podía sincronizar todos los módulos al volver a «Mis horarios».
Matrículas también descargaba el directorio para buscar por DNI y pedía el
historial de asistencia al consultar reservas. El selector de escritorio
cambiaba las opciones de FullCalendar al seleccionar cada clase. La confirmación
de matrícula administrativa podía esperar al proveedor de correo.

Chromium con sesión y API simuladas verificó las consultas de datos, aparte de
la autenticación. Horarios e inscripción administrativa hicieron una lectura
inicial cada uno. El editor pidió dos recursos adicionales al abrirse (rutinas y
parámetros) y el guardado emitió un POST. Buscar un DNI hizo dos lecturas, una
para el cliente y otra para sus matrículas sin asistencias. El portal del cliente
hizo dos lecturas y suspendió la actualización por foco y visibilidad con el
selector abierto. La selección por teclado y ratón conservó los nodos del
calendario. Ambos modales se revisaron visualmente a 1440 × 960 y se comprobó
el guardado de horario y matrícula con datos ficticios.

Frontend: 453 pruebas aprobadas y compilación correcta. Backend: 1123 aprobadas,
68 omitidas. La regresión de rutas comprueba el filtro de asistencia, los permisos
del DNI, la identidad de sesión y la entrega del aviso a la tarea de fondo.
Flake8 crítico sin errores en el código del repositorio, excluyendo `.venv`.
No se midieron tiempos contra Supabase o el proveedor de correo reales.

## Semanas que cruzan de mes · 2026-11-26

El calendario recortaba las sesiones y el conteo al mes seleccionado aunque
la cuadrícula mostraba la semana completa. Ahora el selector, los conteos, la
agenda, la lista y Excel usan el mismo rango inclusivo de lunes a domingo.
El mes elegido se conserva al seleccionar su primera semana.

Chromium con API simulada verificó del 30 de noviembre al 6 de diciembre en
Horarios por servicio, Matrículas, Mis horarios, Asistencia y Mi asistencia.
Se comprobó la consulta de matriculados para el 1 de diciembre, el conteo de
dos visitas al cambiar de mes y las dos fechas en el Excel descargado.
El frontend aprobó 454 pruebas y compiló correctamente. El endpoint de
asistencia personal ya consulta los siete días, por lo que no requirió cambios.

## Avisos superpuestos de Matrículas · 2026-11-26

El directorio de matrícula y el selector reutilizan el aviso superpuesto de
Clientes. El resultado aparece una sola vez en la superficie activa y se
puede cerrar. La exportación de ambos calendarios usa el mismo aviso.

Chromium con API simulada comprobó el aviso al buscar un cliente, el error de
cupo, el alta y la cancelación dentro del selector, y la descarga de Excel con
su aviso en móvil. Pasaron las 457 pruebas del frontend y la compilación.
