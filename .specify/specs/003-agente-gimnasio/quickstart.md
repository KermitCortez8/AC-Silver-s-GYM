# Probar el agente localmente

La primera versión está en `levano/agenteAgente`. El panel aparece en páginas públicas. La ruta `POST /api/agente/mensajes` consulta los servicios existentes de planes y horarios; Groq selecciona una de esas herramientas y el backend arma la respuesta con datos consultados.

## Pruebas aisladas, sin credenciales ni servicios externos

Desde `backend`: `.venv\Scripts\python.exe -B -m pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short`

Desde `frontend`: `npm test -- --test-concurrency=1`, `npm run build` y `npx playwright test e2e/agent.spec.js`.

Las pruebas de backend sustituyen proveedor y catálogo; Playwright intercepta `/api` y bloquea tráfico externo. No generan cobros, correos ni registros reales. Resultados: [validación](validation.md).

## Comprobación con proveedor real

Con autorización del responsable se creó una clave nueva en Groq y se guardó únicamente en el `backend/.env` local, ignorado por Git; la clave anterior quedó intacta. Se comprobó manualmente el recorrido interfaz → ruta FastAPI → proveedor Groq → herramienta `consultar_planes` → respuesta, mediante un backend local aislado con catálogo sintético. Este entorno no accede a Supabase ni ejecuta cobros, correos o tareas de inicio del backend normal. Antes de habilitar tráfico público se requiere cuota distribuida y revisión de privacidad; el cupo actual solo protege una instancia.
