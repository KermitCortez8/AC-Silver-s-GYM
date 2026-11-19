# Validación de la primera versión del agente

La batería agrupada y el antes/después posteriores a esta primera validación están en [qa-v1-bateria.md](qa-v1-bateria.md). La relación entre casos y criterios se revisó el 2026-11-19; los resultados de ejecución indicados abajo conservan sus fechas originales.

**Fecha:** 2026-11-12. **Rama:** `levano/agenteAgente.v1`. La batería automatizada usa datos sintéticos y no llama a Groq, Supabase, Stripe ni correo. La comprobación manual posterior conectó la API local de solo lectura al catálogo real de Supabase; otras preguntas públicas usan Groq para elegir una herramienta permitida.

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
| AG-08 | CA-08, CA-13 | Aplicación; concurrencia | Diez reservas simultáneas con cupo 3; exactamente 3 permitidas. | Alta | `backend/tests/agente/test_agent_flow.py` |
| AG-09 | CA-09 | Dominio, aplicación y UI | Pregunta por ejercicios o primer día; ficha pública pertinente y enlace. Tema malformado o ajeno rechazado. | Alta | `backend/tests/agente/test_agent_flow.py`, `frontend/e2e/agent.spec.js` |
| AG-10 | CA-02 | Aplicación; regresión | 23 horarios de cuatro actividades se muestran completos; una consulta concreta filtra las demás y no inventa horarios para otra actividad. | Alta | `backend/tests/agente/test_agent_flow.py` y comprobación manual con Supabase |
| AG-11 | CA-01, CA-02 | HTTP; aislamiento | La API de demostración solo expone el chat y tres consultas públicas GET; no publica rutas de escritura. | Alta | `backend/tests/agente/test_agent_http.py` |
| AG-12 | CA-10 | Dominio y aplicación; regresión | Saludos, agradecimientos y despedidas breves reciben respuesta sin proveedor, presupuesto ni catálogo; una pregunta de negocio con saludo conserva su intención. | Media | `backend/tests/agente/test_agent_flow.py` y navegador local |
| AG-13 | CA-06, CA-07, CA-10 | Aplicación; regresión | La IA solo puede elegir una intención social aprobada o marcar un tema claramente ajeno. Una pregunta ambigua mantiene la conversación; una segunda pregunta ajena recibe una redirección más directa. | Media | `backend/tests/agente/test_agent_flow.py` y navegador local |
| AG-14 | CA-05, CA-11 | Dominio, aplicación y UI; regresión | Recuperar cuenta u olvidar contraseña abre el formulario local para correo, DNI y teléfono. Estos datos no salen a la API ni se muestran en el historial; un mensaje con correo o clave real se bloquea antes de cualquier proveedor. | Alta | `backend/tests/agente/test_agent_flow.py`, `frontend/e2e/agent.spec.js` y navegador local |
| AG-15 | CA-03, CA-10, CA-12 | Dominio y aplicación; regresión | Frases de cierre después de una consulta de horarios reciben una respuesta natural sin repetir la pregunta genérica. Pedir ayuda paso a paso para registrarse devuelve el flujo publicado y el enlace a Registro; una orden de inscripción directa conserva su bloqueo. | Media | `backend/tests/agente/test_agent_flow.py` y API local |

## Resultados

| Comando | Resultado |
| --- | --- |
| `pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short` | 100 aprobadas; 2 advertencias de deprecación de dependencias. |
| `npm test -- --test-concurrency=1` | 373 aprobadas, 0 fallidas. |
| `npx playwright test e2e/agent.spec.js --config=node_modules/.cache/agent-playwright.config.js --reporter=line` con servidor de demostración | 27 aprobadas: 9 escenarios × Chromium, Firefox y WebKit. |
| `npm run build` | Compilación Vite aprobada. |
| `flake8 app application domain infrastructure presentation tests --count --select=E9,F63,F7,F82 --show-source --statistics` | 0 errores. Se indican directorios fuente para excluir el entorno virtual local. |

Una ejecución paralela de la batería frontend informó un fallo de archivo en la suite de paginación; el archivo pasó aislado y la batería completa pasó con concurrencia 1. No se atribuyó ese fallo al agente.

## Límites y pendientes

