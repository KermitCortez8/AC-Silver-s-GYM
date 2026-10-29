# Guía práctica: del planteamiento al chatbot con Spec Kit

Aplicar esta guía cuando el usuario indique expresamente que quiere utilizar
Spec Kit. Mientras tanto, no generar specs, planes ni tareas para sus pedidos.

**Los prompts `$...` se escriben en el chat de Codex. Los comandos `git`,
`python`, `bash`, `npm`, `docker` y `deno` se ejecutan en la terminal.** Envía
cada prompt junto con su texto, no solo el nombre de la skill. Esta guía usa las
etapas oficiales instaladas de GitHub Spec Kit y el hook del proyecto.

Codex CLI y la extensión permiten mencionar una skill mediante `$` o buscarla
con `/skills`, según [OpenAI Docs: skills](https://learn.chatgpt.com/docs/build-skills).
Los nombres locales son `$speckit-specify`, `$speckit-plan`, etc. El directorio
`.agents/skills/` conserva sus enlaces a `.specify/.codex/skills/` para que Codex
las descubra. Si no aparecen tras un cambio de instalación, reinicia Codex desde
la raíz y comprueba los enlaces; no dupliques las skills en otra carpeta.

El chatbot es un ejemplo de alcance. Este documento no crea una feature ni
acredita que el chatbot esté implementado. Tampoco es necesario ejecutar los
ejemplos para leer la guía. Reemplaza `NNN-chatbot-clientes`
por el nombre real de la carpeta creada. Todo parte de la raíz:

```bash
cd /workspaces/AC-Silver-s-GYM
```

La [estructura](estructura-codex.md) conserva docs con los cinco documentos,
.codex con los componentes del asistente, contratos en base/modulos y features
en .specify/specs. No hay alias docs/specs en la raíz.

El recorrido completo es:

| Momento | Prompt en Codex | Resultado esperado |
| --- | --- | --- |
| Idea y consulta de base | `$gym-spec-driven` con «solo analiza» | Módulos, reutilización y decisiones; sin crear feature. |
| Activación y requisitos | `$speckit-specify` | Una feature con `context.md` y `spec.md`. |
| Aclaraciones | `$speckit-clarify` | Decisiones registradas en esa spec. |
| Calidad de requisitos, opcional | `$speckit-checklist` | Checklist de requisitos, no pruebas ejecutadas. |
| Diseño | `$speckit-plan` | `plan.md` y artefactos de diseño pertinentes. |
| Desglose | `$speckit-tasks` | `tasks.md` trazable a los criterios. |
| Revisión previa | `$speckit-analyze` | Hallazgos de consistencia y revisión local. |
| Código y verificación | `$speckit-implement` | Implementación y tareas comprobadas. |
| Comprobación de faltantes | `$speckit-converge` | Tareas adicionales del mismo alcance, si faltan partes. |
| Cierre | Prompt de auditoría y hook `close` | Contratos vivos y `validation.md` con evidencia real. |

Puedes avanzar por etapas con los prompts de esta guía o pedir el recorrido
completo expresamente. En ambos casos se utiliza una sola feature y la sesión
actual. Los perfiles de revisor/auditor no abren otros agentes.

## 1. Comprobar el entorno — terminal

```bash
git branch --show-current
git status --short --branch
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

Comprueba la rama antes de guardar cambios. Actualmente este trabajo se mantiene
en `feat/correcciones`; el generador de features no crea ni cambia ramas Git.
Un número de spec identifica una carpeta, no la rama activa. Conserva cualquier
cambio local previo al comenzar y distingue su diff del trabajo del chatbot.

El CLI es opcional para las etapas de chat y scripts. En este espacio ya existe:

```bash
.specify/.venv/bin/specify version
.specify/.venv/bin/specify integration list
```

Solo si falta en un clon nuevo, instalar el CLI fijado sin regenerar el proyecto:

```bash
python -m venv .specify/.venv
.specify/.venv/bin/python -m pip install -r .specify/integrations/requirements.txt
```

En Windows usar WSL o un entorno con Bash y enlaces simbólicos operativos.

## 2. Plantear y analizar la idea — chat

```text
$gym-spec-driven

Quiero analizar un chatbot para clientes del gimnasio que responda
sobre planes, horarios y su propia membresía.

Consulta primero la base implementada, los contratos de módulos,
arquitectura, seguridad, reglas, código y pruebas.

Identifica qué podemos reutilizar, qué módulos afecta y qué decisiones
debemos resolver. En esta etapa solo analiza, sin implementar.
```

Para este ejemplo, revisar identidad, membresías, planes y horarios, y sus
relaciones según el índice. La base `000` y los contratos parten de una referencia
histórica: contrastarlos con el código de la rama activa, incluidas sus
correcciones de validación y errores. Si difieren, registrar qué archivo demuestra
el comportamiento actual. La base `000` se consulta; no es trabajo pendiente.

### Qué debe consultar Codex

Primero, [constitución](../memory/constitution.md), [base 000](../specs/000-base-implementada/spec.md),
[índice modular](../base/modulos/README.md), [arquitectura](../docs/arquitectura.md),
[diseño](../docs/diseno.md), [seguridad](../.codex/rules/seguridad.md) y
[DoD](../docs/DoD.md). Después, contratos y fuentes del área:

| Módulo | Qué reutilizar o proteger | Fuentes iniciales |
| --- | --- | --- |
| [MOD-01](../base/modulos/01-identidad-acceso.md) | Bearer, roles, activación y aislamiento de sesiones. | [Dependencias HTTP](../../backend/presentation/dependencies.py), [AuthService](../../backend/application/services/auth_service.py) y [sesión frontend](../../frontend/src/application/stores/sessionStore.js). |
| [MOD-03](../base/modulos/03-membresias-pagos.md) | Lectura de la membresía propia, vigencia y estado; conservar importes/pagos. | [Rutas de membresía](../../backend/presentation/routes/memberships_routes.py) y [reglas](../../backend/domain/services/memberships_rules.py). |
| [MOD-04](../base/modulos/04-planes-promociones.md) | Catálogo de planes y reglas vigentes, sin inventar precios o descuentos. | [Rutas de planes](../../backend/presentation/routes/memberships_routes.py) y [catálogo público frontend](../../frontend/src/application/services/publicCatalog.js). |
| [MOD-05](../base/modulos/05-horarios-matriculas.md) | Horarios públicos activos y su proyección sin datos de clientes. | [Rutas de horarios](../../backend/presentation/routes/gym_routes.py). |
| [MOD-10](../base/modulos/10-paneles-configuracion.md) | Integración de interfaz y servicios por instancia de Pinia. | [Bootstrap frontend](../../frontend/src/bootstrap.js), [puertos](../../frontend/src/application/ports/services.js) y [router](../../frontend/src/presentation/router/index.js). |

No añadir notificaciones, tienda, rutinas ni otros módulos porque existan en el
repositorio: se incluyen si el alcance del chatbot realmente los necesita.

Hay dos bases distintas: **Codex consulta `.specify/` para desarrollar**;
**el chatbot consulta datos autorizados de la aplicación al ejecutarse**.
Instalar Spec Kit no conecta el modelo con Supabase ni convierte las specs en
conocimiento público del chatbot. No enviar contratos internos, secretos o la
base completa al proveedor como contexto de conversación.

### Decidir el alcance antes de planificar

Una primera versión acotada puede atender a clientes autenticados y habilitados,
responder sobre planes/horarios y explicar su propia membresía. Puede usar una
respuesta completa por solicitud y conservar la conversación solo en memoria de
la interfaz, hasta cerrar o sustituir la sesión. Es una **propuesta para acordar**,
no una funcionalidad existente ni una decisión ya aprobada de producto.

| Decisión | Qué debe quedar escrito en la spec |
| --- | --- |
| Audiencia y permisos | Si atiende solo al rol `user`, también a personal o a visitantes; qué información corresponde a cada uno. |
| Datos permitidos | Campos concretos de planes, horarios y membresía; qué resumen puede recibir el proveedor y qué datos se excluyen. |
| Proveedor y modelo | Proveedor elegido, modelo disponible, configuración y tratamiento de datos aceptado; comprobar su documentación al elegirlo. |
| Memoria | Solo conversación de sesión o historial persistido; si hay persistencia, propietario, retención y borrado. |
| Interfaz | Página o panel, entrada de navegación, estados vacío/cargando/error y respuesta completa o streaming. |
| Límites y coste | Longitud de entrada, contexto/respuesta, frecuencia por cuenta, concurrencia, tiempo máximo y presupuesto. Escribir valores y cómo se aplican. |
| Fallos | Qué ocurre sin proveedor/configuración, con timeout, límite excedido o datos insuficientes; condiciones de reintento. |
| Acciones | Si solo informa o ejecuta operaciones; la propuesta inicial solo informa. |

**Restricción actual de identidad:** `get_current_user` vuelve a resolver la
cuenta. Un cliente necesita activación y membresía pagada y vigente para el acceso
controlado por autenticación. Un token vencido se rechaza; el bloqueo de activación
puede devolver 403. No se debe prometer atención autenticada a un cliente vencido
saltándose esa dependencia. Para atenderlo habrá que especificar expresamente
la diferencia de acceso en MOD-01, o diseñar un chat público con datos públicos.

No elegir un proveedor ni crear una tabla de conversaciones por suposición.
Si se mantiene la propuesta sin historial, no hace falta una migración de
conversaciones. Un límite global por cuenta debe funcionar con los procesos y
réplicas previstos; un contador en memoria de un proceso no demuestra ese límite.

## 3. Activar Spec Kit y crear una sola feature — terminal

Desde este punto se inicia el flujo, cuando decidas implementar el módulo con
Spec Kit. Para seguir esta guía, ejecuta el generador una sola vez:

```bash
bash .specify/scripts/bash/create-new-feature.sh \
  --json --short-name chatbot-clientes \
  "Chatbot para consultar planes, horarios y la membresía del cliente autenticado"
```

El generador asigna el número, prepara spec.md y context.md y selecciona la
feature mediante feature.json local. No crea código de producto ni cambia rama.
No volver a ejecutarlo por cada etapa. Si ya existe una feature del cambio,
continuarla como se indica en el paso 13.

Toma el nombre de la carpeta de `SPEC_FILE` en el JSON. Selecciónala para las
comprobaciones de tu terminal, sustituyendo el marcador por ese nombre real:

```bash
export SPECIFY_FEATURE_DIRECTORY="$PWD/.specify/specs/NNN-chatbot-clientes"
bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

Si prefieres hacerlo todo desde el chat, pide a `$speckit-specify` que ejecute
este mismo generador una vez y complete el contexto. Es una alternativa al paso
de terminal, no una segunda creación. La variable exportada afecta a esa terminal;
en el chat menciona siempre la misma carpeta para evitar selecciones ambiguas.

## 4. Completar contexto y especificación — chat

```text
$speckit-specify

Activa Spec Kit para implementar este módulo.
Completa la feature existente NNN-chatbot-clientes.
No crees otra feature.

Lee las fuentes y pruebas de los contratos y completa context.md con
módulos, fuentes leídas, reglas, reutilización y comprobaciones elegidas.

Completa spec.md con los siete componentes:
Sprint Goal, User Story, Acceptance Criteria, Technical Constraints,
Guardrails, Edge Cases y Definition of Done.

Alcance propuesto para esta primera versión, sujeto a las decisiones acordadas:
- Clientes autenticados y habilitados según MOD-01; solo rol user.
- Consultas sobre planes y horarios.
- Consulta de la propia membresía.
- Sin ejecutar compras, pagos, matrículas ni modificaciones.
- Conversación de sesión, sin historial persistido; respuesta completa sin streaming.

Conserva las cuatro capas, permisos y Docker de frontend y backend.
Incorpora las decisiones del análisis. Expón las dudas de producto aún reales,
incluidos proveedor/modelo, datos enviados y valores de límites.
En esta etapa prepara requisitos y contexto; no escribas código de producto.
```

| Componente | Aplicación al ejemplo |
| --- | --- |
| Sprint Goal | Permitir consultas del cliente desde la aplicación. |
| User Story | Como cliente, consultar servicios y membresía mediante conversación. |
| Acceptance Criteria | Autenticación, respuestas fundamentadas, privacidad y fallos con criterios verificables. |
| Technical Constraints | Reutilizar Vue/Pinia, FastAPI, servicios y Docker; credenciales en backend. |
| Guardrails | Conservar permisos y excluir operaciones económicas o modificaciones. |
| Edge Cases | Membresía inexistente, sesión vencida, proveedor caído o acceso a otra cuenta. |
| Definition of Done | Criterios cubiertos, pruebas y documentación actualizadas. |

Ejemplo de aceptación: una consulta sobre membresía utiliza exclusivamente la
identidad validada por el backend. Cualquier límite de tiempo, tamaño o uso
acordado debe quedar concretado en la spec.

### Ejemplos de criterios que deben convertirse en pruebas

Estos criterios corresponden al alcance propuesto. Ajustarlos al acuerdo final;
no son una aprobación ni evidencia de implementación:

1. **CA-01.** Con una sesión de cliente habilitado, enviar un mensaje permite
   obtener respuesta; sin token válido se rechaza la solicitud y con un rol
   excluido o cliente bloqueado se deniega sin consultar al proveedor.
2. **CA-02.** Si un mensaje o identificador intenta consultar otra cuenta, ningún
   dato ajeno se consulta para la respuesta ni se transmite al proveedor. El
   cliente se deriva de la sesión validada en servidor.
3. **CA-03.** Ante una consulta sobre planes, sus precios y duración coinciden
   con la fuente autorizada del caso de prueba; sin datos no se inventa oferta.
4. **CA-04.** Ante una consulta de horarios solo se utiliza la proyección pública
   de horarios activos. No se revelan matrículas ni identidades de asistentes.
5. **CA-05.** La consulta de membresía respeta sus estados y fechas de Perú,
   incluido el último día de vigencia; no recalcula un importe contratado.
6. **CA-06.** Si falta configuración o falla el proveedor, se muestra el error
   acordado sin credenciales, respuestas internas ni datos personales en logs.
7. **CA-07.** Una entrada vacía o que supera el límite acordado se rechaza antes
   de llamar al proveedor; se respetan las cuotas y tiempos definidos en la spec.
8. **CA-08.** Al cerrar o cambiar de sesión se vacía la conversación y una
   respuesta pendiente de la cuenta anterior no se muestra en la nueva.
9. **CA-09.** La interfaz permite enviar, ver carga, recibir respuesta y recuperarse
   de errores según el diseño; texto generado con HTML se muestra como texto seguro.
10. **CA-10.** Una petición de pago, compra, matrícula o cambio de datos no ejecuta
    esa operación; instrucciones para ignorar permisos no amplían el acceso.

Los valores de tamaño, cuotas y tiempos no pueden quedar como «razonables» o
«rápidos»: completarlos en la aclaración. Los contratos de API deben concretar
los estados de validación, indisponibilidad, timeout y límite excedido.

`context.md` debe conservar las fuentes realmente leídas, los módulos con sus IDs
en negrita, restricciones, reutilización y pruebas elegidas. Completar también
su «Evaluación específica del cambio» antes del plan. No basta con copiar enlaces.

La tabla de evidencia de `spec.md` puede enlazar inicialmente el contexto y las
fuentes/pruebas existentes, indicando qué comprobación nueva se proyecta. Las
pruebas nuevas se describen como rutas propuestas hasta crearlas; no inventar
enlaces Markdown a archivos inexistentes para pasar el hook. Al implementar,
añadir enlaces a las pruebas reales y sus resultados en `validation.md`.

## 5. Resolver ambigüedades — chat

```text
$speckit-clarify

Revisa NNN-chatbot-clientes. Resuelve ambigüedades de comportamiento,
privacidad, proveedor, datos permitidos y fallos. Registra las respuestas.
```

Responder las preguntas que afecten al resultado. Si la spec ya es precisa,
no hace falta inventar aclaraciones. Si faltan decisiones de alcance, privacidad
o proveedor necesarias para construirlo, resolverlas antes del plan. Los
resultados quedan en la misma spec; no crear otra feature al contestar.
Opcionalmente:

```text
$speckit-checklist

Genera una checklist de calidad de requisitos para el chatbot,
centrada en permisos, privacidad, respuestas y fallos del proveedor.
```

Esta checklist revisa los requisitos escritos. Las pruebas del producto se
planifican y ejecutan por separado.

## 6. Preparar el plan — chat

```text
$speckit-plan

Prepara el plan de NNN-chatbot-clientes.
Enlaza context.md e identifica componentes, servicios y pruebas reutilizables.
Define interfaz de chat, caso de uso backend, adaptador del proveedor
y consultas autorizadas. Incluye configuración, Docker, pruebas y revisión visual.
Las credenciales privadas permanecen en el backend.
Define contrato HTTP, campos permitidos por consulta, errores, límites y
aislamiento de sesión. Conserva los mecanismos actuales de transporte y validación.
No añadas historial SQL, RAG, embeddings o un servicio aparte sin justificarlo
con los requisitos acordados. No implementes todavía.
```

El script oficial ejecuta el hook de plan antes de crear plan.md. Puedes
comprobar las mismas precondiciones directamente en terminal:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-chatbot-clientes --stage plan
```

### Cómo debe encajar el módulo en el código

El plan concreta nombres y rutas. Esta distribución orienta el diseño, sin crear
ahora los archivos ni obligar a añadir capas vacías:

| Parte | Integración esperada |
| --- | --- |
| Presentación backend | Ruta de chat autenticada, esquema de entrada/salida y errores HTTP. Registrar el router en el ensamblaje actual. Un posible endpoint es `POST /api/chatbot/messages`, aún propuesto. |
| Aplicación backend | Caso de uso que obtiene datos del cliente validado y catálogos permitidos mediante servicios existentes; prepara solo el contexto autorizado y llama al puerto del proveedor. |
| Dominio | Reutilizar reglas de vigencia, importes y fechas; añadir reglas propias solo si el chatbot las necesita. |
| Infraestructura backend | Adaptador del proveedor elegido, configuración privada, timeout y tratamiento de fallos. Inyectarlo desde el bootstrap para sustituirlo en pruebas. |
| Aplicación frontend | Estado/composable del chat, envío mediante los servicios de esa instancia de Pinia y limpieza de sesión/respuestas obsoletas. |
| Infraestructura frontend | Adaptador que usa el cliente HTTP instalado. Conservar autenticación, validación de respuestas, timeout y mensajes de error actuales. |
| Presentación frontend | Vista/panel y navegación para el rol acordado; componentes y estilos existentes, estados de carga y contenido seguro. |

Puntos de integración actuales: [bootstrap backend](../../backend/app/bootstrap.py),
[registro de rutas](../../backend/app/main.py), [bootstrap frontend](../../frontend/src/bootstrap.js),
[cliente HTTP](../../frontend/src/infrastructure/services/apiClient.js),
[transporte y cancelación](../../frontend/src/infrastructure/services/httpTransport.js) y
[validación de respuestas](../../frontend/src/application/services/responseValidation.js).
El transporte actual consume la respuesta completa; el streaming exigiría otro
diseño explícito y sus propias pruebas. No conectar el proveedor desde una vista
ni consultar Supabase directamente desde el componente de chat.

El backend filtra los datos **antes** de enviarlos al modelo. Un prompt que diga
«no reveles datos» no sustituye la autorización. No aceptar SQL generado por el
modelo ni darle las claves de Supabase. El MVP informativo no necesita puertos
que ejecuten pagos, matrículas o escrituras.

Frontend y backend siguen en sus contenedores actuales. La dependencia del
proveedor se instala en el backend y sus secretos se leen desde configuración
del servidor. El archivo `backend/.env` ya se inyecta por Compose. Las variables
`VITE_*` son públicas: no guardar allí una clave del modelo. El tiempo del
proveedor debe dejar margen al timeout HTTP del frontend. El nombre de variables
del chatbot se fija en el plan; aún no existen por documentarlas aquí.

`speckit-plan` puede producir `research.md`, `data-model.md`, `contracts/` y
`quickstart.md` dentro de la feature. Si no hay persistencia, el modelo de datos
puede describir solicitudes y respuestas sin introducir una tabla.

## 7. Generar las tareas — chat

```text
$speckit-tasks

Genera las tareas de NNN-chatbot-clientes a partir de spec y plan.
Relaciona cada tarea con criterios y rutas concretas. Incluye implementación,
pruebas, Docker cuando corresponda, documentos y evidencia de cierre.
```

Resultado: tasks.md con secuencia y casillas de seguimiento. Cada criterio
necesita tareas y evidencia prevista.

Una secuencia útil es: contratos y dobles del proveedor; pruebas de autorización
y aislamiento; caso de uso y adaptador; ruta HTTP; estado/interfaz frontend;
pruebas de sesión y errores; comprobación Docker y visual; documentación y cierre.
Cada tarea lleva ID, ruta concreta y sus `CA-XX`. El plan decide las dependencias:
no marcar como paralelas tareas que modifiquen el mismo archivo.

Ejemplo de formato, con una ruta nueva todavía propuesta:

```text
- [ ] T003 [US1] CA-01 CA-02 Cubrir autenticación y aislamiento en backend/tests/test_chatbot.py con un proveedor falso.
```

## 8. Analizar consistencia — chat

```text
$speckit-analyze

Comprueba spec, plan y tareas de NNN-chatbot-clientes.
Aplica el perfil de revisor configurado en settings.json.
Identifica contradicciones, criterios sin tareas y conflictos con reglas existentes.
```

Se realiza después de generar tareas y sin modificar artefactos durante el
análisis. Corregir los hallazgos mediante la etapa correspondiente. El perfil
se utiliza en esta sesión, sin abrir otros agentes.

No iniciar código si hay un conflicto de permisos, datos sin fuente o criterios
sin tareas. Si cambia un requisito, volver a specify/clarify; si cambia el diseño,
corregir el plan y ajustar las tareas afectadas. Conservar IDs y evidencia válida.

## 9. Implementar — chat

```text
$speckit-implement

Implementa NNN-chatbot-clientes siguiendo contexto, spec, plan y tareas.
Reutiliza módulos existentes, conserva contratos y permisos, ejecuta las
comprobaciones pertinentes y marca tareas solo cuando estén verificadas.
```

Los prerrequisitos oficiales con --require-tasks ejecutan el hook de implementación.
Comprobación directa equivalente:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-chatbot-clientes --stage implement
bash .specify/scripts/bash/check-prerequisites.sh \
  --json --require-spec --require-tasks --include-tasks
```

Estos checks validan documentos y trazabilidad; no crean el chatbot ni prueban
sus respuestas. Con la variable del paso 3 se verifica la feature seleccionada.

## 10. Ejecutar las pruebas pertinentes — terminal

El plan determina las pruebas específicas del chatbot: autorización, aislamiento
por cliente, respuestas y fallos del proveedor con dobles de prueba. Las pruebas
automatizadas deben poder ejecutarse sin llamadas de pago ni servicios reales.
Un doble verifica los contratos; no acredita por sí solo la calidad de las
respuestas del modelo elegido.

### Matriz mínima para este ejemplo

| Comprobación | Criterios | Qué verificar |
| --- | --- | --- |
| Permisos del endpoint | CA-01 | Usuario habilitado, token ausente/vencido, cliente bloqueado y roles excluidos; no llamar al proveedor cuando el acceso se deniega. |
| Dos clientes sintéticos | CA-02 | Intentos con identificadores en payload/mensaje y revisión del contexto que recibe el doble: ningún dato del otro cliente. |
| Datos controlados | CA-03…CA-05 | Plan/precio/duración, solo horarios públicos activos, fecha de Perú y ausencia de datos; las respuestas no inventan hechos. |
| Fallos del adaptador | CA-06 | Configuración ausente, timeout, respuesta inválida y error externo con mensaje seguro, sin filtrar datos en logs. |
| Límites | CA-07 | Entradas vacías, longitud exacta y superior al límite, cuota, contexto y tiempos; reloj/proveedor controlados. |
| Sesión sustituida | CA-08 | Iniciar solicitud con A, cerrar sesión, entrar con B y resolver la solicitud de A; no aparece su respuesta. |
| Interfaz | CA-09 | Vacío, envío, carga, respuesta, error y reintento; teclado, pantalla móvil y contenido que intenta inyectar HTML. |
| Solo lectura | CA-10 | Peticiones de cobro, matrícula o modificación no invocan servicios de escritura ni amplían permisos. |

Pruebas de regresión existentes que conviene revisar y seleccionar según el diff:

- Backend: [permisos y cargas por recurso](../../backend/tests/test_scoped_operations.py),
  [vigencia](../../backend/tests/test_membership_expiration.py),
  [capas](../../backend/tests/test_layer_boundaries.py),
  [regresiones](../../backend/tests/test_review_regressions.py) y
  [control de errores](../../backend/tests/test_module_error_control.py).
- Frontend: [sesión](../../frontend/tests/14-session-validation.test.js),
  [capas](../../frontend/tests/23-layer-boundaries.test.js),
  [contexto por aplicación](../../frontend/tests/28-application-context.test.js),
  [errores HTTP](../../frontend/tests/32-http-error-control.test.js) y
  [validación de respuestas](../../frontend/tests/35-response-identifiers.test.js).

Las pruebas específicas nuevas se añaden en las carpetas actuales `backend/tests/`
y `frontend/tests/`; no crear otro framework sin necesidad. El proyecto frontend
utiliza `node --test`, no un script `lint`. Registrar también la revisión visual:
el build y las pruebas de estado no prueban solos cómo se ve y usa el panel.

### Comandos locales si eliges verificar sin contenedores

Requieren dependencias instaladas. En un clon que no las tenga, preparar el
entorno de desarrollo y utilizar `npm ci` sobre el lockfile existente:

```bash
python -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
```

No hace falta recrear un entorno ya preparado. Desde la raíz, para las suites:

```bash
(cd backend && AUTH_SECRET_KEY=solo-pruebas-locales-no-produccion-0123456789 .venv/bin/python -m pytest tests/ -q)
(cd backend && .venv/bin/python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics)
npm --prefix frontend test
npm --prefix frontend run build
```

Si usas otro entorno Python de desarrollo, sustituye `.venv/bin/python` por su
intérprete. La clave del ejemplo es exclusiva de pruebas. Los fixtures y dobles
deben evitar que la suite use datos o proveedores reales.

### Comandos con los targets Docker existentes

Para comprobar las suites como CI, utiliza los targets `test` de ambos
Dockerfiles. Son una alternativa para ejecutar esas suites; registra el entorno
que hayas utilizado, sin declarar ejecuciones locales adicionales:

```bash
docker build --target test -t gym-backend-test ./backend

docker run --rm --network none \
  --env AUTH_SECRET_KEY=solo-pruebas-locales-no-produccion-0123456789 \
  gym-backend-test

docker build --target test -t gym-frontend-test ./frontend

docker run --rm --network none gym-frontend-test

docker build -t gym-frontend-check ./frontend
```

El último build comprueba además la compilación de la imagen de producción del
frontend. Las imágenes `test` ejecutan las suites; los contenedores de ejecución
habituales no incluyen todas las dependencias ni archivos de prueba.

### Arranque conjunto y revisión manual

Preparar `.env` y `backend/.env` según [arquitectura](../docs/arquitectura.md),
sin sobrescribir los archivos ya configurados. Tras implementar, incluir también
las variables privadas del proveedor que haya definido el plan. Entonces:

```bash
docker compose config --quiet
docker compose up --build --detach --wait
docker compose ps
```

Abre `http://localhost:5173`, inicia sesión con una cuenta de prueba habilitada
y comprueba conversación, fuente de datos, permisos, carga, errores y cambio de
sesión. El frontend usa Nginx y el proxy `/api/` hacia FastAPI; ambos contenedores
comparten red y Compose publica los puertos desde el servicio backend. El volumen
local conserva archivos; los datos de negocio están en Supabase externo.

La sonda normal comprueba Supabase. Un contenedor saludable no acredita que la
conversación funcione. Si falla el arranque, revisar configuración y logs locales
sin copiarlos con secretos a la documentación:

```bash
docker compose logs --tail=100 backend frontend
```

Una revisión con proveedor real requiere que ese proveedor y su entorno de prueba
estén disponibles y que el uso esté autorizado. Si no se ejecutó, registrar que
solo se comprobó el adaptador con dobles; no declarar aprobada una integración
externa o evaluación de calidad omitida.

Al terminar el uso local:

```bash
docker compose down
```

Solo si cambia la función de correo:

```bash
deno check supabase/functions/schedule-emails/index.ts
deno test supabase/tests/
```

PostgreSQL requiere su contenedor desechable específico según el [DoD](../docs/DoD.md)
y [pr-validation.yml](../../.github/workflows/pr-validation.yml). Si no se prepara,
las pruebas se omiten y debe registrarse. No forma parte del Compose de aplicación.

## 11. Comprobar pendientes — chat

```text
$speckit-converge

Contrasta NNN-chatbot-clientes con el código. Registra como tareas
las partes del alcance definido que todavía falten.
```

Si aparecen tareas nuevas, ejecutar `$speckit-implement` y después volver a
`$speckit-converge`. Verificar las correcciones pertinentes sin ampliar alcance.
Converge solo añade tareas de faltantes; no implementa código ni reescribe la
spec o el plan. Si ya se cumple el alcance, no debería añadir una fase vacía.

## 12. Revisar, documentar y cerrar — chat y terminal

```text
Aplica el perfil de auditor indicado para close en settings.json en esta sesión.
Revisa los criterios y las reglas afectadas de NNN-chatbot-clientes.
Actualiza contratos y documentos, completa validation.md con resultados,
fallos, omisiones y evidencia, y comprueba la Definition of Done.
No marques como terminado un criterio cuya comprobación requerida falte.
```

Terminal:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-chatbot-clientes --stage close
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
git diff --check
```

| Archivo | Evidencia que conserva |
| --- | --- |
| context.md | Módulos, fuentes leídas, reglas, dependencias y reutilización. |
| spec.md | Siete componentes y aceptación. |
| plan.md | Diseño e integración, pruebas y comprobaciones. |
| tasks.md | Tareas y seguimiento por criterio. |
| validation.md | Ejecuciones reales, resultados y límites. |

El hook comprueba estructura y trazabilidad; las pruebas del producto demuestran
comportamiento. La base 000 no se reimplementa; actualizar los contratos vivos.

El módulo nuevo necesita un contrato vivo de siete componentes después de su
implementación. Si `MOD-12` sigue libre en ese momento, una ruta posible es
`.specify/base/modulos/12-chatbot.md`, incorporada al índice de módulos. No añadir
ese ID al contexto como módulo existente antes de crear su contrato: el hook
comprueba el catálogo real. Mientras se diseña, el contexto cita los módulos
existentes afectados y describe el chatbot como el cambio propuesto.

Actualizar los contratos afectados si cambia su comportamiento y solo los
documentos transversales que lo requieran. Arquitectura y diseño pueden registrar
la integración final; Backlog y retro solo recogen alcance/acuerdos reales. No
editar el README principal ni crear carpetas raíz como efecto de este cierre.

En `validation.md`, conservar una tabla como esta, rellenada con ejecuciones
reales, no con resultados esperados:

```text
| Fecha y entorno | Comando/procedimiento | Resultado real | Criterios | Evidencia y límites |
| --- | --- | --- | --- | --- |
| Fecha de ejecución | Comando exacto usado | Pasó/falló/omitido, con cantidades reales | CA-XX | Archivo de prueba, procedimiento y causa de cualquier omisión |
```

Adjuntar evidencia visual propia sin datos personales cuando cambie la interfaz.
Un criterio obligatorio sin verificar impide declarar completa la DoD, aunque el
validador documental pase. No añadir un `validation.md` ficticio para desbloquear
el hook. Mantener pendientes reales hasta resolverlos o acordar un cambio de alcance.

## 13. Retomar en otra sesión

En el chat:

```text
$gym-spec-driven

Continúa NNN-chatbot-clientes. Lee su contexto, spec, plan, tareas y validación
antes de resolver los pendientes. Reutiliza la misma carpeta.
```

Para seleccionar una feature en una terminal con los mecanismos oficiales:

```bash
export SPECIFY_FEATURE_DIRECTORY="$PWD/.specify/specs/NNN-chatbot-clientes"
bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

La variable aplica a esa terminal. Las operaciones oficiales que persisten
selección actualizan feature.json; --paths-only solo consulta.

Antes de reanudar, comprobar de nuevo la rama con `git branch --show-current` y
el estado con `git status --short --branch`. La selección de feature no cambia
la rama. Si el check señala archivos o contexto incompletos, completar la etapa
correspondiente de esa carpeta; no generar otra spec para el mismo módulo.

Para dejar de seleccionar esa feature en la terminal:

```bash
unset SPECIFY_FEATURE_DIRECTORY
unset SPECIFY_FEATURE
```

Esto no borra los artefactos ni la selección persistida en `feature.json`.

## Si quieres que Codex recorra todo el flujo

Después de acordar las decisiones del paso 2, puedes sustituir el avance manual
por un solo pedido. Si ya creaste la carpeta, indica su nombre exacto:

```text
$gym-spec-driven

Quiero implementar el módulo de chatbot usando expresamente Spec Kit.
Usa el alcance y las decisiones que acabamos de acordar.
Continúa NNN-chatbot-clientes, sin crear otra feature ni cambiar de rama.

Consulta la base y el código actual; completa contexto y los siete componentes.
Recorre specify, clarify cuando haga falta, plan, tasks, analyze, implement y
converge. Aplica revisor y auditor en esta sesión. Ejecuta las pruebas pertinentes,
actualiza los contratos vivos y registra resultados reales en validation.md.
Resuelve decisiones rutinarias; pregunta por datos de producto que falten.
No publiques, cobres ni despliegues con esta petición.
```

Si todavía no existe la feature, cambia «Continúa…» por «Crea una sola feature
con el generador oficial» y no ejecutes antes el paso 3. Puedes interrumpir el
recorrido y retomar esa misma carpeta más adelante.

## Otras skills

`$speckit-constitution` se utiliza al solicitar un cambio de principios; la
constitución existente se consulta durante el trabajo habitual.
`$speckit-taskstoissues` está obsoleta y no forma parte del recorrido. Crear
issues, publicar PR, desplegar, enviar correos o cobrar requiere su propio alcance.
