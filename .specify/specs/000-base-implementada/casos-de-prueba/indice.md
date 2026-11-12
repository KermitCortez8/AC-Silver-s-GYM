# Casos de prueba organizados por módulo

Fecha de organización: **2026-11-10**. Se conservan los resultados y datos de la
revisión documentada en [validation.md](../validation.md). Cada módulo tiene
su carpeta con documentos separados para casos individuales, escenarios de
uso y catálogo estructurado; dentro de los documentos se ordenan por tipo.

| Componente | Casos individuales | Aprobados registrados | Omitidos registrados |
| --- | ---: | ---: | ---: |
| Backend | 805 | 751 | 54 |
| Frontend | 372 | 372 | 0 |
| **Total** | **1.177** | **1.123** | **54** |

Los 89 escenarios de uso agrupados se distribuyen entre las mismas carpetas.
Sus IDs `CP-*` y los 1.177 IDs individuales `CT-*` se mantienen. Esta separación
no implica una ejecución nueva de las suites ni cambia sus omisiones.

El [plan de pruebas general](plan-de-pruebas.md) organiza las funcionalidades,
los tipos de prueba, los entornos, los hitos de ejecución y el cierre. Cada
módulo tiene además su propio plan enlazado desde sus documentos de casos.

## Módulos

| Módulo | Casos individuales | Escenarios agrupados | Casos de prueba | Casos de uso | Catálogo JSON |
| --- | ---: | ---: | --- | --- | --- |
| MOD-01 · Identidad y acceso | 29 | 6 | [Casos individuales](01-identidad-acceso/casos-de-prueba.md) | [Escenarios](01-identidad-acceso/casos-de-uso.md) | [JSON](01-identidad-acceso/catalogo-pruebas.json) |
| MOD-02 · Clientes | 102 | 9 | [Casos individuales](02-clientes/casos-de-prueba.md) | [Escenarios](02-clientes/casos-de-uso.md) | [JSON](02-clientes/catalogo-pruebas.json) |
| MOD-03 · Membresías y pagos | 108 | 9 | [Casos individuales](03-membresias-pagos/casos-de-prueba.md) | [Escenarios](03-membresias-pagos/casos-de-uso.md) | [JSON](03-membresias-pagos/catalogo-pruebas.json) |
| MOD-04 · Planes y promociones | 13 | 6 | [Casos individuales](04-planes-promociones/casos-de-prueba.md) | [Escenarios](04-planes-promociones/casos-de-uso.md) | [JSON](04-planes-promociones/catalogo-pruebas.json) |
| MOD-05 · Horarios y matrículas | 38 | 8 | [Casos individuales](05-horarios-matriculas/casos-de-prueba.md) | [Escenarios](05-horarios-matriculas/casos-de-uso.md) | [JSON](05-horarios-matriculas/catalogo-pruebas.json) |
| MOD-06 · Asistencias | 118 | 15 | [Casos individuales](06-asistencias/casos-de-prueba.md) | [Escenarios](06-asistencias/casos-de-uso.md) | [JSON](06-asistencias/catalogo-pruebas.json) |
| MOD-07 · Rutinas y progreso | 15 | 5 | [Casos individuales](07-rutinas-progreso/casos-de-prueba.md) | [Escenarios](07-rutinas-progreso/casos-de-uso.md) | [JSON](07-rutinas-progreso/catalogo-pruebas.json) |
| MOD-08 · Inventario y movimientos | 90 | 7 | [Casos individuales](08-inventario/casos-de-prueba.md) | [Escenarios](08-inventario/casos-de-uso.md) | [JSON](08-inventario/catalogo-pruebas.json) |
| MOD-09 · Tienda y pedidos | 15 | 8 | [Casos individuales](09-tienda-pedidos/casos-de-prueba.md) | [Escenarios](09-tienda-pedidos/casos-de-uso.md) | [JSON](09-tienda-pedidos/catalogo-pruebas.json) |
| MOD-10 · Paneles y configuración | 41 | 6 | [Casos individuales](10-paneles-configuracion/casos-de-prueba.md) | [Escenarios](10-paneles-configuracion/casos-de-uso.md) | [JSON](10-paneles-configuracion/catalogo-pruebas.json) |
| MOD-11 · Notificaciones | 21 | 6 | [Casos individuales](11-notificaciones/casos-de-prueba.md) | [Escenarios](11-notificaciones/casos-de-uso.md) | [JSON](11-notificaciones/catalogo-pruebas.json) |
| Controles transversales | 587 | 4 | [Casos individuales](transversales/casos-de-prueba.md) | [Escenarios](transversales/casos-de-uso.md) | [JSON](transversales/catalogo-pruebas.json) |

## Cómo leer y repetir cada caso

- **Dado:** preparar las dependencias del componente, los fixtures/dobles del
  archivo enlazado y los parámetros de la variante. En backend los nombres de
  fixtures y parámetros están en la fila; sus valores/configuración están en
  la prueba y sus decoradores. Los datos siguen siendo sintéticos.
