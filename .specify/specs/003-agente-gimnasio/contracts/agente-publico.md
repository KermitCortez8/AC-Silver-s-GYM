# Contrato implementado: atención pública del agente

Implementado en `levano/agenteAgente`; aún no integrado en `develop`.

`POST /api/agente/mensajes` recibe JSON con `mensaje` (1–150 caracteres) e `id_conversacion` opaco opcional. No acepta rol, ID de cliente, URL, SQL, precio ni nombre de herramienta enviados por el navegador. La identidad de cliente no se infiere del texto.

Respuesta satisfactoria: `id_conversacion`, `estado: "respondida"`, `texto` y `enlaces` de una lista permitida (`/registro`, `/` o `/login`). Sin datos confirmados se devuelve `estado: "sin_datos"`; una acción privada se devuelve como `fuera_de_alcance` y un mensaje sensible como `bloqueado`. El proveedor caído devuelve HTTP 503; la interfaz muestra orientación.

Errores: mensaje vacío o demasiado largo en el esquema JSON → 422; exceso del cupo local → 429; indisponibilidad técnica → 503. Los errores no incluyen prompts, claves, datos personales ni respuestas crudas del proveedor.

Herramientas internas permitidas: `consultar_planes()` y `consultar_horarios_publicos()`. Se ejecutan desde servicios existentes del backend, con argumentos cerrados y resultados depurados. Una herramienta desconocida se rechaza. El proveedor no recibe credenciales ni controla la URL o consulta de datos.

El cupo actual es global por proceso: 10 llamadas por minuto y 100 por día UTC, sin identificar visitantes. Un despliegue con varios procesos necesita un cupo compartido antes de habilitar uso público real.
