# Control de errores por módulo

Revisión del frontend Vue y de las rutas, contratos y servicios del backend.
Las comprobaciones usan servicios simulados y datos locales; no ejecutan escrituras
en Supabase, Stripe, Google ni servicios de correo. Los cambios quedan sin commit.

## Hallazgos y correcciones

| Módulo | Control aplicado o verificado |
| --- | --- |
| Autenticación | Se conservan los códigos de cuenta/membresía bloqueada y vinculación con Google. Las respuestas HTTP mantienen su estado y código de negocio. El acceso con contraseña rechaza sesiones incompletas. Los fallos de proveedores se devuelven como indisponibilidad, sin detalles internos. |
| Usuarios | Un error al leer, guardar o eliminar conserva los datos locales. Las respuestas de guardado deben contener un registro identificable. Se verificaron los errores HTTP de consulta, alta y eliminación. |
| Clientes y registro | Una respuesta vacía ya no puede aparentar una edición correcta reutilizando la identidad anterior. Altas públicas/administrativas y confirmaciones validan cliente y membresía antes de publicar el estado. Los errores conservan el borrador. |
| Planes | Lecturas y guardados rechazan respuestas sin estructura o identidad válidas. Los errores de guardado/eliminación conservan el catálogo. El editor mantiene su protección contra doble envío. |
| Promociones | Se bloquean guardados simultáneos; el formulario exige exactamente un plan. Los errores se muestran dentro del editor. Si falla la eliminación, se conservan la confirmación, el artículo seleccionado y un mensaje visible para reintentar. |
| Horarios y matrículas | Las respuestas necesitan identidades válidas antes de actualizar horarios, rutinas o matrículas. No se reemplaza silenciosamente un cupo de cero por diez al preparar el envío. Se conservan los códigos de conflicto y de membresía requerida. |
| Entrenador y rutinas | Una caída del servidor deja de anunciarse como dato inválido o cliente inexistente. El DNI de consulta exige ocho dígitos. Si una asignación, desvinculación o registro de progreso ya se guardó y falla la recarga, se informa del guardado y del refresco pendiente; se cierra el diálogo correspondiente para evitar repetirlo por error. |
| Asistencias | Las consultas de ficha y resumen rechazan contenedores inválidos antes de reemplazar el estado. Se mantienen los controles existentes de solicitudes sustituidas, conflictos, doble entrada, identidad del intento y liberación del indicador de carga. |
| Inventario | Los movimientos necesitan una confirmación con identificador antes de incorporarse al historial local. Listas inválidas no reemplazan el historial. Los errores al guardar o eliminar conservan los datos. Se mantienen las validaciones de cantidades de la revisión anterior. |
| Tienda y carrito | Cantidades vacías, negativas, decimales o exponentes se rechazan sin conversión silenciosa. Agregar varias veces acumula la cantidad frente al stock disponible. Los errores se muestran en la tienda. El pedido local valida todas las líneas y los totales de productos repetidos antes de descontar stock o vaciar el carrito. |
| Pedidos | Solo puede existir un guardado pendiente por pedido. El estado y la observación del borrador se conservan si el servidor rechaza la actualización. No se eliminan ni se publican pedidos locales ante respuestas no confirmadas. |
| Pagos | Checkout no envía cantidades inválidas ni vacía el carrito si falla. El historial de membresías rechaza filas sin identificador. Se verificaron errores de consulta y activación de membresía, manteniendo las reglas existentes de confirmación del pago en el servidor. |
| Dashboard y configuración | Una capacidad de cero ya no se transforma en un valor predeterminado o en uno. Se validan ambas capacidades antes de cambiar la configuración. La respuesta de configuración se comprueba antes de sustituir el estado. |
| Imágenes | La galería y la subida usan el mismo manejo de conexión y espera que las demás solicitudes. Una galería inválida produce un error explícito. Una recarga fallida conserva las imágenes anteriores; no se anuncia como galería vacía. Se bloquean recargas simultáneas. |
| Sincronización | Se validan los contenedores y las identidades relevantes antes de publicar datos. Se conservan los últimos datos correctos cuando falla una sección. Los fallos no se cachean como cargas correctas y los indicadores de carga se liberan. |

## Validaciones básicas y mensajes de formulario

Ampliación del control: 27 de octubre de 2026.

