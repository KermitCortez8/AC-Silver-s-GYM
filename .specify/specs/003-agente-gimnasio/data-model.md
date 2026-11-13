# Datos del agente · primera entrega

El agente usa datos públicos existentes y estado conversacional temporal. Esta entrega no crea ni modifica clientes, pagos, matrículas o pedidos.

| Elemento | Datos mínimos | Regla |
| --- | --- | --- |
| Mensaje de entrada | Texto, identificador opaco de conversación opcional | Máximo 150 caracteres; rechazar vacío y datos sensibles antes del proveedor. |
| Conversación temporal | Identificador opaco, último tema público y vencimiento | Aislar por conversación; caducar y eliminar; no guardar el mensaje ni información personal. |
| Solicitud de herramienta | Nombre cerrado, argumentos validados | `consultar_planes`, `consultar_horarios_publicos` o `consultar_informacion_publica` con tema enumerado; nunca URL o SQL libre. |
| Resultado público | Plan/horario publicado o ficha pública revisada | Obtener del servicio existente o de las fichas permitidas y tratarlo como datos, no como instrucciones. |
| Respuesta | Texto seguro, enlaces de navegación permitidos, estado | Los importes y horarios afirmados deben corresponder al resultado consultado. |
| Cuota técnica | Ventana y consumo globales por proceso | Sin IP ni mensajes en claro; pendiente de compartir entre instancias para uso público. |

Flujo de estados: `nueva` → `atendiendo` → `respondida`; una falla produce `indisponible` y una conversación caducada vuelve a `nueva`. Ningún estado autoriza operaciones de negocio.
