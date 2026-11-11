# Límites silenciosos de formularios

Se implementó directamente la propuesta autorizada, sin iniciar Spec Kit.
El síntoma era la entrada sin límite o con límites diferentes entre módulos.
El criterio de regresión es que escribir o pegar no supere el máximo, sin
mostrar avisos, contadores o ayudas nuevas sobre la longitud.

## Reglas aplicadas

| Campos | Máximo |
| --- | --- |
| Nombre completo y correo de clientes y usuarios | 50 caracteres |
| Nombre del plan y promoción, duración textual, palabra clave y código del día | 50 caracteres |
| Descripción de planes/promociones, beneficios y motivo de asistencia | 150 caracteres |
| Búsqueda general mediante `SearchInput` | 50 caracteres |
| DNI | 8 dígitos |
| Teléfono | 9 dígitos |

Por ajuste posterior del usuario, nombre completo y correo se clasifican como
textos cortos: ambos pasan de 150 a 50 caracteres en las tres pantallas de
cuentas y en las escrituras del servidor. Las pruebas comprueban 50 aceptados
y 51 rechazados.

Los campos opcionales conservan esa condición; DNI y teléfono, si se completan,
requieren su longitud exacta. El motivo conserva el mínimo de 5 caracteres.
Se conservan ceros iniciales y se filtran caracteres no numéricos en los campos
de identidad. Las contraseñas conservan su validación propia, sin aplicarles
50/150 ni recortar sus espacios. Fechas, horas, números y listas conservan sus
validaciones específicas.

Los máximos están centralizados en `formLimits.js` y `domain/form_limits.py`.
Vue utiliza `maxlength` y una directiva numérica que actúa antes de `v-model`.
Los esquemas HTTP y comandos de dominio rechazan datos demasiado largos en
escrituras directas; no recortan silenciosamente los valores recibidos.
La etiqueta de promoción se ajusta visualmente dentro de su vista previa cuando
alcanza 50 caracteres, conservando completo el valor editable.
No se modificaron datos históricos ni se ejecutaron migraciones.

## Estado posterior

Los 39 fallos y 33 omisiones registrados en la entrega de límites se revisaron
posteriormente. La sincronización de la fixture y la ejecución SQL aislada se
documentan en [validación de relojes y PostgreSQL](../relojes-asistencia/validation.md).
Los resultados siguientes se conservan como evidencia de la entrega inicial.

## Comprobaciones ejecutadas en la entrega inicial

| Comando desde la raíz | Resultado |
| --- | --- |
| `npm test --prefix frontend` | 294 pruebas aprobadas. |
| `npm run build --prefix frontend` | Aprobado. |
| `/tmp/gym-limits-venv/bin/python -m pytest backend/tests/transversales/integracion/test_basic_form_validation.py backend/tests/transversales/integracion/test_form_limits.py -q` | 82 pruebas aprobadas, incluidas 21 nuevas de fronteras y comandos directos. |
| `/tmp/gym-limits-venv/bin/python -m pytest backend/tests/ -q` | 640 aprobadas, 39 fallidas y 33 omitidas. |
| `/tmp/gym-limits-venv/bin/python -m flake8 backend --count --select=E9,F63,F7,F82 --show-source --statistics` | Aprobado, 0 errores. |
| `node .specify/base/validaciones/limites-formularios/evidence/browser-review.cjs` | 17 comprobaciones aprobadas en Chromium, sin errores de JavaScript. |
| `python .specify/.codex/hooks/validate.py` | Aprobado. |
| `python -B -m unittest discover -s .specify/tests -v` | 13 pruebas aprobadas. |
| `git diff --check` | Aprobado. |

En esa entrega la suite completa de backend no quedó verde: se comparó con una copia de
`HEAD` (`ce5219d780f3b724653673b36f1ee7952e326fea`) creada mediante `git archive`,
sin modificar el checkout del usuario. Con clave de firma sintética en la copia,
la base obtuvo 619 aprobadas, las mismas 39 fallidas y 33 omitidas. Los nombres
de los fallos coinciden exactamente; no se añadieron fallos. Afectan pruebas
existentes de asistencia y vigencia con fechas de octubre de 2026. La comparación
está en [backend-baseline-comparison.json](evidence/backend-baseline-comparison.json).

Las pruebas PostgreSQL permanecen omitidas porque no se preparó un contenedor
desechable. No se comprobaron Supabase real, pagos ni proveedores externos.

## Evidencia visual e interacción

Se revisaron formularios reales mediante Vite y Chromium, con API interceptada,
cuentas sintéticas y bloqueo de conexiones externas. El script reproduce escritura,
pegado, conservación de ceros y guardado del modelo de cliente. Ver
[browser-review.cjs](evidence/browser-review.cjs) y
[browser-results.json](evidence/browser-results.json).

Capturas revisadas:

- [Clientes](evidence/clientes.png) y [usuarios](evidence/usuarios.png).
- [Membresías/planes](evidence/membresias.png) y [promociones](evidence/promociones.png).
- [Horarios](evidence/horarios.png) y [asistencia](evidence/asistencia.png).
- [Registro público móvil](evidence/registro-movil.png).

Para repetir la revisión: arrancar Vite con `VITE_AUTH_API_BASE_URL=/api` en
`127.0.0.1:5174`, disponer de Playwright/Chromium y, si se instala en otra ruta,
definir `GYM_PLAYWRIGHT_MODULE`. El script no requiere un backend real.
