# Perfiles de revisión dentro del flujo

[settings.json](../settings.json) asigna dos revisiones:

| Etapa | Perfil | Resultado |
| --- | --- | --- |
| speckit-analyze | [Revisor](revisor.md) | Contrastar spec, plan y tareas con arquitectura, reglas y pruebas. |
| Antes de cierre | [Auditor](auditor.md) | Revisar alcance, permisos, privacidad, atomicidad y evidencia afectados. |

Las skills leen un preámbulo que requiere aplicar esos perfiles en la sesión
actual. Son instrucciones de revisión, no subagentes registrados automáticamente.
Los hallazgos no autorizan funciones nuevas ni publicación de mensajes.

También pueden invocarse expresamente:

```text
Lee .specify/.codex/agents/revisor.md y revisa la feature actual en esta sesión.
```
