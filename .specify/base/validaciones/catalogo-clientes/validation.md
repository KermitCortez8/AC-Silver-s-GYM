# Validación del catálogo en los formularios de clientes

Fecha: 2026-10-30.

## Problema observado

El modal de la captura corresponde a `ClientEditorDialog.vue`, usado desde
`/admin/clients` al editar o dar de alta un cliente. Sus planes estaban fijados
en MENSUAL, 3 MESES y ANUAL, aunque la sección cargaba catálogos remotos. Las
promociones no se filtraban completamente por plan e inicio de vigencia.
Además, el guardado de datos personales reemplazaba su descriptor por SIN PROMOCION.

El registro público consultaba `/planes-membresia` y `/promociones/vigentes-publico`,
pero un fallo o una lista vacía activaban tres planes locales con precios propios.

## Corrección

- Servicio compartido de catálogo con validación de listas, IDs, nombres, precios
  y descuentos; usa los endpoints del backend, cuya persistencia es Supabase.
- Cada apertura administrativa recarga planes y promociones. Las altas muestran
  planes activos y promociones aplicables por plan, fechas, estado y cupos.
- Indicadores de carga, errores con reintento y bloqueo del alta hasta contar con
  un catálogo válido. El borrador se conserva; no se inventan planes ni precios.
- La edición personal muestra y conserva plan, promoción e importe contratados,
  incluido cero. No permite simular cambios financieros mediante selectores que
  antes no actualizaban la membresía. Conserva opciones históricas retiradas.
- El registro público usa el mismo catálogo, con promociones vigentes
  y precios mostrados calculados con el redondeo existente. El servidor sigue
  validando y calculando el importe final del registro.
- Las respuestas posteriores al desmontaje o de otra sesión no publican datos.

No hay cambios de esquema, permisos, cobros ni renovaciones en el backend.

## Lectura de Supabase

Se consultaron únicamente PLANES_MEMBRESIA y PROMOCIONES con la configuración privada
del backend, sin guardar credenciales ni filas de clientes. La lectura confirmó
4 planes y 5 promociones. Se aplicaron sus mappers reales para comprobar el contrato:
los nombres remotos como `Nombre_Plan`, `Duración` e `id_PM` se convierten a los
campos que consume el frontend. [Resultado de solo lectura](evidence/supabase-read.json).
La API local no estaba arrancada; la revisión HTTP del frontend usa respuestas
sintéticas. Esta lectura no certifica guardados ni pagos sobre datos reales.

## Regresión y navegador

Las pruebas de [client-catalog.test.js](../../../../frontend/tests/clientes/interfaz/client-catalog.test.js)
cubren planes personalizados, filtros y descuentos, cambio de plan, errores y
reintentos, preservación de valores históricos/cero, guardado del descriptor de
promoción, catálogo vacío/inválido y respuestas tardías.

Comprobaciones ejecutadas:

- `npm test` en `frontend`: 288 pruebas correctas, incluidas 8 regresiones nuevas.
- `npm run build` en `frontend`: compilación correcta.
- `git diff --check`: sin errores de formato.
- `python .specify/.codex/hooks/validate.py`: documentación válida.
- Las 31 vistas siguen bajo el máximo de 500 líneas.

El [recorrido en navegador](evidence/browser-review.cjs) verifica el modal exacto
de edición, la apertura del catálogo, selecciones e importe registrados y guardado
personal. Comprueba alta administrativa con plan personalizado y promoción,
cambio de plan y limpieza de una promoción incompatible, y errores/reintentos con
borrador conservado. En móvil revisa el registro público con catálogo, fallo y
lista vacía. [Resultados](evidence/browser-results.json): cinco escenarios correctos,
sin errores de página; solo escrituras simuladas.

Capturas revisadas: [editar cliente](evidence/editar-cliente.png),
[alta administrativa](evidence/nuevo-cliente.png),
[error de catálogo](evidence/error-catalogo.png) y
[registro público móvil](evidence/registro-publico-movil.png).

Para repetir con Playwright/Chromium y dependencias del frontend instaladas,
arrancar desde la raíz:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
```

En otra terminal:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/catalogo-clientes/evidence/browser-review.cjs
```

## Alta administrativa con un plan de un día

Se reprodujo HTTP 422 con el plan activo `CLASE` porque el esquema de alta
limitaba los nombres a tres opciones. El endpoint ahora acepta el nombre
del plan y comprueba su disponibilidad en el catálogo antes de guardar.
Pasaron las 44 pruebas de alta y pago inicial. La regresión verificó HTTP 201
para `CLASE` con y sin Stripe simulado, un importe de S/ 12 y el rechazo de
planes inactivos o inexistentes antes de escribir.

## Alta pública con un plan de un día

El registro público también devolvía HTTP 422 para el plan activo `CLASE`.
El esquema acepta el nombre y la reserva de la cotización verifica que el
plan exista y esté activo. La prueba de Mercado Pago confirmó el enlace del
importe reservado con persistencia en memoria y comprobó que los planes
inactivos o inexistentes no crean solicitudes.

Las suites de clientes y membresías y pagos completaron 181 pruebas y omitieron
8 que requieren PostgreSQL. Tras reiniciar la API local, se comprobó la salud
a través del proxy de Vite y el esquema actualizado en OpenAPI.

## DNI en las altas pública y administrativa

Los formularios limitan el campo DNI a ocho caracteres y muestran un error
si contiene separadores o no tiene ocho dígitos. El servidor devuelve la
validación de DNI en su propio campo. Se conservan los ceros iniciales.
Pasaron 255 pruebas del backend, con 8 omisiones de PostgreSQL. Pasaron la
suite de frontend y la compilación de Vite.

## Avisos superpuestos en Clientes · 2026-11-26

El aviso del directorio se mostraba como un bloque que movía el contenido de la
página y quedaba detrás de los diálogos. Ahora se muestra superpuesto con un
botón de cierre. Detalles y Solicitudes de pago muestran el aviso dentro del
diálogo cuando corresponde. Las validaciones de formularios siguen visibles
junto a la acción que se debe corregir.

Chromium con API simulada verificó a 1440 y 390 px el error de borrado sin
desplazar el directorio, la confirmación manual y la confirmación de una solicitud
sin duplicar el aviso al cerrar el diálogo. Pasaron las 456 pruebas del frontend,
la compilación y el validador documental.
