# Hook único de validación

[validate.py](validate.py) contiene la implementación de validación documental,
configuración, estructura y trazabilidad por feature. Lee los artefactos de cada
etapa declarados en [settings.json](../settings.json), sin comandos arbitrarios.

```bash
python .specify/.codex/hooks/validate.py
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage plan
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage implement
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage close
```

El script oficial setup-plan ejecuta plan antes de escribir plan.md.
check-prerequisites --require-tasks ejecuta implement antes de devolver los
artefactos. Sus mensajes van a stderr para conservar el JSON oficial. El cierre
se ejecuta directamente después de la revisión y registro de resultados.

No hay un hook intermediario ni runner adicional. Son hooks del flujo Spec Kit,
no interceptores de cada edición ni eventos nativos del runtime de Codex.
El resultado valida documentos y trazabilidad, no sustituye las suites del producto.

En Windows con `core.symlinks=false`, Git guarda los enlaces de `.agents/skills`
como archivos de texto. El validador acepta únicamente la ruta relativa exacta
de cada skill y exige que su `SKILL.md` exista en `.specify/.codex/skills`.
No acepta directorios copiados ni destinos alternativos. En Linux se siguen
exigiendo enlaces simbólicos reales. Esta compatibilidad valida el checkout;
no convierte los archivos de texto en skills descubribles por Codex. Para ese
descubrimiento se necesitan enlaces reales y permisos de Windows que permitan
crearlos. Los archivos Git de los enlaces no se modifican.
