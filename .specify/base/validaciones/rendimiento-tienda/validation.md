# Validación de rendimiento de Tienda

Fecha: 2026-11-26. Corrección directa del módulo de Tienda.

El catálogo real devuelve 39 productos y unos 13 KB de JSON. La muestra de
20 imágenes originales sumó 5,96 MB. La revisión encontró una sincronización
global al abrir la pantalla de pago y componentes administrativos importados
en el catálogo del cliente. Las tarjetas del cliente se montaban todas juntas.

El pago carga el perfil. Catálogo, ventas y papelera cargan su código al abrirse.
El cliente navega el mismo catálogo con nueve tarjetas al entrar, lotes de
nueve al pedir más y búsqueda sobre todos los productos. Al cambiar un filtro
vuelve al primer lote. Las imágenes conservan su resolución original y se
cargan a medida que se muestran.

En administración, las miniaturas de Productos, Papelera y el selector del
editor tienen prioridad baja. Ventas prepara un índice de clientes, calcula el
mes una vez por pedido y reutiliza el formato de fecha. Así evita volver a
recorrer el directorio o reconstruir los formatos por cada línea de venta.

Chromium sobre Vite con sesión simulada y catálogo real comprobó nueve tarjetas
iniciales, dieciocho al pulsar «Ver más productos» y nueve tras limpiar la
búsqueda. El catálogo solo consultó `/api/tienda` aparte de autenticación.
Ventas pidió clientes y pedidos tras abrirse. La pantalla de pago solo consultó
`/api/clientes/me` aparte de autenticación. Se revisaron catálogo del cliente y
tabla administrativa a 1440 × 900. No se efectuaron compras ni cambios en datos.
La revisión administrativa comprobó también la fila de una venta con su comprador,
Papelera, apertura del editor y consulta de imágenes solo al abrir la galería.

Pasaron las 455 pruebas de frontend, la compilación y el validador documental.

## Ventas y Papelera por separado

Ventas carga pedidos y muestra el comprador guardado. Solo solicita el
directorio si una venta pagada con vínculo o DNI tiene datos incompletos.
El filtro descarta primero mes, pedido y comprador antes de buscar texto.
Papelera usa la misma respuesta de Productos, separada en una sola pasada, y
evita filtrar cuando el buscador está vacío. Se retiró el desenfoque de fondo
en ambas pestañas.

Chromium comprobó que Ventas solo pide pedidos cuando el comprador está
guardado y que resuelve el comprador de un pedido antiguo con el directorio.
Cambiar a Papelera y buscar reutilizó el catálogo sin emitir otra consulta.
Pasaron las 455 pruebas y la compilación del frontend.
