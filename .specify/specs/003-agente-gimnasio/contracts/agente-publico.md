# Contrato implementado: atención pública del agente

Implementado en `develop`.

`POST /api/agente/mensajes` recibe JSON con `mensaje` (1–500 caracteres) e `id_conversacion` opaco opcional. No acepta rol, ID de cliente, URL, SQL, precio ni nombre de herramienta enviados por el navegador. La identidad de cliente no se infiere del texto.

Respuesta satisfactoria: `id_conversacion`, `estado: "respondida"`, `texto` y `enlaces` de una lista permitida (`/registro`, `/`, `/login`, `/#servicios`, `/#ubicacion` o `/preguntas-frecuentes`). Sin datos confirmados se devuelve `estado: "sin_datos"`; una acción privada se devuelve como `fuera_de_alcance` y un mensaje sensible como `bloqueado`.

Los mensajes vacíos o demasiado largos reciben HTTP 422. Si el agente carece de una consulta de respaldo, el cupo agotado devuelve HTTP 429 y la indisponibilidad técnica devuelve HTTP 503. Los errores no incluyen prompts, claves, datos personales ni respuestas crudas del proveedor.

Herramientas internas permitidas: `consultar_planes()`, `consultar_horarios_publicos()` y `consultar_informacion_publica(tema)`. Las dos primeras usan los servicios existentes del backend. La tercera consulta fichas revisadas de actividades, primer día, principiantes, ubicación, registro, acceso y cupos, basadas en la web pública. El backend valida el tema contra una lista cerrada y devuelve el texto de la ficha; el modelo no redacta cifras ni hechos adicionales. Una herramienta o argumento desconocido se rechaza. El proveedor no recibe credenciales ni controla la URL o consulta de datos.

Groq selecciona primero la herramienta para las consultas de catálogo. Si falta la clave, falla el proveedor, se agota el cupo o el proveedor no elige una herramienta, el agente resuelve las consultas reconocibles de planes y horarios mediante el catálogo público de Supabase.

El cupo actual es global por proceso: 10 llamadas por minuto y 100 por día UTC, sin identificar visitantes. Un despliegue con varios procesos necesita un cupo compartido antes de habilitar uso público real.