| Campo o flujo | Regla y mensaje |
| --- | --- |
| Correos de cuentas y datos introducidos al comprar | Formato válido y dominio exacto `gmail.com` o `hotmail.com`, sin distinguir mayúsculas. Los dominios distintos muestran «Solo se permiten correos @gmail.com o @hotmail.com.». Se rechazan dominios falsos, subdominios, espacios internos y puntos consecutivos en la parte local. |
| Acceso existente | Valida el formato del correo y la contraseña obligatoria. La lista de dominios se aplica a escrituras y formularios de compra; no invalida sesiones ni impide autenticar cuentas históricas por su dominio. |
| Google en preregistro | El dominio también se comprueba después de verificar la credencial en el servidor, antes de buscar o reutilizar un preregistro pendiente. |
| DNI | Exactamente ocho dígitos. Obligatorio en preregistro y editor de clientes; opcional en usuarios y datos informativos de compra, pero se valida si se introduce. |
| Teléfono | Entre siete y nueve dígitos, sin letras ni espacios. Obligatorio en el preregistro; opcional en administración. La interfaz ya no borra silenciosamente los caracteres incorrectos. |
| Contraseña | Al menos seis caracteres; obligatoria al crear cuentas con contraseña. En edición, dejarla vacía conserva la anterior. El registro con Google no exige contraseña local. |
| Correo y DNI duplicados | Los editores de usuarios y clientes rechazan duplicados dentro de su directorio y permiten guardar la propia cuenta. El preregistro conserva sus comprobaciones de duplicados y reanudación autenticada. |
| Planes | Nombre y duración obligatorios; duración positiva en días, meses o años. Precio no negativo con hasta dos decimales en el formulario; el contrato HTTP y el guardado conservan los céntimos. |
| Promociones | Nombre obligatorio, descuento no negativo, porcentaje hasta 100, fechas ordenadas, exactamente un plan y cupos opcionales como entero positivo. |
| Inventario y tienda | Nombre obligatorio, cantidades enteras y no negativas y precio válido. El inventario muestra sus mensajes en español sin depender del diálogo nativo del navegador. |
| Confirmación de compra | Nombre y correo válidos, DNI válido si se introduce, carrito con productos y referencia obligatoria para pagos sin tarjeta. Se bloquean envíos simultáneos y se conservan los datos al fallar. |
| Corrección de asistencia | Motivo entre 5 y 500 caracteres, fecha/hora de entrada completas y fecha/hora de salida juntas, sin fechas futuras ni salida anterior a la entrada. Las reglas del servidor siguen comprobando las horas y el resto de restricciones. |

Los formularios de preregistro, clientes y usuarios muestran errores por campo,
con `aria-invalid`, `aria-describedby` y mensajes de alerta. Los fallos 422 de la API
se traducen a mensajes en español y se asocian a sus campos cuando corresponde.
Los errores permanecen en el formulario y no borran el borrador. Al corregir un
campo que tenía error, el mensaje se actualiza mientras se escribe para evitar
que el botón se mueva al perder el foco durante un clic. El rojo se adapta
al fondo: profundo en claro y suave en oscuro. Los avisos informativos conservan
el azul.

## Respuestas comunes

El traductor de errores se comparte entre rutas y también cubre consultas y
eliminaciones que antes no tenían manejo local:

| Situación | HTTP |
| --- | --- |
| Error de validación de negocio | 400 |
| Sesión ausente/inválida | 401 |
| Falta de permisos o membresía requerida | 403 |
| Entidad inexistente, identificada con `EntityNotFound` | 404 |
| Conflicto de asistencia, matrícula o pedido | 409 |
| Entrada que incumple el contrato de la API | 422 |
| Error inesperado o modelo interno inválido | 500 con mensaje genérico |
| Base de datos/proveedor temporalmente no disponible | 503 |

Los errores 422 devuelven únicamente ubicación, mensaje y tipo. No incluyen el
valor enviado, contraseñas/tokens ni contextos de validadores no serializables.
Los errores de modelos internos no se atribuyen al usuario como entradas inválidas.
Una migración pendiente conserva su mensaje accionable mediante `SchemaNotReady`.

El transporte HTTP limita la espera de respuesta a 30 segundos y distingue una
cancelación, una desconexión y un tiempo de espera agotado. No reintenta escrituras
automáticamente. Cuando se pierde la respuesta de una escritura, advierte que no se
pudo confirmar el resultado y pide actualizar los datos antes de repetirla.
El JSON incompleto produce un mensaje legible en vez de una excepción del parser.

## Verificación

- Frontend: **228 pruebas aprobadas** y compilación de producción correcta.
- Backend: **544 pruebas aprobadas**, **15 omitidas** por requerir PostgreSQL
  desechable, y comprobación de errores Python sin incidencias.
- Matriz HTTP: rutas de todos los módulos con proveedores fallidos, estados de
  dominio, credenciales no reflejadas en errores y errores inesperados sanitizados.
- Flujos Vue reales: borradores conservados, guardados duplicados bloqueados,
  errores dentro del diálogo, carrito e imágenes.
- Navegador Chromium: campos obligatorios, correos malformados y dominios falsos,
  contraste del error, respuesta 503 y conservación del borrador en preregistro.
- Los mocks anteriores de configuración y progreso se ajustaron para devolver los
  campos que realmente devuelve la API; las respuestas sin esos campos se cubren
  ahora como casos de error.

Pruebas añadidas:

- `backend/tests/test_module_error_control.py`
- `backend/tests/test_basic_form_validation.py`
- `frontend/tests/31-module-error-control.test.js`
- `frontend/tests/32-http-error-control.test.js`
- `frontend/tests/33-trainer-refresh-errors.test.js`
- `frontend/tests/34-form-validation.test.js`
- Casos adicionales en `frontend/tests/26-stock-edit-forms.test.js`.

Para repetir la comprobación:

```bash
npm --prefix frontend test
npm --prefix frontend run build
cd backend
AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef python -m pytest tests/ -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

La clave mostrada es exclusivamente de pruebas. La revisión no sustituye una
comprobación de despliegue con una base PostgreSQL aislada y credenciales de prueba
de las integraciones externas, ni certifica la ausencia de otros errores.
