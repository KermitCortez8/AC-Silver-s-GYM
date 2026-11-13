# Decisiones para la primera entrega

Fecha: 2026-11-12. Fuentes: [contexto](context.md), [SPEC](spec.md) y contratos MOD-04/MOD-05. Son decisiones de diseño, no resultados de pruebas.

| Decisión | Motivo | Alternativa considerada |
| --- | --- | --- |
| Comenzar con planes y horarios públicos de solo lectura. | Permite demostrar uso real de herramientas sin afectar pagos o matrículas. | Acciones privadas en la primera entrega; requieren autorización, confirmación y pruebas adicionales. |
| Usar como candidato inicial Groq y el modelo `openai/gpt-oss-120b`, citados en el trabajo de Rodrigo, mediante un puerto intercambiable del backend. | El equipo ya investigó esa integración; el código de Rodrigo sigue siendo solo referencia. | Acoplar el caso de uso directamente al proveedor. Antes de una llamada real hay que verificar que la cuenta tenga acceso al modelo. |
| Limitar las herramientas a consultas de planes y horarios existentes; el backend valida argumentos y resultados. | Las respuestas no pueden ampliar permisos ni inventar datos de negocio. | Dar al modelo acceso a URLs, SQL o servicios arbitrarios. |
| Construir los datos afirmables de la respuesta desde los resultados de herramientas, no desde memoria del modelo. | El prompt puede quedar desactualizado y una salida del modelo puede inventar precios. | Poner precios y horarios fijos en instrucciones. |
| Conservar conversación temporal y límite de 150 caracteres del diseño vigente en esta rama. | Evita tomar como definitivos valores contradictorios de otra rama. | Historial persistente y límite de 500 caracteres descritos por Rodrigo. |
| Preparar límites de frecuencia/presupuesto compartidos antes de habilitar llamadas reales en más de una instancia. | La cuota no puede depender solo de memoria de un proceso. | Contador local por proceso, útil solo en pruebas aisladas. |

La interfaz y el backend se prueban con un proveedor falso. No se crean claves ni variables de entorno en esta etapa documental.
