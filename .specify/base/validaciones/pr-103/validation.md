# Revisión y resolución de conflictos del PR 103

Fecha: 2026-11-03. Rama del PR: `feat/refeat`; destino: `develop`.
Se incorpora `develop` en la rama del PR. No se integra ni cierra el PR.

## Resolución

Nueve archivos presentaban conflictos. Se conserva la separación de vistas y
composables, trasladando a estos últimos las validaciones en vivo de Inventario
y la navegación a Papelera. Se conservan la restauración/eliminación de Tienda,
los límites de formularios y los correos `.com` de hasta 50 caracteres.

La prueba SQL combina las migraciones de archivado, papelera y preregistros;
la prueba de asistencia mantiene el reloj sincronizado con el servicio.
Se actualiza el contrato de Tienda y las dependencias SQL de la guía de pruebas.
El borrador local del chatbot queda fuera del PR.

## Evidencia ejecutada

| Comprobación | Resultado |
| --- | --- |
| Suite backend completa con clave sintética y `GYM_TEST_POSTGRES_CONTAINER=gym-pr103-postgres` | 718 aprobadas, sin fallos ni omisiones; PostgreSQL 16 desechable, sin datos externos. |
| Suite frontend `npm test` | 305 aprobadas, sin fallos ni omisiones. |
| `node --test tests/26-stock-edit-forms.test.js tests/34-form-validation.test.js` | 55 aprobadas; incluye las regresiones añadidas para avisos en vivo y pestaña de Papelera. |
| `npm run build` | Correcto. |
| Flake8 `--select=E9,F63,F7,F82` sobre backend | 0 errores. |
| Validador documental | Correcto. |
| Índice de Git y revisión de espacios | Sin archivos en conflicto ni errores de espacios. |

Pruebas de regresión en [26-stock-edit-forms.test.js](../../../../frontend/tests/26-stock-edit-forms.test.js).
La corrección del correo conserva los escenarios de [34-form-validation.test.js](../../../../frontend/tests/34-form-validation.test.js).

## Límites

Validación de vistas mediante sus componentes/composables reales y renderizado
SSR. No se ejecuta una nueva revisión visual de navegador en esta corrección.
No se contactan Stripe, Google, Resend o Supabase remotos ni se certifica un E2E
con proveedores reales. La suite backend informa una advertencia de deprecación
de Starlette/httpx sin fallos. El build termina con avisos de tiempos de plugins.
El resultado de los checks remotos corresponde al commit publicado y debe
consultarse en GitHub; las pruebas locales no sustituyen esa comprobación.
