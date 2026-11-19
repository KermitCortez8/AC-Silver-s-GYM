# Probar el agente localmente

La versión local está en `levano/agenteAgente.v1`. El panel aparece en páginas públicas. La ruta `POST /api/agente/mensajes` consulta los servicios existentes de planes y horarios o una base revisada de información pública (actividades, primer día, principiantes, ubicación, registro, acceso y cupos). Las preguntas explícitas de horarios se resuelven directamente con el catálogo; para las demás preguntas públicas Groq selecciona el tema permitido. El backend arma la respuesta desde esa fuente. No se ha entrenado un modelo con todo el repositorio.

## Pruebas aisladas, sin credenciales ni servicios externos

Desde `backend`: `.venv\Scripts\python.exe -B -m pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short`

Desde `frontend`: `npm test -- --test-concurrency=1`, `npm run build` y `npx playwright test e2e/agent.spec.js`.

Las pruebas de backend sustituyen proveedor y catálogo; Playwright intercepta `/api` y bloquea tráfico externo. No generan cobros, correos ni registros reales. Resultados: [validación](validation.md).

## Demo local con catálogo real de solo lectura

Con autorización del responsable se creó una clave nueva en Groq y se guardó únicamente en el `backend/.env` local, ignorado por Git; la clave anterior quedó intacta. El mismo archivo local ya contiene las credenciales del proyecto para la lectura de Supabase. No crear archivos de entorno ni copiar claves al repositorio.

Desde `backend`, iniciar `.venv\Scripts\python.exe -m uvicorn app.agent_readonly_app:app --host 127.0.0.1 --port 8765`. Desde otra terminal, en `frontend`, iniciar `npm run dev -- --config vite.agent-readonly.config.js --host 127.0.0.1 --port 4173 --strictPort`. Abrir `http://127.0.0.1:4173/` y preguntar «Dime los horarios de todas las clases». Este montaje publica solo el asistente y las tres consultas públicas que necesita la página: planes, promociones vigentes y horarios activos del servicio real de Supabase. No inicia tareas de fondo ni ofrece rutas de pagos, correo o escritura. Vite carga el `.env` local del frontend para mostrar las imágenes públicas de Supabase; la política del servidor solo permite imágenes de ese origen y mantiene las llamadas API en el servidor local de solo lectura.

El 12/11/2026 se verificaron manualmente 23 horarios activos de Baile, Cardio, Fitness y Musculación a través del navegador y del proxy. Los horarios se agrupan por actividad y se muestran completos; una consulta por una actividad concreta filtra las demás. Los saludos y las cortesías comunes se responden localmente; para frases sociales menos previsibles, Groq puede seleccionar una intención conversacional permitida. Frases de cierre como «todo bien» y «muchas gracias» tienen respuestas propias. Una pregunta de cómo registrarse paso a paso recibe instrucciones revisadas desde la pantalla de Registro y un enlace a ella. Una pregunta ambigua invita a precisar. Solo las preguntas claramente ajenas al gimnasio y a la charla breve reciben una redirección al negocio; si se insiste, la redirección es más directa. La consulta «quiero recuperar mi cuenta» abre un formulario para reunir correo, DNI y teléfono solo en la memoria de esa pestaña. El formulario no envía ni guarda los datos en backend, Supabase, Groq o correo; al cerrar el chat se borran. Es una demostración pendiente de integración: el dueño no recibe ninguna solicitud y no se restablece la contraseña. Ninguna de estas respuestas permite al modelo inventar precios u horarios. La batería automatizada sigue aislada de red y usa dobles. Antes de habilitar tráfico público se requiere cuota distribuida y revisión de privacidad; el cupo actual solo protege una instancia.
