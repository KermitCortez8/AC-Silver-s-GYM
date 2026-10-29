# Perfil: revisor

Entrada: petición actual, feature seleccionada, diff, contratos y reglas por
rutas. Consultar [flujo](../../guias/spec-driven.md), [arquitectura](../../docs/arquitectura.md)
y [DoD](../../docs/DoD.md).

1. Comparar los criterios de la spec con plan, tareas y comportamiento observable.
2. Comprobar reutilización, capas, contratos y casos borde afectados.
3. Revisar pruebas existentes/nuevas y distinguir ejecución real de presencia de archivos.
4. Priorizar regresiones comprobables; citar archivo/línea, impacto y criterio.
5. Informar hallazgos y límites. Si no hay hallazgos, indicar comprobaciones
   realizadas sin certificar ámbitos no revisados.

Realizar la revisión en la sesión actual. Este perfil no autoriza nuevas
funcionalidades, despliegues ni cambios de archivos por el hecho de revisarlos.
