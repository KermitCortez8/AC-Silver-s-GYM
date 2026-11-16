# Casos documentados y automatización de Testiny

Catálogo consultado el **2026-11-15** mediante Chromium/Playwright en una sesión
independiente de Edge: **199 casos** del proyecto `SILVE`. No se modificaron los
casos ni los runs manuales durante esta revisión.

La ejecución local verificó **100/199 casos (50,25 %)**: 100 aprobados, ninguno
fallido y ninguno omitido entre los seleccionados. Los otros 99 permanecen en el
denominador. Se conservan los módulos y los RF/CUS del catálogo; compartir un RF
no acredita otro caso.

| Archivo | Contenido |
| --- | --- |
| [catalogo.json](catalogo.json) | Snapshot de títulos, precondiciones, pasos, resultados, módulos, tipos, RF/CUS e IDs de Testiny; sin datos de propietarios o auditoría. |
| [automatizacion.json](automatizacion.json) | Revisión de cada resultado esperado, pruebas concretas obligatorias y huellas de sus aserciones y soporte. |
| [revision.md](revision.md) | Matriz legible de los 100 casos y diferencias pendientes. |
| [trazabilidad.csv](trazabilidad.csv) | Los 199 casos con RF, CUS, tipo, alcance revisado y selectores de prueba; abrir como UTF-8 en Excel. |
| [resultado-local.json](resultado-local.json) | Recuentos de la ejecución local, tipos y 316 resultados esperados revisados de los 100 casos. |
| [Evidencia de ejecución](../validaciones/testiny-ci/validation.md) | Comandos, resultados y límites de la verificación. |

## Alcance comprobado

Los casos funcionales se automatizan por contratos HTTP, servicios y componentes
Vue reales. Se comprueban resultados de negocio, relecturas, validaciones,
permisos y ausencia de escrituras parciales. Las pruebas unitarias ejercitan
funciones/contratos aislados. Se usan repositorios QA, perfiles de sesión
resueltos, gateways, colas y transporte de proveedores dobles declarados.

Esta evidencia no ejecuta todos los clics de los recorridos manuales ni certifica
E2E en navegador, Supabase productivo, Stripe, Google, Resend, accesibilidad o
compatibilidad entre navegadores. Las pruebas de concurrencia en memoria no
demuestran concurrencia SQL entre servidores. Los tiempos de adaptadores con
proveedor doble son descriptivos y no acreditan un SLA remoto.

## Cómo se calcula

Cada caso requiere todos sus pasos revisados y todos sus selectores presentes,
incluidas todas las variantes parametrizadas. Una omisión o una prueba ausente
impide contar el caso como ejecutado completo. Cada caso se cuenta una sola vez,
aunque tenga varias pruebas o comparta una prueba con otro caso.

Un fallo conserva el resultado fallido y cuenta como ejecución, nunca como
aprobación. Las pruebas del integrador no acreditan casos del producto.
El mínimo es `ceil(total / 2)`: con 199 se necesitan 100. CI exige ese mínimo
antes de publicar cualquier fuente en Testiny. Si falta evidencia, falla el
publicador y conserva el diagnóstico en artefactos. Este control pertenece al
publicador posterior a las suites; no añade una dependencia al despliegue.

La fuente `gym-casos-documentados` contiene un resultado por caso revisado, con
clave estable `SILVE-TC-<id>` y campos `rf`, `cus`, `testiny_case_id`,
`tipo_documentado` y `manual_case_url`. Es evidencia derivada de pruebas reales;
no escribe resultados en runs manuales. Las fuentes técnicas siguen mostrando
cada prueba individual. Sus duraciones pueden compartir pruebas y no representan
el tiempo de un recorrido manual completo.

## Mantener la revisión

1. Ante cambios en Testiny, consultar de nuevo el catálogo con Chromium/Playwright
   aislado y actualizar el snapshot completo, sin reducir el denominador.
2. Revisar precondiciones y cada resultado esperado contra código y aserciones.
   Completar pruebas faltantes; mantener fuera los casos parcialmente cubiertos.
3. Actualizar la correspondencia y las huellas SHA-256 de los archivos revisados
   normalizando CRLF a LF. No actualizar huellas para eludir una revisión.
4. Ejecutar las suites y preparar los informes con `--documented`, según la
   [guía de CI](../../guias/testiny-ci.md). Comprobar CSV/JSON y el mínimo.

El catálogo es una versión revisada, no una consulta dinámica en cada pipeline.
Las huellas impiden reutilizar una revisión sobre aserciones distintas: también
se contrastan con las que produjo el checkout de origen, incluido el merge
provisional de un PR. Un artefacto anterior sin estas huellas no acredita esta
revisión: ejecutar nuevamente todas las suites después de incorporar los cambios.
