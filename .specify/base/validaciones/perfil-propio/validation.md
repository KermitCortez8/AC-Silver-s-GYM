# Configuración de cuenta

Los paneles de cliente, administrador y entrenador ofrecen un resumen de la
cuenta autenticada y un formulario para actualizar su nombre y teléfono. Se
reutiliza la preferencia de tema del navegador. La vista consulta la sesión y
realiza sus guardados mediante `/api/auth/me`.

- [La prueba HTTP](../../../../backend/tests/identidad_acceso/integracion/test_perfil_propio.py)
  usa sesiones firmadas y persistencia en memoria. Verifica guardado para los
  cuatro roles, lectura posterior, rechazo de campos protegidos y cuentas sin
  acceso, y ausencia de escrituras parciales si falla la validación.
- [Las pruebas de sesión](../../../../frontend/tests/identidad_acceso/integracion/perfil-propio.test.js)
  verifican que una respuesta anterior no reemplace el perfil guardado ni se
  publique en una sesión nueva.
- Chromium con API simulada verificó el resumen y el acceso desde la navegación,
  validación de teléfono, descarte, reintento, avisos y guardado independiente
  del nombre y el teléfono. Los datos y el tema persistieron al recargar.
  Revisión de admin y entrenador a 1440 px,
  cliente a 390 px y ambos temas. La vista consultó solo `/api/auth/me`.
- Backend con `pytest tests -q` aprobó 1128 pruebas y omitió 68. Flake8 aprobó
  las comprobaciones E9, F63, F7 y F82.
- Frontend con `npm test` aprobó 459 pruebas. `npm run build` completó la compilación.
- No se escribieron datos en Supabase remoto.

## Ficha de consulta y edición explícita

La ficha muestra nombre, rol, correo, teléfono, DNI, código, estado de cuenta y
métodos de acceso. Para el cliente añade la fecha de registro y la membresía
vigente con el plan, el pago y sus fechas. «Editar datos» abre un diálogo de
nombre y teléfono. Cancelar o pulsar Escape descarta el borrador. Un error del
servidor mantiene los campos para reintentar.

- Chromium con API simulada verificó la ficha inicial sin campos editables,
  el foco del diálogo, cancelación, Escape, validación, error, reintento y
  guardado con recarga. Administración y entrenador en escritorio, cliente
  a 390 px. La vista consultó solo `/api/auth/me`.
- La prueba HTTP de perfil verifica los nuevos datos y que la ficha del cliente
  seleccione su membresía vigente aunque haya un cobro posterior pendiente.
- Backend aprobó 1129 pruebas y omitió 68. Frontend aprobó 459 pruebas y compiló
  correctamente.

## Revisión anterior del diálogo

Esta revisión incluyó el perfil y la membresía vigente dentro del diálogo,
junto a los campos de nombre y teléfono. Se verificó el fondo opaco y el
desplazamiento del contenido en pantallas pequeñas con los botones visibles.

- Chromium con perfiles simulados verificó los datos dentro del diálogo,
  el fondo opaco en ambos temas, los avisos de error y el guardado. La ficha
  del cliente permitió consultar la membresía a 390 px con los botones visibles.
- Frontend aprobó 459 pruebas y completó la compilación.

## Edición de correo, DNI y contraseña

En esta revisión, «Editar datos» incorporó nombre, correo, DNI, teléfono y
contraseña nueva. El diálogo solicitaba la contraseña actual o el Google
vinculado para autorizar cambios sensibles.

- Las pruebas HTTP cubrieron los cuatro roles, credenciales incorrectas,
  duplicados, preregistros pendientes y la confirmación de Google. El acceso
  con la nueva contraseña se validó contra el repositorio en memoria.
- Chromium verificó los campos y los avisos de guardado en escritorio y móvil
  con datos simulados. También se simuló el botón para confirmar con Google.
- Backend aprobó 1135 pruebas y omitió 68. Flake8 reportó cero errores en las
  comprobaciones E9, F63, F7 y F82. Frontend aprobó 459 pruebas y compiló.

## Modal con campos editables

Los datos de consulta se muestran en la ficha de Configuración. Chromium
verificó en escritorio y móvil que el diálogo abre con cinco campos
editables y que la confirmación de identidad aparece cuando corresponde.
Frontend aprobó las 459 pruebas y compiló.

## Un solo campo para cambiar la contraseña

La ficha pasó a representar la contraseña configurada con puntos fijos.
El diálogo pasó a mostrar «Contraseña nueva» con el campo vacío. En esa
revisión, cambiar correo, DNI o contraseña exigía que la sesión tuviera
menos de 15 minutos.

- Las pruebas HTTP verificaron el cambio con sesión reciente y el rechazo
  con una sesión anterior sin modificar la cuenta.
- Chromium verificó la máscara, el campo único y el regreso a Configuración
  tras iniciar sesión de nuevo, con perfiles simulados en escritorio y móvil.
- Backend aprobó 1137 pruebas y omitió 68. Frontend aprobó 459 y compiló.

## Guardado con la sesión vigente

Configuración permite guardar con la sesión activa hasta su vencimiento.
Las pruebas HTTP verificaron un guardado con un token de 55 minutos de
antigüedad y el rechazo con un token vencido. Chromium verificó en escritorio
y móvil que el guardado conserva la vista de Configuración.
Backend aprobó 1137 pruebas y omitió 68. Frontend aprobó 459 y compiló.
