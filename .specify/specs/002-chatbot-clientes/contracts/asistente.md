# Contrato previsto del asistente

Propuesta, todavía no expuesta por el producto. [Spec](../spec.md), [modelo y límites](../data-model.md).

## Endpoints nuevos

| Endpoint | Permisos | Información disponible |
| --- | --- | --- |
| `POST /api/asistente/publico/mensajes` | Visitante, cuota pública | Ayuda revisada y catálogo/horarios públicos. No perfiles, estado de preregistro, pagos o matrículas. |
| `POST /api/asistente/mensajes` | Sesión actual habilitada, rol `user` | Mismo contenido público, búsqueda de sesiones elegibles y tarjetas con inscripciones propias. |

No se acepta `client_id` ni rol en el cuerpo. El endpoint privado usa la dependencia actual y obtiene dueño desde sesión. Un token inválido no degrada la petición a pública. El frontend limpia conversación y pide al usuario continuar en modo público sin reenviar historial privado.

## Entrada

`message`: obligatorio, no vacío, máximo 150 caracteres.
`history`: lista opcional de hasta ocho mensajes depurados con rol `user` o `assistant`, sin roles `system` o `tool`; cada texto de usuario máximo 150 y de asistente 600. No se acepta historial como autorización o resultado de herramienta.
`page_context`: enum `inicio`, `registro`, `acceso`, `retorno_pago`, `cliente`, `matricula`, `mi_horario`.
`service_id`: entero positivo opcional. `class_date`: fecha ISO opcional; se validan contra horario y calendario del servidor. Cuerpo máximo 8 KiB. Sin campos extra. Solo texto, sin adjuntos, HTML o ejecución de Markdown.

## Salida

`request_id`: identificador opaco generado por backend.
`mode`: `ia` o `guiado`.
`message`: texto seguro, máximo 600 caracteres; no confirma operaciones de negocio.
`actions`: lista de máximo tres elementos tipados de la enumeración del modelo. IDs y argumentos contrastados contra entidades reales; ruta de navegación nunca viene del modelo.
`cards`: datos canónicos opcionales construidos por backend, con campos mínimos del catálogo/sesión o inscripciones propias; no se devuelven al proveedor como historial.

Si la salida del modelo no cumple esquema o hace referencia a una entidad inexistente: respuesta guiada sin acción inválida. Precios, promociones, fechas y disponibilidad se presentan con tarjetas construidas desde las consultas actuales, no como datos inventados en la prosa.

## Herramientas disponibles al modelo

| Herramienta | Alcance y control |
| --- | --- |
| `consultar_catalogo` | Solo planes/promociones públicos vigentes y campos de presentación permitidos. |
| `consultar_horarios_publicos` | Solo vista pública, sin clientes o inscripciones. |
| `buscar_sesiones` | Solo privado; fecha/servicio validados, sin datos ajenos. |
| `solicitar_mis_inscripciones` | Solo privado; servidor genera tarjeta propia fuera del contexto del modelo, sin aceptar ID de cliente. |

Máximo tres consultas y dos llamadas de modelo por turno. Sin herramientas de SQL, HTTP libre, archivos, correo, pagos, administración o escritura de matrícula. El contenido de catálogos no se interpreta como instrucciones.

## Confirmación fuera del proveedor

`REVISAR_MATRICULA` solo prepara una tarjeta. La aplicación recarga datos reales y requiere botón Confirmar matrícula. Usa el endpoint actual `POST /api/gym/matriculas`, vía módulo existente, con `id_horario_servicio` y `fecha_clase`; el servidor impone identidad y conserva reglas/RPC. Confirmar no es una herramienta ni un mensaje de texto que el modelo pueda emitir.

Tras respuesta válida, refrescar matrículas propias y Mi horario. Ante resultado incierto: consultar `GET /api/gym/matriculas` antes de ofrecer reintento. Rechazo de cupo/vigencia no cambia a éxito por prosa de IA. No se incorpora un endpoint alternativo de matrícula.

## Límites y errores

| Condición | Resultado |
| --- | --- |
| Entrada fuera de esquema o 150 caracteres | `422`, sin llamada al proveedor. |
| Cuerpo mayor de 8 KiB | `413`, sin procesar conversación. |
| Sesión inválida / no habilitada / rol distinto | `401` / `403` del control existente. |
| Límite del sujeto o turno simultáneo | `429` con `Retry-After`, sin llamada. |
| Proveedor sin configurar, presupuesto agotado, salida inválida o timeout | `200`, `mode=guiado`, explicación breve y acciones seguras; nunca éxito de operación. |
| Cuotas/servicios internos indisponibles | Sin llamada externa, guía local si se puede construir; en otro caso `503` y enlace frontend al recorrido original. |

Timeout total de turno 15 s; no lanzar reintentos automáticos del proveedor. Limitar tokens antes de cada llamada y reservar presupuesto compartido según [modelo](../data-model.md). Logs sin mensajes/historial/secretos ni argumentos privados. Esquemas y errores se prueban con proveedor falso.
