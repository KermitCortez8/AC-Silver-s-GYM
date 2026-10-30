# Reglas comunes

- Trabajar en español desde el comportamiento comprobable del repositorio.
- Consultar [constitución](../../memory/constitution.md), [base existente](../../specs/000-base-implementada/spec.md),
  [módulos](../../base/modulos/README.md) y fuentes antes de diseñar o programar.
- Mantener las cuatro capas y reutilizar servicios, puertos, componentes y pruebas;
  ver [arquitectura](../../docs/arquitectura.md) y [diseño](../../docs/diseno.md).
- Cuando el usuario active Spec Kit, completar contexto, spec de siete componentes, plan
  y tareas en una sola feature. Seguir [Spec Driven](../../guias/spec-driven.md).
  Una consulta de viabilidad solo analiza; la implementación continúa hasta verificar.
- En correcciones acotadas, registrar síntoma, criterio de regresión y comprobación
  sin inventar una funcionalidad. Si código y docs difieren, explicar la evidencia.
- La base 000 no es trabajo pendiente. Auditorías y correcciones son control de
  errores, no alcance autorizado. Consultar [Backlog](../../docs/Backlog.md).
- Actualizar contratos vivos cuando cambie su comportamiento y registrar resultados
  reales de verificación, fallos y omisiones en `validation.md`.
- No modificar README principal salvo petición explícita. Los cinco documentos del equipo
  van en `.specify/docs/`; módulos, guías y control de errores tienen carpetas propias.
  Los recursos de Codex van en `.specify/.codex/` y las features en `.specify/specs/`;
  no recrear alias raíz.
- Conservar `.github/` y los enlaces de skills nativos. Continuar en la sesión
  actual sin confirmaciones rutinarias ni otros agentes automáticos.
- No publicar issues, PR, mensajes, cobros, correos o despliegues sin una petición
  que autorice esas acciones. Las preferencias locales complementan estas reglas.
