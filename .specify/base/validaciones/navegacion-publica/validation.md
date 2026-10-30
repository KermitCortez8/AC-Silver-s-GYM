# Validación de navegación pública con sesión

Fecha: 2026-10-30.

## Síntoma y corrección

Al volver a `/` después de iniciar sesión, el guard redirigía automáticamente al
panel. La landing y sus anclas dejaban de ser accesibles para cualquier rol.
Además, el observador de sesión podía enviar al login desde páginas públicas al
detectar una membresía vencida.

La política del guard se separa en `presentation/router/sessionGuard.js` para
reutilizarla en pruebas de navegación. Se retira la redirección de `/`; las rutas
públicas ya inicializadas no esperan una comprobación privada adicional. La
restauración inicial y las validaciones de rutas privadas/login se conservan.
El observador de `App.vue` solicita login por caducidad solo en rutas protegidas.

## Regresión

`37-public-navigation.test.js` recorre con Vue Router en memoria el retorno desde
paneles de admin, staff, trainer y user, anclas de landing, entrada directa con
sesión restaurada, acceso explícito al panel, visitante anónimo, membresía vencida
y restricciones de rol. Antes de corregir la redirección fallaban 6 de sus 8 casos;
después pasan los 8. `21-module-navigation.test.js` comprueba también que volver a
la landing no fuerza una revalidación privada.

## Revisión en navegador

El [recorrido](evidence/browser-review.cjs) usa formulario de contraseña, router y
stores reales con respuestas API sintéticas, sin conectarse con proveedores.
Prueba los cuatro roles: landing → login → panel → botón Atrás → landing, anclas,
recarga, acceso explícito al panel y entrada directa a `/`.

Para clientes comprueba además caducidad durante la landing: la sesión se revoca,
la landing sigue visible y la entrada al panel exige login con motivo de caducidad.
Capturas: escritorio 1440×1000 y móvil 390×844.

El [resultado](evidence/browser-results.json) confirma los cuatro roles sin errores
de página. Se revisaron las capturas de [administrador](evidence/landing-admin.png),
[cliente móvil](evidence/landing-user.png) y
[sesión vencida](evidence/landing-sesion-vencida.png).

## Comprobaciones ejecutadas

- `npm test` en `frontend`: 280 pruebas correctas; 9 regresiones nuevas.
- `npm run build` en `frontend`: compilación correcta.
- Recorrido Chromium: contraseña, Atrás, landing directa, anclas, recarga y retorno
  al panel correctos para los cuatro roles; caducidad comprobada con cliente.
- `python .specify/.codex/hooks/validate.py`: documentación válida.
- `git diff --check`: sin errores de formato.

No hay cambios en backend, base de datos ni proveedores para esta corrección.

## Repetición del recorrido

Con Playwright/Chromium y dependencias del frontend instaladas, desde la raíz:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
```

En otra terminal:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/navegacion-publica/evidence/browser-review.cjs
```

El entorno simulado valida navegación y revocación en el navegador; no acredita
autenticación real con Google ni disponibilidad de servicios remotos.
