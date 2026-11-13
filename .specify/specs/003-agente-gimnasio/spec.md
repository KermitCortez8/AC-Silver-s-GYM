# Agente de atención del gimnasio · primera entrega

**ID:** `003-agente-gimnasio` · **Rama:** `levano/agenteAgente` · **Fecha:** 2026-11-12.
**Estado:** versión pública implementada y verificada con dobles de prueba; conexión real a Groq comprobada manualmente con datos sintéticos.
**Contexto:** [fuentes y código actual](context.md).

## 1. Sprint Goal

Un visitante pregunta en español por planes, clases e información pública del gimnasio. El agente consulta catálogos actuales o fichas públicas revisadas y responde con datos verificables. Si no puede confirmarlos, ofrece una salida útil sin inventar información. Esta entrega demuestra el recorrido desde la interfaz hasta las consultas del negocio y el proveedor de IA.

## 2. User Story

### US1 · Consultar planes y clases (P1)

Como visitante, quiero preguntar por planes o clases para decidir si me registro o consulto un horario.

**Prueba independiente:** con catálogos de prueba conocidos, preguntar por un plan y una clase; comprobar que las respuestas corresponden a los datos consultados y permiten abrir la pantalla pública pertinente.

1. Dado un plan público, cuando pregunto por él, entonces recibo su nombre, precio y duración actuales.
2. Dada una clase activa, cuando pregunto por horarios, entonces recibo los horarios publicados.
3. Dado un catálogo vacío o no disponible, cuando pregunto, entonces el agente reconoce que no puede confirmar la información.

### US2 · Atención dentro de límites (P1)

Como visitante, quiero recibir orientación sin que el agente revele datos privados o ejecute operaciones que requieren identificación y confirmación.

**Prueba independiente:** pedir una matrícula, un cobro o datos de otro cliente; comprobar que no hay escritura ni revelación de información privada.

## 3. Acceptance Criteria

1. **CA-01.** Dada una pregunta sobre planes o clases, cuando existen datos públicos, el agente consulta la fuente correspondiente y responde usando los valores recibidos; no usa precios u horarios fijos en sus instrucciones.
2. **CA-02.** Si el proveedor propone datos distintos de los consultados, el sistema evita afirmarlos y muestra una respuesta segura.
3. **CA-03.** Si un visitante solicita datos privados, matrícula, pago, cancelación o activación, el agente explica el siguiente paso permitido sin ejecutar la operación.
4. **CA-04.** Si el proveedor o catálogo falla, la interfaz informa la indisponibilidad y conserva acceso a las pantallas públicas.
5. **CA-05.** Si un mensaje contiene credenciales o datos de pago, se intercepta antes de remitirlo al proveedor y no se incluye en registros.
6. **CA-06.** Si el usuario o proveedor intenta cambiar permisos o solicitar una herramienta no autorizada, el sistema rechaza la operación.
7. **CA-07.** Dos conversaciones simultáneas no comparten contexto; una segunda consulta del mismo visitante conserva solo el contexto necesario.
8. **CA-08.** Los casos normales, de error y de abuso se pueden repetir con proveedor falso y datos de prueba sin pagos, correos ni llamadas externas reales.
9. **CA-09.** Una pregunta sobre servicios, ubicación o preparación para la primera visita devuelve una ficha pública pertinente con enlace a su página; una selección de tema ajeno o argumentos extra se rechaza.

| Criterio | Evidencia |
| --- | --- |
| CA-01, CA-02 | Pruebas de catálogos cambiantes y proveedor falso; recorrido funcional desde la interfaz. Véase [validación](validation.md). |
| CA-03, CA-05, CA-06 | Casos de permisos, privacidad y herramientas rechazadas; comprobar ausencia de escrituras. |
| CA-04 | Prueba de fallo del proveedor y acceso a pantallas públicas. |
| CA-07 | Prueba de aislamiento de dos conversaciones. |
| CA-08 | Batería automatizada con datos sintéticos y registro de ejecución. |
| CA-09 | Pruebas de fichas públicas, argumentos rechazados y recorrido de tipos de entrenamiento en tres motores. |

### Requisitos funcionales

