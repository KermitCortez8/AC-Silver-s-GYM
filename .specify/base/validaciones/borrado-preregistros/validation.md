# Validación del borrado de preregistros pendientes

Fecha: 2026-10-30.

## Síntoma y causa reproducida

Al borrar un cliente aparecía «No se pudo confirmar la operación», aunque el
servidor podía haber completado la eliminación. La lectura de los registros del
backend local mostró una respuesta DELETE 204. No se ejecutaron borrados sobre
clientes reales durante la investigación.

Chromium devuelve un stream vacío en `response.body` para un 204; Node devuelve
`null`. El transporte leía ese stream y construía `new Response(buffer,
{ status: 204 })`, que lanza `TypeError` porque ese estado no admite cuerpo. El
capturador lo convertía en el mensaje de conexión de la captura del usuario.
La prueba nueva reprodujo exactamente ese mensaje antes de la corrección.

## Corrección y alcance

[httpTransport.js](../../../../frontend/src/infrastructure/services/httpTransport.js)
conserva la respuesta original para estados sin cuerpo (204, 205 y 304) y HEAD,
sin reconstruirla. Un borrado confirmado retira la fila y comunica éxito.
Los errores HTTP reales y la pérdida de conexión mantienen sus controles;
no se reenvían automáticamente las escrituras de resultado incierto.

El preregistro se guarda antes del checkout por diseño para permitir retomar
el pago con la misma identidad, membresía e importe. Abandonar o expirar el
checkout conserva `EN_TRAMITE/PENDIENTE`; no acredita pago ni activa la cuenta.
Los pendientes se pueden eliminar mediante el borrado administrativo existente.
No se cambia esta regla ni se añade limpieza automática que pudiera interferir
con un pago o webhook en curso. No se modifican SQL, permisos ni la cascada.

También se comprobó mediante lecturas y planificación en memoria que tres
pendientes de la configuración actual producían únicamente operaciones de
eliminación de cliente y membresía. La transacción remota se sustituyó por un
capturador que impide enviarla. Esta comprobación no certifica borrados reales.

## Regresión y resultados

- [32-http-error-control.test.js](../../../../frontend/tests/32-http-error-control.test.js):
  respuesta 204 con stream de navegador, tanto en API como repositorio, sin
  leer el cuerpo ni repetir DELETE; conservación de otros estados sin cuerpo.
- [test_client_flow_control.py](../../../../backend/tests/test_client_flow_control.py):
  checkout público abierto/expirado sin pago ni notificación, reintento sin
  duplicados y borrado HTTP 204 conservando otro cliente y su membresía.
- `npm test` en `frontend`: 290 pruebas correctas.
- `npm run build` en `frontend`: compilación correcta.
- `python -m pytest tests/ -q` en `backend`: 629 correctas, 28 omitidas por
  requerir PostgreSQL desechable explícito; no cambia persistencia SQL.
- `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`:
  sin errores de las categorías configuradas.
- `python .specify/.codex/hooks/validate.py`: documentación válida.
- `python -B -m unittest discover -s .specify/tests -v`: 13 pruebas correctas.
- `git diff --check`: sin errores de formato.

El [recorrido real en Chromium](evidence/browser-review.cjs) intercepta todas las
API con datos sintéticos y bloquea proveedores externos. Reproduce el fallo
anterior con el stream nativo y comprueba el transporte corregido. Verifica
cancelación del diálogo, borrado público y administrativo, conflicto 409 que
conserva la fila y pérdida de respuesta sin reenvío, con actualización posterior.
[Resultado](evidence/browser-results.json): cinco escenarios correctos y ningún
error de página. Capturas revisadas: [antes](evidence/antes.png),
[borrado confirmado](evidence/borrado-confirmado.png) y
[conflicto real](evidence/conflicto-real.png).

Para repetir con Playwright/Chromium instalado, arrancar desde la raíz:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
```

En otra terminal:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/borrado-preregistros/evidence/browser-review.cjs
```