- No se guardó una línea base comparable de esta rama antes de añadir los casos nuevos; no se afirma un antes/después medido.
- Playwright comprueba la interfaz con API simulada. pytest comprueba la ruta y la aplicación con proveedor/catálogos falsos. La comprobación manual adicional sí recorrió frontend → proxy local → API → servicio → Supabase. Las consultas públicas devolvieron 23 horarios activos, 4 planes y 0 promociones vigentes en ese momento. El navegador mostró las cuatro actividades y las 23 sesiones en el chat sin los horarios ficticios de Spinning y Yoga; tras cargar el catálogo, la tarjeta de Baile mostró sus 5 sesiones reales. Esta comprobación manual no reemplaza una batería automatizada contra Supabase.
- Ante «dime los horarios de cada ejercicios que hay», el proveedor podía no elegir herramienta y el backend devolvía fuera de alcance. Las preguntas explícitas de horarios del gimnasio ahora consultan directamente el servicio real, sin depender de que Groq elija herramienta. Una actividad concreta filtra la respuesta; una actividad sin horarios activos recibe un mensaje sin inventar clases. La interfaz distingue el límite temporal (429) de una indisponibilidad del servidor.
- Las respuestas con varios planes, horarios o tipos de entrenamiento se presentan en líneas con viñetas. Se comprobó visualmente en el chat local que la lista completa de actividades queda visible; la prueba funcional verifica también el desplazamiento automático de una lista larga en tres motores.
- Se comprobó en el navegador local una conversación breve: «Hola, ¿cómo estás?», «Bien, ¿y tú?», «¿Cómo te llamas?» y «Gracias por la información». También se verificó «como estás silver» seguido de dos preguntas ajenas; la primera redirigió con suavidad y la segunda de manera más directa. «Hola, ¿qué planes tienen?» sigue consultando el catálogo. Las pruebas automatizadas confirman que las cortesías comunes no invocan al proveedor, no gastan cuota y no borran el tema previo. El proveedor solo puede seleccionar intenciones sociales de una lista validada.
- Se comprobó en el navegador local «hola» → «qué tal todo» sin repetir la presentación. La recuperación abre un formulario local que indica de forma breve que la solicitud todavía no se envía al gimnasio. Se verificó con el frontend y backend reales que, al reunir correo, DNI y teléfono de prueba, la única petición saliente contenía la pregunta inicial, sin esos datos. El formulario borra sus datos al cerrar el chat. La app no implementa restablecimiento automático de contraseña.
- Tras una consulta de horarios, «vale, todo bien creo yo» y «no tranquilo, quería consultar, muchas gracias» reciben respuestas sociales distintas, sin repetir «Te sigo». «¿Puedes ayudarme paso a paso a registrarme?» devuelve cuatro pasos basados en la pantalla de Registro y enlaza a `/registro`. Se verificó la secuencia contra la API local.
- Los `.env` locales ignorados por Git contienen la configuración recibida para backend y frontend. La demo usa únicamente la API pública de solo lectura y las imágenes públicas del frontend; no se ha habilitado el backend completo con sus tareas de pagos, correos o escritura.
- El límite de llamadas es atómico **dentro de un proceso**, no entre varias instancias. Se necesita cuota distribuida antes de exposición pública real.
- El filtro de datos personales cubre los patrones probados; requiere revisión adicional antes de enviar consultas libres de usuarios reales a un proveedor externo.
- SonarQube/Quality Gate no se ejecutó para esta rama. La validación documental general de Spec Kit presenta 11 errores previos de descubrimiento de skills; no afectan la ejecución de las pruebas de producto.

## Ajuste visual del acceso al chat · 2026-11-19

Se reemplazó el botón flotante de texto por un acceso circular rojo con un ícono de asistente dibujado en SVG. Conserva la etiqueta accesible «Abrir asistente del gimnasio» y muestra «Pregúntale a Silver» al pasar el cursor o enfocar con teclado en escritorio. Se revisó visualmente a 390 × 844 y 1440 × 900 píxeles. `npm run build` terminó correctamente y los 27 casos de `frontend/e2e/agent.spec.js` pasaron en Chromium, Firefox y WebKit. Es un cambio de presentación; no se modificaron el servicio, la API ni las respuestas del agente.

## Panel y campo multilínea · 2026-11-19

Se mejoraron la cabecera, la bienvenida, las burbujas y los enlaces del panel. La entrada del mensaje ahora es un área de texto que envuelve palabras largas, crece hasta un límite y permite seguir desplazándose sin mostrar una barra gruesa. Enter envía y Shift + Enter inserta una línea. Se revisó visualmente el chat abierto en una ventana estrecha, con un mensaje de 100 caracteres sin espacios: el texto pasó a varias líneas y el botón Enviar siguió visible. La prueba nueva verifica crecimiento, ausencia de desplazamiento horizontal y ambas teclas en los tres motores.

Comprobaciones: `npm test -- --test-concurrency=1`: 373/373; `npm run build`: aprobado; `frontend/e2e/agent.spec.js`: 30/30; Playwright integrado: 18/18. No se modificaron las respuestas ni la API. La demo local volvió a responder HTTP 200 en los puertos 4173 y 8765 después de la integración.

## Límite de mensajes · 2026-11-19

