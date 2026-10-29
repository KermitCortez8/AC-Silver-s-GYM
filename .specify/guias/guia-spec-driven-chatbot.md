# Guía práctica: del planteamiento al chatbot con Spec Kit

Aplicar esta guía cuando el usuario indique expresamente que quiere utilizar
Spec Kit. Mientras tanto, no generar specs, planes ni tareas para sus pedidos.

**Los comandos `$...` se escriben en el chat de Codex. Los comandos `python`,
`bash`, `docker` y `deno` se ejecutan en la terminal.** Esta guía usa las etapas
oficiales y el hook del proyecto; no hay un runner paralelo.

El chatbot es un ejemplo de alcance. Este documento no crea una feature ni
acredita que el chatbot esté implementado. Reemplaza `NNN-chatbot-clientes`
por el nombre real de la carpeta creada. Todo parte de la raíz:

```bash
cd /workspaces/AC-Silver-s-GYM
```

La [estructura](estructura-codex.md) conserva docs con los cinco documentos,
.codex con los componentes del asistente, contratos en base/modulos y features
en .specify/specs. No hay alias docs/specs en la raíz.

## 1. Comprobar el entorno — terminal

```bash
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

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
relaciones según el índice. Resolver público objetivo, datos permitidos,
acciones, proveedor y fallos. La documentación interna guía a Codex al programar;
las fuentes que el chatbot consultará en ejecución se definen explícitamente.

## 3. Crear una sola feature — terminal o mediante specify

Puedes dejar que `$speckit-specify` ejecute el generador o ejecutarlo una vez:

```bash
bash .specify/scripts/bash/create-new-feature.sh \
  --json --short-name chatbot-clientes \
  "Chatbot para consultar planes, horarios y la membresía del cliente autenticado"
```

El generador asigna el número, prepara spec.md y context.md y selecciona la
feature mediante feature.json local. No crea código de producto ni cambia rama.
No volver a ejecutarlo por cada etapa. Si ya existe una feature del cambio,
continuarla como se indica en el paso 13.

## 4. Completar contexto y especificación — chat

```text
$speckit-specify

Completa la feature existente NNN-chatbot-clientes.
No crees otra feature.

Lee las fuentes y pruebas de los contratos y completa context.md con
módulos, fuentes leídas, reglas, reutilización y comprobaciones elegidas.

Completa spec.md con los siete componentes:
Sprint Goal, User Story, Acceptance Criteria, Technical Constraints,
Guardrails, Edge Cases y Definition of Done.

Alcance inicial:
- Clientes autenticados.
- Consultas sobre planes y horarios.
- Consulta de la propia membresía.
- Sin ejecutar compras, pagos, matrículas ni modificaciones.

Conserva las cuatro capas, permisos y Docker de frontend y backend.
Señala decisiones pendientes, incluido el proveedor del modelo.
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

## 5. Resolver ambigüedades — chat

```text
$speckit-clarify

Revisa NNN-chatbot-clientes. Resuelve ambigüedades de comportamiento,
privacidad, proveedor, datos permitidos y fallos. Registra las respuestas.
```

Responder las preguntas que afecten al resultado. Si la spec ya es precisa,
no hace falta inventar aclaraciones. Opcionalmente:

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
```

El script oficial ejecuta el hook de plan antes de crear plan.md. Puedes
comprobar las mismas precondiciones directamente en terminal:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-chatbot-clientes --stage plan
```

## 7. Generar las tareas — chat

```text
$speckit-tasks

Genera las tareas de NNN-chatbot-clientes a partir de spec y plan.
Relaciona cada tarea con criterios y rutas concretas. Incluye implementación,
pruebas, Docker cuando corresponda, documentos y evidencia de cierre.
```

Resultado: tasks.md con secuencia y casillas de seguimiento. Cada criterio
necesita tareas y evidencia prevista.

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
```

## 10. Ejecutar las pruebas pertinentes — terminal

El plan determina las pruebas específicas del chatbot: autorización, aislamiento
por cliente, respuestas y fallos del proveedor con dobles de prueba. Los targets
Docker ejecutan las suites de backend y frontend siguiendo el enfoque de CI:

```bash
docker build --target test -t gym-backend-test ./backend

docker run --rm --network none \
  --env AUTH_SECRET_KEY=solo-pruebas-locales-no-produccion-0123456789 \
  gym-backend-test

docker build --target test -t gym-frontend-test ./frontend

docker run --rm --network none gym-frontend-test
```

La clave del ejemplo es de prueba; no se inyectan credenciales de producción.
Si corresponde comprobar arranque conjunto, preparar .env y backend/.env según
el [README](../../README.md) y ejecutar:

```bash
docker compose config --quiet
docker compose up --build --detach --wait
docker compose ps
docker compose logs --tail=100 backend frontend
```

La sonda normal comprueba Supabase. Un contenedor saludable no acredita que la
conversación funcione: revisar los criterios y la interfaz cuando corresponda.
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

## 12. Revisar, documentar y cerrar — chat y terminal

```text
Aplica el perfil de auditor indicado para close en settings.json en esta sesión.
Revisa los criterios y las reglas afectadas de NNN-chatbot-clientes.
Actualiza contratos y documentos, completa validation.md con resultados,
fallos, omisiones y evidencia, y comprueba la Definition of Done.
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

## Otras skills

`$speckit-constitution` se utiliza al solicitar un cambio de principios; la
constitución existente se consulta durante el trabajo habitual.
`$speckit-taskstoissues` está obsoleta y no forma parte del recorrido. Crear
issues, publicar PR, desplegar, enviar correos o cobrar requiere su propio alcance.
