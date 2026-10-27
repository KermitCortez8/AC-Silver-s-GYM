# Inventario e interfaz

La rama `feat/correcciones-inventario-ui` parte de `origin/develop` (la rama base
disponible en el repositorio; no existe una rama `developer`).

## Cantidades y artículos

- Stock inicial y mínimo: enteros entre 0 y 2147483647.
- Entradas, salidas y ajustes: enteros entre 1 y 2147483647, conservando la regla
  actual de movimientos positivos. Los ajustes continúan representando el saldo exacto.
- Los campos aceptan dígitos (`[0-9]+`). Se rechazan vacíos, signos, exponentes,
  decimales y texto; no se redondean ni se convierten silenciosamente en una unidad.
  La validación se ejecuta en el formulario, en los contratos de la API y en las
  reglas de inventario para llamadas directas al servicio.
- Crear/editar un artículo ofrece desplegables para categoría, ubicación y unidad.
  Incluyen opciones iniciales y valores existentes, también los personalizados.
  El estado mantiene su desplegable y la regla automática para artículos de Tienda.
- Los errores al guardar permanecen visibles dentro del editor sin perder el
  borrador. Guardar dos veces mientras hay una petición pendiente no duplica el alta.
- Se conserva la respuesta de eliminación para informar correctamente cuando un
  artículo con historial se marca como descontinuado.

## Búsquedas

Las búsquedas de texto de los módulos usan `SearchInput`: máximo 30 caracteres,
coincidencia parcial y sin distinguir mayúsculas. Los símbolos se tratan como texto,
no como expresiones regulares. Los filtros por listas y fechas se combinan con el
texto. Los campos de identificación por DNI conservan su validación específica.

| Módulo | Campos consultados |
| --- | --- |
| Inventario | Código ACT, nombre y categoría |
| Movimientos de inventario (pestaña) | Nombre del artículo y descripción |
| Movimientos de inventario (vista dedicada) | Nombre del artículo, tipo y descripción |
| Destino | Nombre del artículo y del producto vinculado |
| Tienda, administración | Nombre, código PROD y descripción |
| Tienda, catálogo | Nombre, categoría y descripción |
| Movimientos de tienda | Producto, cliente, DNI, número y estado del pedido |
| Pedidos | Número, cliente, correo, DNI, estados de pago/pedido y productos |
| Clientes | ID, nombre, correo, teléfono, DNI, plan, promoción, estados y referencia de pago |
| Usuarios | ID, nombre, correo, teléfono, DNI, rol y disponibilidad de contraseña |
| Pagos de membresías | Cliente, correo, DNI, ID de usuario/membresía, plan y referencia |
| Horarios de servicios | Servicio, rutina, zonas musculares, día, código del día, horas, cupos y estado |

Los placeholders identifican los campos principales. El título del buscador explica
la coincidencia parcial y el límite. Inventario ya no anuncia una búsqueda por
marca, pues no existe ese campo; filtrar reinicia la paginación.

## Colores y temas

Los acentos amarillos/ámbar de los módulos pasan a naranja. Se eliminan las reglas
globales que pintaban de rojo colores azules y verdes. Avisos y confirmaciones usan
azul; los mensajes de error, rojo. Los estados de negocio conservan sus colores
semánticos (por ejemplo, operativo en verde y stock bajo en naranja).

El modo oscuro usa tonos claros/pastel para información y errores. El modo claro
usa tonos profundos sobre superficies claras. Los inputs de modales enviados a
`body` con `Teleport` reciben los mismos colores y foco que los del panel.

## Verificación

Desde `frontend/`: `npm test` y `npm run build`.

Desde `backend/`, con dependencias de desarrollo instaladas:

```bash
AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef python -m pytest tests/ -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

La clave de ejemplo es exclusivamente para pruebas y coincide con la configuración
de CI. La suite omite las pruebas de PostgreSQL que requieren una base de pruebas
externa cuando no está configurada.

Para revisar la interfaz: abrir Inventario en claro y oscuro, crear un artículo,
seleccionar los desplegables, introducir `1e2` o `1.5`, corregir a `12`, verificar
los botones de cantidad y provocar un fallo de guardado. Comprobar que el error se
ve dentro del modal, que las búsquedas no superan 30 caracteres y que filtrar stock
bajo desde otra página muestra los artículos correspondientes.
