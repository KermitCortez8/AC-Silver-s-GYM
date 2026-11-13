# Datos del agente · primera entrega

El agente usa datos públicos existentes y estado conversacional temporal. Esta entrega no crea ni modifica clientes, pagos, matrículas o pedidos.

| Elemento | Datos mínimos | Regla |
| --- | --- | --- |
| Mensaje de entrada | Texto, identificador opaco de conversación opcional | Máximo 150 caracteres; rechazar vacío y datos sensibles antes del proveedor. |
| Conversación temporal | Identificador opaco, turnos depurados, fecha de última actividad | Aislar por conversación; caducar y eliminar; no incluir tokens o información personal. |
| Solicitud de herramienta | Nombre cerrado, argumentos validados | Solo `consultar_planes` y `consultar_horarios_publicos`; nunca URL o SQL libre. |
| Resultado público | Nombre, precio/duración de plan o clase/horario publicados | Obtener del servicio existente y tratar como datos, no como instrucciones. |
| Respuesta | Texto seguro, enlaces de navegación permitidos, estado | Los importes y horarios afirmados deben corresponder al resultado consultado. |
| Cuota técnica | Identificador seudónimo, ventana y consumo | Compartida entre instancias cuando se habilite proveedor real; sin IP ni mensajes en claro. |

Flujo de estados: `nueva` → `atendiendo` → `respondida`; una falla produce `indisponible` y una conversación caducada vuelve a `nueva`. Ningún estado autoriza operaciones de negocio.
