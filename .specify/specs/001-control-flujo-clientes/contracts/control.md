# Contrato de control de errores

Se conservan rutas, cuerpos y permisos existentes. DELETE /api/clientes/{id} devuelve
204 solo si termina el comando; persistencia indisponible devuelve 503 sanitizado.
La edición genérica de membresía confirmada o ajena devuelve 400 sin mutación.
Importe positivo que no coincide con el guardado se rechaza; cero no activa un flujo gratuito.
Los horarios inválidos se rechazan; toda hora guardada se puede consumir como tiempo ISO.
Entrada de asistencia sin membresía pagada y vigente se rechaza sin consumir aforo.
Las fechas finales son inclusivas y los reintentos conservan idempotencia.

Frontend: el retorno distingue verificando, pendiente, confirmado y error. Reintentar
consulta la misma sesión; no inicia checkout. La confirmación se muestra solo para
el cliente que devuelve el servidor y no se publica si cambió la ruta. El diálogo
de clientes desactiva el pago manual durante su petición y refleja la activación guardada.
