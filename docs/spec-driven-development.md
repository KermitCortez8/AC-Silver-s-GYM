# Desarrollo guiado por especificaciones con GitHub Spec Kit

Estado: integración instalada el 27 de octubre de 2026.
Versión: **Spec Kit 1.2.3**, fijada al commit oficial en
[tools/spec-kit-requirements.txt](../tools/spec-kit-requirements.txt).

## Los cuatro puntos implementados

| Punto | Definición en el repositorio |
| --- | --- |
| 1. Principios del proyecto | [Constitución](../.specify/memory/constitution.md): cuatro capas, contratos, tratamiento de errores, evidencia y adopción incremental. |
| 2. Especificación piloto | [Control de errores](../specs/001-control-errores/spec.md): cuatro historias, nueve requisitos, escenarios, límites y criterios de éxito. |
| 3. Plan y tareas | [Plan](../specs/001-control-errores/plan.md) y [tareas](../specs/001-control-errores/tasks.md): responsabilidades por capa, dependencias y vínculos con pruebas existentes. |
| 4. Implementación y verificación | [Guía ejecutable](../specs/001-control-errores/quickstart.md), [registro de evidencia](../specs/001-control-errores/verification.md), skills oficiales y comprobación estructural en CI. |

La integración SDD está instalada. La aceptación funcional del piloto permanece
abierta: una tarea marcada como pendiente no se declara implementada por haber
documentado su requisito. El trabajo local de la aplicación se conserva.

## Qué se instaló

- `.specify/`: scripts Bash, plantillas, metadatos de integración y workflow
  oficiales de Spec Kit.
- `.agents/skills/speckit-*/SKILL.md`: diez skills oficiales para Codex.
- `.specify/memory/constitution.md`: principios particulares del gimnasio.
- `AGENTS.md`: instrucciones para continuar el proceso en sesiones futuras.
- `.tools/spec-kit/`: CLI aislada, ignorada por Git.
- `scripts/setup-spec-kit.sh` y `scripts/specify`: instalación y acceso locales.

Las plantillas oficiales se mantienen sin cambios internos. La personalización
del proyecto vive en la constitución, esta guía y `specs/`. No se añaden
dependencias SDD a FastAPI, Vue ni sus imágenes de producción.

## Usar la herramienta en este checkout

Desde la raíz:

```bash
bash scripts/specify version
```

Para otro checkout con Python 3.11+, venv/pip y Git disponibles:

```bash
bash scripts/setup-spec-kit.sh
bash scripts/specify version
```

La descarga usa el commit oficial fijado. El script no configura el PATH ni
reinicializa los documentos. Los archivos generados ya forman parte del
repositorio; no hace falta repetir `specify init`.

## Trabajar sobre el piloto actual

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/001-control-errores
bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

El script comprueba que existen los documentos necesarios. No ejecuta pruebas de
la aplicación ni certifica el cumplimiento de sus reglas. La selección del
piloto queda como estado local ignorado en `.specify/feature.json`; no cambia la
rama Git.

En el chat del agente configurado, usar las skills instaladas:

```text
$speckit-analyze
$speckit-implement
$speckit-converge
```

El modo instalado usa nombres con guion y prefijo `$`. Los ejemplos anteriores
con `/speckit.plan` corresponden a otra forma de integración. Estas invocaciones
son instrucciones del chat, no comandos de Bash. También se puede indicar la
ruta del `SKILL.md` al agente cuando el cliente no exponga el selector.

Para continuar, leer primero las tareas abiertas. La semántica de cancelación
está decidida en ERR-009; su corrección y regresiones se planifican en T013/T014.
No repetir las tareas completadas ni declarar convergencia con brechas pendientes.

## Desarrollar el siguiente cambio

1. **Especificar:** describir resultado, actores, alcance, errores y efectos sobre
   los datos con `$speckit-specify`. Empezar por una necesidad concreta.
2. **Aclarar:** resolver ambigüedades relevantes con `$speckit-clarify` cuando haga
   falta; no bloquear trabajo independiente por una decisión ajena.
3. **Planificar:** usar `$speckit-plan`, reutilizar capas y contratos, y revisar la
   sección de cumplimiento de la constitución.
4. **Dividir y analizar:** `$speckit-tasks` y `$speckit-analyze`, con tareas por
   historia y evidencia por criterio.
5. **Implementar y verificar:** `$speckit-implement`, pruebas pertinentes y
   `$speckit-converge`; reconciliar los documentos si cambia el alcance.

`$speckit-constitution` sirve para mantener los principios; no es necesario
recrearlos en cada cambio. La extensión Git no se instaló: las ramas y commits
se manejan con el flujo habitual del proyecto.

Los nuevos artefactos siguen las plantillas de `.specify/templates/`:

```text
specs/NNN-cambio/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/
  quickstart.md
  tasks.md
  verification.md
```

Los archivos auxiliares deben aportar información aplicable al cambio; no hay
que inventar tablas, dependencias o contratos solo para rellenar una plantilla.
Una corrección añade el escenario faltante; una refactorización demuestra
equivalencia frente a criterios existentes. Documentación y formato no necesitan
una nueva especificación funcional.

## Evidencia y definición de terminado

Reutilizar pytest, node:test, compilación y CI. Para comportamiento nuevo o una
regresión, comprobar el fallo esperado antes de implementar. Para comportamiento
existente, enlazar y ejecutar la prueba adecuada sin duplicarla.

| Regla | Evidencia apropiada |
| --- | --- |
| Negocio | Datos válidos, límites y rechazo en pruebas de dominio. |
| Coordinación y estado | Confirmación, fallo y conservación en aplicación. |
| HTTP y permisos | Rutas con estados, cuerpos y autenticación real cuando corresponda. |
| Formularios | Flujo de presentación; revisión visual/accesible cuando aplique. |
| Atomicidad y concurrencia | PostgreSQL aislado; memoria no demuestra comportamiento SQL. |
| Dependencias | Pruebas existentes de límites de arquitectura. |

Un cambio termina cuando los criterios afectados tienen evidencia, las pruebas
pertinentes pasan, los contratos/migraciones están actualizados y no quedan
decisiones necesarias sobre el comportamiento entregado. Registrar revisión
evaluada, comandos, resultados y omisiones. Mantener las specs como contratos
vivos y actualizar plan, tareas y evidencia cuando cambie una regla.

CI conserva sus trabajos funcionales y añade una comprobación de presencia de
artefactos del piloto con el script oficial. Esta comprobación no evalúa la
semántica de Markdown ni reemplaza la revisión de criterios.

## Actualizar Spec Kit

Elegir una release oficial, fijar su commit y probar la actualización en una
carpeta temporal. Revisar el diff generado antes de sustituir plantillas o
skills. Preservar la constitución y todas las especificaciones; verificar versión,
prerrequisitos y evidencia después de la actualización.

Referencias: [instalación oficial](https://github.com/github/spec-kit/blob/v1.2.3/docs/installation.md)
y [guía para proyectos existentes](https://github.com/github/spec-kit/blob/v1.2.3/docs/guides/existing-projects.md).
