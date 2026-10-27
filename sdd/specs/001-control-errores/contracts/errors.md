# Contrato de errores del piloto

## API existente

La tabla de estados HTTP se mantiene en [spec.md](../spec.md), ERR-006.
Formas admitidas, según la ruta:

```json
{"detail":"No existe el registro solicitado"}
```

```json
{"detail":{"code":"membership_expired","message":"Membresía vencida"}}
```

```json
{"detail":[{"loc":["body","correo"],"msg":"Correo inválido","type":"value_error"}]}
```

Los ejemplos son ilustrativos de la estructura; no fijan el texto literal de
todos los mensajes. Los errores `422` solo incluyen `loc`, `msg` y `type` por
problema. No reflejan valores enviados ni `ctx`. Un modelo interno inválido
genera `500`; no se atribuye al usuario como solicitud inválida.

No se cambia ningún endpoint, esquema de éxito, permiso ni código de negocio.

## Transporte frontend

| Situación | Código | Resultado incierto de escritura |
| --- | --- | --- |
| Tiempo agotado | `request_timeout` | `true` para escrituras enviadas. |
| Fallo de conexión | `network_error` | `true` para escrituras intentadas. |
| Cancelación antes de enviar | `request_cancelled` | `false`; sin envío (ERR-009 pendiente). |
| Cancelación tras invocar transporte | `request_cancelled` | `true` para escrituras (ERR-009 pendiente). |
| Cancelación de lectura | `request_cancelled` | `false`. |

El límite predeterminado es 30 segundos para recibir la respuesta completa en
los clientes JSON/texto actuales. El transporte devuelve el estado y contenido
legibles y conserva las cabeceras y metadatos usados por los clientes.

Una respuesta de escritura inválida no acredita reversión: ERR-003 exige
conservar el estado local y comunicar la necesidad de consultar antes de repetir.
La tarea T007 comprueba la presentación de ese aviso, además de la validación.

## Interfaz

Ante rechazo conocido, conservar borrador y datos previos aplicables. Ante
resultado incierto, mostrar el fallo de confirmación y la acción de consultar.
Ante guardado confirmado y recarga fallida, informar ambos resultados sin
presentar el guardado como rechazado. No implica mantener borradores de progreso
que ya fueron confirmados y limpiados correctamente.