- **FR-001:** Consultar planes y horarios publicados mediante herramientas autorizadas y responder desde sus resultados (CA-01, CA-02).
- **FR-002:** Proponer navegación a las pantallas públicas relacionadas, sin crear registros ni asumir identidad del visitante (CA-01, CA-03).
- **FR-003:** Bloquear datos sensibles, operaciones prohibidas y cambios de instrucciones por texto o salida del proveedor (CA-03, CA-05, CA-06).
- **FR-004:** Mantener contexto mínimo y aislado, con salida comprensible ante fallos (CA-04, CA-07).
- **FR-005:** Permitir pruebas del recorrido con dobles controlados de proveedor y datos (CA-08).
- **FR-006:** Consultar fichas aprobadas de información pública sin abrir archivos internos al modelo (CA-09).

### Entidades y resultados medibles

Turno de conversación, consulta autorizada y respuesta basada en datos públicos. No se crean entidades de cliente, matrícula o pago en esta entrega.

- **SC-001:** En los casos automatizados, el 100 % de importes y horarios afirmados coinciden con los datos devueltos por la fuente pública.
- **SC-002:** En casos de abuso y error, se observan cero escrituras de negocio y cero envíos de credenciales o datos de pago al proveedor.
- **SC-003:** Los recorridos de planes y clases se muestran desde la interfaz con resultados reproducibles y evidencia registrada.

## 4. Technical Constraints

- Mantener las capas de presentación, aplicación, dominio e infraestructura. La interfaz solicita atención; el backend controla las herramientas y valida su resultado.
- Reutilizar las consultas públicas de planes y horarios. El agente no consulta tablas directamente ni copia precios u horarios en el prompt.
- Las fichas de información general se mantienen revisadas a partir de la web pública; no se indexa todo el repositorio ni se envían sus documentos privados al proveedor.
- El modelo y sus credenciales pertenecen al backend. La elección técnica se documenta en el plan; esta spec no crea claves ni variables de entorno.
- Las operaciones privadas conservan la sesión y permisos existentes. Esta entrega es pública y de solo lectura.
- El [SPEC anterior](../002-chatbot-clientes/spec.md) y los prototipos orientan la experiencia; no prueban una integración terminada. El trabajo de Rodrigo se consulta solo como referencia, sin traerlo automáticamente a esta rama.
- El mensaje conserva el máximo de 150 caracteres y el historial efímero del diseño vigente en esta rama. El plan define límites compartidos de frecuencia y presupuesto antes de programar.

## 5. Guardrails

- El modelo puede solicitar únicamente las consultas públicas autorizadas para esta entrega. El backend decide si las ejecuta.
- Una respuesta no cobra, activa membresías, matricula, cancela, modifica precios ni consulta datos de terceros.
- No exponer claves, tokens, datos de pago, mensajes ajenos ni información personal al proveedor o en logs.
- No usar datos fijos del prompt como fuente de verdad de precios, cupos u horarios actuales.
- Aislar pagos, correos y servicios externos durante las pruebas; usar datos controlados.

## 6. Edge Cases

| Caso | Resultado esperado | Criterio |
| --- | --- | --- |
| Catálogo cambia entre consultas | La nueva respuesta refleja la fuente reciente. | CA-01 |
| Catálogo vacío, lento o con error | No se inventan datos; se ofrece alternativa. | CA-02, CA-04 |
| Herramienta ajena o argumentos inválidos | Se rechaza sin efecto externo. | CA-03, CA-06 |
| Contraseña o tarjeta en el mensaje | Advertencia local; el dato no llega al proveedor. | CA-05 |
| Conversaciones simultáneas | Cada una conserva su contexto aislado. | CA-07 |
| Tema público desconocido o argumento malformado | Se rechaza sin consultar otras fuentes. | CA-09 |

### Decisiones de alcance

- La entrega sigue siendo pública y de solo lectura: planes y horarios actuales mediante herramientas controladas, más información general de las páginas públicas.
- Matrículas, cancelaciones, compras y consultas privadas serán ampliaciones con criterios y confirmaciones propios.
- El trabajo de Rodrigo se usa como referencia, según indicó el usuario; no se fusiona en esta rama.

## 7. Definition of Done

- [ ] El equipo revisa esta primera versión antes de integrarla al producto compartido.
- [x] La matriz relaciona cada criterio con los casos unitarios, de integración y funcionales pertinentes.
- [ ] Se registra el antes y se repite la misma batería: no existe una línea base documentada anterior a la implementación de esta rama.
- [x] Se demuestra en la interfaz el recorrido planes/clases y la salida ante fallo con API simulada.
- [x] Se registran resultados reales y límites de verificación en [validación](validation.md).
