# Formulario de planes de membresía

## Cambio solicitado

La duración era un campo de texto que exigía conocer y escribir el formato del
servidor. Se sustituyó por un selector con 1, 7, 15, 30, 60, 90, 180 y 365 días,
con 30 días seleccionados al crear. No se inicia Spec Kit para este ajuste directo.

Al editar un plan se conserva su duración registrada como opción adicional si
no coincide con las habituales. No se convierte `1 mes` en `30 días` ni `1 año`
en `365 días` automáticamente. La selección original sigue disponible durante
la edición y desaparece al abrir un alta nueva.

Duración y precio comparten fila en escritorio y se apilan en móvil. El precio
nuevo parte vacío; es obligatorio introducirlo, incluido cero cuando corresponda.
Los errores de nombre, duración y precio se asocian a su campo mediante
`aria-invalid`, `aria-describedby` y el componente `FieldError`. Las descripciones
y beneficios se identifican como opcionales. Se conservan los máximos silenciosos
50/150 y los estados de guardado. No se modificaron la API, las conversiones de
vigencia ni las membresías contratadas.

## Verificación

- `npm test --prefix frontend`: **298 pruebas aprobadas**, incluidas cuatro
  nuevas de opciones, conservación de duración, precio y validación del formulario.
- `node --test frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js`: **4 aprobadas**
  tras el ajuste final del mensaje de validación.
- `npm run build --prefix frontend`: **aprobado**.
- `node .specify/base/validaciones/formulario-planes/evidence/browser-review.cjs`:
  **6 escenarios aprobados**, sin errores de JavaScript.
- `python .specify/.codex/hooks/validate.py` y `git diff --check`: **aprobados**.

La revisión usa Vite y Chromium con API interceptada, cuentas sintéticas y bloqueo
de conexiones externas. Cubre selección de duración, validación antes de guardar,
importe decimal, bloqueo durante el envío, conservación de la duración `45 dias`
y precio cero, fallo de servidor con reintento y revisión móvil en ambos temas.
El registro de envíos comprueba los valores recibidos por la API simulada.

Evidencia reproducible: [script de navegador](evidence/browser-review.cjs) y
[resultados](evidence/browser-results.json). El script usa `127.0.0.1:5174` por
defecto, admite `GYM_FRONTEND_URL` y `GYM_PLAYWRIGHT_MODULE` y requiere Vite con
`VITE_AUTH_API_BASE_URL=/api`. No guarda planes en servicios reales.

Capturas propias revisadas:

- [Nuevo plan](evidence/nuevo-plan.png).
- [Errores de campos](evidence/errores-campos.png).
- [Duración histórica al editar](evidence/editar-duracion-actual.png).
- [Móvil claro](evidence/nuevo-plan-movil.png) y [oscuro](evidence/nuevo-plan-oscuro.png).

La suite backend no se repitió en este cambio de presentación. La comprobación
anterior de sus 713 casos consta en [relojes y PostgreSQL](../relojes-asistencia/validation.md).
