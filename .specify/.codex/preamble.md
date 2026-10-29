# Contexto común de las etapas Spec Kit

Leer AGENTS.md raíz, el índice .specify/AGENTS.md, la constitución, la base 000,
los contratos afectados y sus fuentes/pruebas antes de diseñar o programar.
Consultar .specify/.codex/settings.json: reglas con always se leen siempre;
las demás se aplican según las rutas del cambio. Leer AGENTS.local.md si existe.
Una consulta informativa solo analiza. Una petición de implementación continúa
hasta verificar, sin confirmaciones rutinarias ni sesiones adicionales.

Respetar el modo actual de AGENTS.md: si el usuario no ha solicitado activar
Spec Kit, consultar la base y atender el pedido sin crear specs, planes o tareas
ni ejecutar estas etapas automáticamente.

## Un solo flujo

- Usar las etapas oficiales speckit-* y los scripts Bash instalados. Si una
  instrucción dice specify, usar .specify/.venv/bin/specify desde la raíz.
- Crear una feature una sola vez con create-new-feature.sh; el script prepara
  spec.md y context.md. Completar contexto con módulos, fuentes, reutilización,
  restricciones y pruebas. Los módulos se consultan en base/modulos/README.md.
- Mantener los siete componentes locales; no quitar restricciones técnicas por
  aplicar la checklist genérica upstream. Reutilizar una feature existente.
- setup-plan.sh ejecuta el hook de plan antes de escribir plan.md.
- check-prerequisites.sh --require-tasks ejecuta el mismo hook para implementación;
  las etapas analyze, implement y converge utilizan esos prerrequisitos.
- Durante speckit-analyze leer el perfil reviews.analyze de settings.json y
  aplicar su revisión sin modificar artefactos en esa etapa.
- Después de converger, leer reviews.close y revisar alcance, permisos y evidencia
  en la sesión actual. Completar validation.md y ejecutar:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage close
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

## Límites

La única ruta de features es .specify/specs/. No recrear docs/ ni specs/ en la raíz.
La constitución existente se preserva salvo cambio de principios solicitado.
No modificar README principal salvo petición explícita. No publicar issues, PR,
correos, cobros o despliegues sin petición que lo autorice. Los perfiles se leen
como instrucciones: no son agentes registrados ni conceden permisos del runtime.
No ejecutar workflows CLI que abran sesiones adicionales.
