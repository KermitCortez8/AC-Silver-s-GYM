# Evidencia de la adopción documental

Registro histórico de la primera entrega documental. La configuración vigente
del CLI, skills y flujo se describe en el [índice central](../../README.md).

Fecha: 2026-10-29. Alcance: documentos, plantillas, instrucciones para Codex y
control documental. Referencia funcional: `fc1577e`.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `python .specify/scripts/validate_docs.py` | Correcto: enlaces locales, siete componentes y fila de evidencia por criterio en once módulos y la spec base. |
| Nombres `test_*` citados en los módulos, contrastados mediante AST con `backend/tests/` | Todos existen. No equivale a ejecutar esas pruebas. |
| Casos negativos del validador con contenido en memoria | Rechazó componente ausente/vacío, criterio duplicado, criterio sin evidencia y evidencia solo externa. |
| Enlaces de ejemplo y enlace roto en directorio temporal | Ignoró el ejemplo dentro de código y detectó el destino inexistente. |
| Sintaxis Python del validador y YAML del workflow | Correctas, usando `compile` y el parser YAML disponible. |
| `git diff --check` y revisión de espacios/saltos finales de archivos nuevos | Sin errores. |
| Revisión del alcance del diff | Solo se modifican README y `.gitignore` existentes y se añaden los archivos de esta adopción. Código e informes históricos intactos. |

La [tabla de criterios](spec.md) enlaza los documentos que satisfacen CA-01…CA-08.
La comprobación puede repetirse desde la raíz con el validador; el
[workflow](../../../.github/workflows/spec-docs.yml) la ejecutará en los PR configurados
una vez incorporado al repositorio remoto.

## Límites de esta verificación

No se ejecutaron las suites de aplicación, compilación frontend, integración
PostgreSQL, navegador, migraciones, cobros o correos reales: no se cambió
comportamiento del producto. La documentación indica pruebas disponibles y
dependencias de configuración; no certifica sus resultados de ejecución actuales.

No se instaló Specify CLI ni se generaron skills nativas en esta sesión. La base
se utiliza directamente con `AGENTS.md`; los pasos para añadir la integración
oficial están en [el flujo de trabajo](../../guias/spec-driven.md).
