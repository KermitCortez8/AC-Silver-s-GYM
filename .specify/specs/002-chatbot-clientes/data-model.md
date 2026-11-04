# Modelo previsto

No se duplican clientes, preregistros, membresías, pagos, horarios o matrículas.

## Turno efímero

- `message`: texto no vacío, máximo 150 caracteres Unicode; evaluar vacío tras normalizar espacios, sin HTML ejecutable.
- `history`: hasta ocho mensajes depurados, cuatro pares completos, en memoria de pestaña; no localStorage ni base. Backend valida todo historial como entrada no confiable.
- `page_context`: enum de páginas del recorrido; `service_id` y `class_date` opcionales y validados con datos reales. No tomar cliente/rol/token del cuerpo.
- Cuerpo completo máximo 8 KiB. Por llamada al modelo: hasta 2.000 tokens de entrada incluyendo instrucciones/contexto y 256 de salida. Hasta dos llamadas y tres herramientas de lectura por turno.
- Respuesta: `request_id`, `message` máximo 600 caracteres y hasta tres acciones tipadas. Datos estructurados construidos por servidor, fuera de la prosa del modelo.

## Acciones sugeridas

`ABRIR_REGISTRO`, `ABRIR_ACCESO`, `VER_PLANES`, `BUSCAR_HORARIOS`, `VER_MIS_INSCRIPCIONES`, `REVISAR_MATRICULA`.
Argumentos según esquema cerrado. Rutas internas definidas por aplicación, sin URL libre. Proponer no ejecuta escrituras.

`REVISAR_MATRICULA` identifica horario y fecha ISO. Frontend recarga detalle real, muestra servicio/fecha/hora y crea selección pendiente ligada a su sesión. Caduca a los cinco minutos o al cambiar datos/sesión; recargar antes de confirmar si caducó. Backend revalida cupo y vigencia siempre.

Panel: `listo → consultando → respuesta | guía_local | error`.
Matrícula: `seleccionada → por_confirmar → enviando → verificada | rechazada | por_reconciliar`.
Solo el botón pulsado por el usuario pasa de `por_confirmar` a `enviando`; el modelo no puede producir ese evento.

## Cuota técnica compartida

Tabla propuesta `CHATBOT_CUOTAS`, aislada de recursos de negocio: clave HMAC del sujeto, tipo/ventana, consumo, reserva presupuestaria, vencimiento y referencia opaca del turno. No guarda conversación o identidad en claro.

Sujeto privado: ID interno transformado por HMAC. Público: IP obtenida de proxy explícitamente confiable y transformada por HMAC; sin proxy confiable, IP de conexión. No confiar en `X-Forwarded-For` arbitrario ni sustituir el límite con una cookie regenerable.

Inicialmente: público 10 turnos/10 min/IP; privado 20/10 min/cliente; un turno simultáneo por sujeto. Configurables. Leases vencidos se liberan al reservar. Filas con TTL lógico de 24 h tras cerrar su ventana; purga al reservar y comando de mantenimiento para períodos sin tráfico. La caducidad lógica no garantiza borrado físico sin ejecutar mantenimiento.

Antes de llamar se reserva atómicamente coste máximo según tokens/modelo/tarifas; se liquida con consumo confirmado. Sin consumo fiable se conserva reserva hasta cerrar ventana diaria. Timeout no libera presupuesto por suposición. Presupuesto diario positivo y tarifas/modelo explícitos son obligatorios; sin configuración, guía local. Día presupuestario UTC, clases America/Lima.

RPC técnica idempotente por turno/llamada con locks de sujeto y presupuesto global, acceso exclusivo backend y limpieza de leases. Fallo de cuota impide llamar al proveedor. No modifica matrículas ni reemplaza RPC de negocio.
