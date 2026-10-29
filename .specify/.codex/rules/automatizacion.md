# Spec Kit, Docker y CI

Consultar [estructura](../../guias/estructura-codex.md), [flujo](../../guias/spec-driven.md)
y [procedencia](../../UPSTREAM.md).

- Usar las etapas y scripts de Spec Kit instalados. Mantener la ruta real de
  specs, overrides y hashes registrados. No recrear docs/specs en la raíz.
- Conservar enlaces nativos .agents/skills a .specify/.codex/skills y .github separado.
- Settings declara reglas, artefactos de hooks y perfiles de revisión. Lo consume
  el hook y lo leen las skills; no concede permisos del runtime ni ejecuta shell arbitrario.
- El hook tiene una sola implementación. Setup-plan y los prerrequisitos oficiales
  lo ejecutan antes de continuar; CI llama al hook global y unittest directamente.
- Revisor se utiliza en analyze y auditor antes de close en esta sesión, sin
  delegación automática ni cambios de modelo o permisos.
- Frontend y backend mantienen Dockerfiles, targets test, usuarios sin root,
  red compartida, proxy y sondas documentados en arquitectura.
- Las imágenes de pruebas y los runtimes publicados Vercel/Render tienen
  configuraciones distintas. Conservar los contratos de despliegue.
- Ante cambios de scripts, ejecutar pruebas aisladas y documentar resultados.