- **Cuando:** ejecutar el selector exacto guardado en el JSON de cada módulo desde `backend/`
  o `frontend/`, según `component`. El campo `command` reproduce solo ese caso.
  Backend requiere una `AUTH_SECRET_KEY` sintética válida. SQL requiere además
  un contenedor desechable explícito y pg_cron para sus variantes de cron.
- **Entonces:** deben cumplirse todas las aserciones/excepciones esperadas del
  código. La fila muestra hasta tres extractos literales para identificar el
  resultado; el número entre paréntesis cuenta comprobaciones estáticas en la
  fuente, no iteraciones ni cobertura. Los auxiliares pueden comprobar más.
- **Resultado registrado:** Aprobado u Omitido en la ejecución indicada; una
  omisión no aprueba el comportamiento. La semántica completa está en la fuente,
  que prevalece sobre un extracto abreviado.

Cada `CT-*` corresponde a un resultado individual del runner: no se agrupan
variantes. Un mismo flujo puede aparecer en backend/frontend o con distintos
roles, límites y fallos. Las once pruebas frontend con aserciones de nivel de
archivo cuentan como once unidades del runner, aunque contienen varias aserciones.
Los títulos técnicos originales se conservan para localizarlos sin ambigüedad.
`transversales` agrupa controles que sirven a varios módulos; no es una nueva
funcionalidad. El orden es módulo, tipo, componente y archivo.

## Preparación y registro de los escenarios agrupados

**Preparación común:** usar C1/C2 como clientes ficticios independientes,
sesiones por rol y repositorios/proveedores inyectados. `D` es el día de negocio
controlado en `America/Lima`; `F` es el último día de vigencia de una membresía.
Cada fila parte de un estado limpio; las variantes temporales usan visitas o
compras independientes. Los escenarios SQL se preparan exclusivamente en un
PostgreSQL desechable, y pg_cron se requiere solo para sus variantes de cron.
Los datos numéricos son ejemplos de prueba, no nuevas reglas de producto.

**Estado de los escenarios agrupados:** pendientes de ejecutar como batería de
aceptación consolidada. El catálogo individual sí registra las ejecuciones de
las suites descritas arriba; no equivale a una UAT de todos estos recorridos.
Una referencia indica prueba o código existente y no una nueva aprobación del recorrido.
Las ejecuciones históricas se consultan en su validación original; los casos
que solo enlazan código necesitan todavía automatización o un procedimiento
manual ejecutado. En particular, el cierre general SQL depende de resolver la
migración 023 vacía. No se ejecutan cobros, correos ni mutaciones remotas reales.

Cada fila contiene actor/datos previos, acción reproducible, resultado binario,
tipo de prueba y trazabilidad `MOD-nn/CA-nn`. Los casos transversales conservan
su alcance común. El orden dentro de cada módulo es unitaria, integración, PostgreSQL e interfaz;
el bloque documental cierra los controles compartidos.

## Registro y criterio de aceptación de la batería

La síntesis contiene **89 escenarios agrupados**: 85 distribuidos entre los once
módulos y cuatro transversales. La enumeración de las 1.177 pruebas individuales
está distribuida en los documentos enlazados en la tabla de módulos. Cada
criterio CA vigente tiene al menos un caso; esto es trazabilidad documental,
no una métrica de cobertura ejecutada.
El prototipo de chatbot queda fuera de la base implementada: sus pruebas de
navegación y escenarios productivos pendientes figuran en el inventario.

Al ejecutar cada caso, registrar en `validation.md` o en un informe enlazado:

| Campo | Contenido requerido |
| --- | --- |
| Caso y criterio | ID CP, MOD/CA y variante concreta. |
| Entorno | Commit, fecha/hora Lima, datos sintéticos, reloj, dependencias y tipo de proveedor/base. |
| Ejecución | Comando o secuencia de pantalla/API realizada. |
| Resultado | Aprobado, fallido, omitido o bloqueado, con resultado observado y causa. |
| Evidencia | Salida del runner, consulta aislada, JSON o captura según el mecanismo. |
| Limpieza | Retirada de datos sintéticos/contenedor si corresponde. |

Una fila pasa solo si se cumplen sus resultados y no quedan efectos parciales.
En los casos que reúnen varios mecanismos/variantes, registrar cada resultado
por separado: por ejemplo, SSR no aprueba navegador, ni un doble aprueba SQL.
Faltas de entorno/migración/proveedor se registran como omisión o bloqueo; no
como aprobación. No repetir automáticamente escrituras con resultado incierto.
No sumar resultados de ejecuciones históricas diferentes como una sola suite.
La revisión visual propia y los controles de compilación siguen el
[DoD](../../../docs/DoD.md).

## Catálogo estructurado por módulo

[catalogo.json](catalogo.json) contiene los totales y las rutas de los doce
catálogos de módulo. Los casos individuales están en esos archivos; el índice
no vuelve a reunirlos en un único array. Las rutas `path` de cada caso siguen
siendo relativas a la raíz del repositorio y los comandos se ejecutan desde
su componente, igual que antes de esta organización.
