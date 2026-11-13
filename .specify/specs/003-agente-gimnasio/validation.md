# Validación de la primera versión del agente

**Fecha:** 2026-11-12. **Rama:** `levano/agenteAgente`. La batería automatizada usa datos sintéticos y no llama a Groq, Supabase, Stripe ni correo. La comprobación manual posterior conectó la API local de solo lectura al catálogo real de Supabase; otras preguntas públicas usan Groq para elegir una herramienta permitida.

## Matriz de casos

| ID | Requisito | Capa / tipo | Entrada y resultado esperado | Prioridad | Evidencia |
| --- | --- | --- | --- | --- | --- |
| AG-01 | CA-01, CA-02 | Aplicación; integración aislada | Plan cambia de S/80 a S/90; respuesta cambia sin inventar. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-02 | CA-01 | Aplicación; integración aislada | Clase activa de prueba; devuelve día y horas publicados. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-03 | CA-03, CA-05 | Dominio; unitarias | Correo, tarjeta, clave o matrícula; no llegan al proveedor ni ejecutan catálogo. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-04 | CA-06 | Dominio; unitarias | Herramienta ajena al catálogo; rechazada. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-05 | CA-07 | Aplicación; unitarias | Dos conversaciones; contexto separado. | Media | `backend/tests/agente/test_agent_flow.py` |
| AG-06 | CA-04, CA-08 | Ruta HTTP; integración aislada | Solicitud válida y mensaje demasiado largo; respuesta y 422. | Alta | `backend/tests/agente/test_agent_http.py` |
| AG-07 | CA-01, CA-04, CA-08 | UI; funcional | Plan, clase, error y acción privada; panel y navegación visibles. | Alta | `frontend/e2e/agent.spec.js` en 3 motores |
| AG-08 | CA-06, CA-08 | Aplicación; concurrencia | Diez reservas simultáneas con cupo 3; exactamente 3 permitidas. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-09 | CA-09 | Dominio, aplicación y UI | Pregunta por ejercicios o primer día; ficha pública pertinente y enlace. Tema malformado o ajeno rechazado. | Alta | `backend/tests/agente/test_agent_flow.py`, `frontend/e2e/agent.spec.js` |
| AG-10 | CA-02 | Aplicación; regresión | 23 horarios de cuatro actividades se muestran completos; una consulta concreta filtra las demás y no inventa horarios para otra actividad. | Alta | `backend/tests/agente/test_agent_flow.py` y comprobación manual con Supabase |
| AG-11 | CA-01, CA-02 | HTTP; aislamiento | La API de demostración solo expone el chat y tres consultas públicas GET; no publica rutas de escritura. | Alta | `backend/tests/agente/test_agent_http.py` |
| AG-12 | CA-04, CA-06 | Dominio y aplicación; regresión | Saludos, agradecimientos y despedidas breves reciben respuesta sin proveedor, presupuesto ni catálogo; una pregunta de negocio con saludo conserva su intención. | Media | `backend/tests/agente/test_agent_flow.py` y navegador local |
| AG-13 | CA-06, CA-07 | Aplicación; regresión | La IA solo puede elegir una intención social aprobada o marcar un tema claramente ajeno. Una pregunta ambigua mantiene la conversación; una segunda pregunta ajena recibe una redirección más directa. | Media | `backend/tests/agente/test_agent_flow.py` y navegador local |

## Resultados

| Comando | Resultado |
| --- | --- |
| `pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short` | 83 aprobadas; 2 advertencias de deprecación de dependencias. |
| `npm test -- --test-concurrency=1` | 373 aprobadas, 0 fallidas. |
| `npx playwright test e2e/agent.spec.js` con configuración local temporal que reutiliza el servidor de demostración | 21 aprobadas: 7 escenarios × Chromium, Firefox y WebKit. |
| `npm run build` | Compilación Vite aprobada. |
| `flake8 app application domain infrastructure presentation tests --count --select=E9,F63,F7,F82 --show-source --statistics` | 0 errores. Se indican directorios fuente para excluir el entorno virtual local. |

Una ejecución paralela de la batería frontend informó un fallo de archivo en la suite de paginación; el archivo pasó aislado y la batería completa pasó con concurrencia 1. No se atribuyó ese fallo al agente.

## Límites y pendientes

- No se guardó una línea base comparable de esta rama antes de añadir los casos nuevos; no se afirma un antes/después medido.
- Playwright comprueba la interfaz con API simulada. pytest comprueba la ruta y la aplicación con proveedor/catálogos falsos. La comprobación manual adicional sí recorrió frontend → proxy local → API → servicio → Supabase. Las consultas públicas devolvieron 23 horarios activos, 4 planes y 0 promociones vigentes en ese momento. El navegador mostró las cuatro actividades y las 23 sesiones en el chat sin los horarios ficticios de Spinning y Yoga; tras cargar el catálogo, la tarjeta de Baile mostró sus 5 sesiones reales. Esta comprobación manual no reemplaza una batería automatizada contra Supabase.
- Ante «dime los horarios de cada ejercicios que hay», el proveedor podía no elegir herramienta y el backend devolvía fuera de alcance. Las preguntas explícitas de horarios del gimnasio ahora consultan directamente el servicio real, sin depender de que Groq elija herramienta. Una actividad concreta filtra la respuesta; una actividad sin horarios activos recibe un mensaje sin inventar clases. La interfaz distingue el límite temporal (429) de una indisponibilidad del servidor.
- Las respuestas con varios planes, horarios o tipos de entrenamiento se presentan en líneas con viñetas. Se comprobó visualmente en el chat local que la lista completa de actividades queda visible; la prueba funcional verifica también el desplazamiento automático de una lista larga en tres motores.
- Se comprobó en el navegador local una conversación breve: «Hola, ¿cómo estás?», «Bien, ¿y tú?», «¿Cómo te llamas?» y «Gracias por la información». También se verificó «como estás silver» seguido de dos preguntas ajenas; la primera redirigió con suavidad y la segunda de manera más directa. «Hola, ¿qué planes tienen?» sigue consultando el catálogo. Las pruebas automatizadas confirman que las cortesías comunes no invocan al proveedor, no gastan cuota y no borran el tema previo. El proveedor solo puede seleccionar intenciones sociales de una lista validada.
- El límite de llamadas es atómico **dentro de un proceso**, no entre varias instancias. Se necesita cuota distribuida antes de exposición pública real.
- El filtro de datos personales cubre los patrones probados; requiere revisión adicional antes de enviar consultas libres de usuarios reales a un proveedor externo.
- SonarQube/Quality Gate no se ejecutó para esta rama. La validación documental general de Spec Kit presenta 11 errores previos de descubrimiento de skills; no afectan la ejecución de las pruebas de producto.