Por decisión del usuario, el mensaje público del agente admite hasta 500 caracteres. El límite se aplica en el campo, el esquema HTTP y la política de dominio; el límite de otros formularios no cambió. Antes del ajuste, el nuevo caso de 500 caracteres devolvió 422 y el campo todavía declaraba `maxlength=150`. Después, 500 caracteres devuelven 200, 501 devuelven 422 y el navegador impide añadir un carácter por encima de 500. La prueba del campo pasó en Chromium, Firefox y WebKit.

Regresión posterior: backend 104/104, Playwright UI 30/30, compilación frontend aprobada y `flake8` crítico con 0 errores. No se repitieron en este ajuste las pruebas unitarias generales del frontend ni la integración de conversaciones; ambas habían pasado antes del cambio de límite. La validación documental general conservaba 11 errores previos de descubrimiento de skills; se resolvieron durante la integración de `develop` descrita abajo.

## Integración de `origin/develop` · 2026-11-19

Se incorporó `origin/develop` en `levano/agenteAgente.v1-pruebas` sin conflictos de Git. La regla nueva de arquitectura detectó que la ruta del agente importaba infraestructura; se movió la construcción del proveedor a `presentation.dependencies` y el error compartido a `application.errors`. Dos pruebas de arquitectura se ajustaron para leer los archivos Python en UTF-8 en Windows. El SPEC y su trazabilidad se adaptaron al validador documental actualizado.

| Comprobación sobre el código combinado | Resultado |
| --- | --- |
| `pytest tests -q -p no:cacheprovider --tb=short` | 1045 aprobadas, 61 omitidas y 2 advertencias de dependencias. Las pruebas PostgreSQL que requieren `GYM_TEST_POSTGRES_CONTAINER` quedaron omitidas. |
| `npm test -- --test-concurrency=1` | 418 aprobadas. |
| `npm run build` | Aprobado. |
| `npx playwright test e2e/agent.spec.js --config node_modules/.cache/agent-playwright.config.js` | 30 aprobadas en Chromium, Firefox y WebKit. |
| `npx playwright test --config playwright.agent-integration.config.js` | 18 aprobadas en Chromium, Firefox y WebKit con API y catálogo controlados. |
| `python .specify/.codex/hooks/validate.py` | Documentación válida: 146 archivos y 15 contratos. |

Estas cifras corresponden a la rama tras traer `develop`; no representan una ejecución de SonarQube ni una certificación de despliegue público.

## Arranque del frontend compilado · 2026-11-19

El build de producción fallaba al abrir inicio o login con `C is not a function`.
Los archivos JavaScript de entrada y del calendario se importaban entre sí antes
de que Vue pudiera montar la aplicación. El asistente se carga ahora bajo demanda
en las rutas públicas que lo muestran. Playwright compila y sirve la versión de
producción para comprobar ese arranque con la API sintética.

| Comprobación | Resultado |
| --- | --- |
| Chromium sobre el build de producción | Inicio y login abren sin errores. El asistente abre en inicio. |
| Playwright de CI sobre `dist` | 4 recorridos aprobados, con capturas. |
| Build y suite de frontend en Docker Linux | Aprobados. |
| Validador documental y suite `.specify/tests` en Docker Linux | Validador aprobado y 62 pruebas aprobadas. |
| Suite de frontend en Windows | 419 aprobadas y un fallo conocido en el temporizador de descanso. |

## Consultas breves de horarios · 2026-11-19

«Quiero saber horarios» devolvía HTTP 503 sin una clave de Groq, aunque el
catálogo estaba disponible. Esta frase y otras preguntas breves equivalentes
ahora consultan directamente las clases activas. Se probó el endpoint con
cuatro variantes y un proveedor sin clave. Las 128 pruebas de agente y de
integración de horarios y matrículas pasaron.

Tras reconstruir Docker Compose, Chromium envió la pregunta desde el chat de
`localhost:5173`. El endpoint devolvió HTTP 200 y el chat mostró los 23 horarios
del catálogo público.

## Groq con respaldo del catálogo

El agente intenta primero seleccionar una herramienta con Groq. Si falla esa
consulta, se agota el cupo o el proveedor devuelve una selección vacía, usa
el catálogo para preguntas reconocibles de planes u horarios. Las protecciones
de privacidad y la validación de herramientas siguen aplicándose.

Pasaron 147 pruebas de agente, planes, promociones y horarios, incluida la
llamada HTTP simulada con una clave sintética y la recuperación ante tiempo
de espera agotado. Después de actualizar Docker Compose, Chromium comprobó
que el chat local devuelve 23 horarios y 4 planes de Supabase. El entorno local
carece de una clave real de Groq, por lo que la llamada real quedó sin verificar.
