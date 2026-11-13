# Validación de la primera versión del agente

**Fecha:** 2026-11-12. **Rama:** `levano/agenteAgente`. La batería automatizada usa datos sintéticos y no llama a Groq, Supabase, Stripe ni correo. La comprobación manual posterior sí llamó a Groq con un catálogo sintético y el backend local aislado.

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

## Resultados

| Comando | Resultado |
| --- | --- |
| `pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short` | 53 aprobadas; 2 advertencias de deprecación de dependencias. |
| `npm test -- --test-concurrency=1` | 373 aprobadas, 0 fallidas. |
| `npx playwright test e2e/agent.spec.js` con configuración local temporal que reutiliza el servidor de demostración | 21 aprobadas: 7 escenarios × Chromium, Firefox y WebKit. |
| `npm run build` | Compilación Vite aprobada. |

Una ejecución paralela de la batería frontend informó un fallo de archivo en la suite de paginación; el archivo pasó aislado y la batería completa pasó con concurrencia 1. No se atribuyó ese fallo al agente.

## Límites y pendientes

- No se guardó una línea base comparable de esta rama antes de añadir los casos nuevos; no se afirma un antes/después medido.
- Playwright comprueba la interfaz con API simulada. pytest comprueba la ruta y la aplicación con proveedor/catálogos falsos. En una comprobación manual adicional, el frontend llamó al backend local aislado y Groq seleccionó `consultar_informacion_publica` para «¿Qué tipo de ejercicios hay?»; se devolvió la ficha revisada de Fitness, Musculación, Cardio y Baile. Las consultas previas de planes usaron precios sintéticos. No es una prueba automatizada contra Supabase.
- Ante «dime los horarios de cada ejercicios que hay», el proveedor podía no elegir herramienta y el backend devolvía fuera de alcance. Se añadió recuperación para preguntas explícitas de horarios del gimnasio. La misma consulta devolvió HTTP 200 y los dos horarios sintéticos del entorno local. Una captura anterior mostraba el mensaje genérico de error de la interfaz; no conserva el código HTTP original, por lo que no se atribuye ese error a una causa concreta. La interfaz ahora distingue el límite temporal (429) de una indisponibilidad del servidor.
- Las respuestas con varios planes, horarios o tipos de entrenamiento se presentan en líneas con viñetas. Se comprobó visualmente en el chat local que la lista completa de actividades queda visible; la prueba funcional verifica también el desplazamiento automático de una lista larga en tres motores.
- El límite de llamadas es atómico **dentro de un proceso**, no entre varias instancias. Se necesita cuota distribuida antes de exposición pública real.
- El filtro de datos personales cubre los patrones probados; requiere revisión adicional antes de enviar consultas libres de usuarios reales a un proveedor externo.
- SonarQube/Quality Gate no se ejecutó para esta rama. La validación documental general de Spec Kit presenta 11 errores previos de descubrimiento de skills; no afectan la ejecución de las pruebas de producto.
