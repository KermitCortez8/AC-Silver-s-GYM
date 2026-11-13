# Validación de la primera versión del agente

**Fecha:** 2026-11-12. **Rama:** `levano/agenteAgente`. Datos de prueba sintéticos; cero llamadas reales a Groq, Supabase, Stripe o correo en la batería nueva.

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

## Resultados

| Comando | Resultado |
| --- | --- |
| `pytest tests/agente tests/planes_promociones tests/horarios_matriculas/integracion -q -p no:cacheprovider --tb=short` | 44 aprobadas; 2 advertencias de deprecación de dependencias. |
| `npm test -- --test-concurrency=1` | 373 aprobadas, 0 fallidas. |
| `npx playwright test e2e/agent.spec.js` | 12 aprobadas: 4 escenarios × Chromium, Firefox y WebKit. |
| `npm run build` | Compilación Vite aprobada. |

Una ejecución paralela de la batería frontend informó un fallo de archivo en la suite de paginación; el archivo pasó aislado y la batería completa pasó con concurrencia 1. No se atribuyó ese fallo al agente.

## Límites y pendientes

- No se guardó una línea base comparable de esta rama antes de añadir los casos nuevos; no se afirma un antes/después medido.
- Playwright comprueba la interfaz con API simulada. pytest comprueba la ruta y la aplicación con proveedor/catálogos falsos. Falta una prueba conjunta con un backend aislado y una prueba controlada de acceso al modelo real.
- El límite de llamadas es atómico **dentro de un proceso**, no entre varias instancias. Se necesita cuota distribuida antes de exposición pública real.
- El filtro de datos personales cubre los patrones probados; requiere revisión adicional antes de enviar consultas libres de usuarios reales a un proveedor externo.
- SonarQube/Quality Gate no se ejecutó para esta rama. La validación documental general de Spec Kit presenta 11 errores previos de descubrimiento de skills; no afectan la ejecución de las pruebas de producto.
