# Casos documentados y automatización de Testiny

Catálogo sincronizado el **2026-11-19** con la exportación de todos los
**222 casos** del proyecto `SILVE`. Los 23 casos nuevos corresponden a los
IDs 200 a 222. Se acreditaron 22 y queda pendiente el TC-215 de PostgreSQL.

La ejecución local verificó **179 de 222 casos (80,63 %)**, todos aprobados.
Incluye el TC-195 con Stripe sandbox. La ejecución habitual sin Stripe sandbox
acredita 178 de 222 (80,18 %). Quedan 43 casos pendientes de cobertura completa.

| Archivo | Contenido |
| --- | --- |
| [catalogo.json](catalogo.json) | Snapshot de títulos, precondiciones, pasos, resultados, módulos, tipos, RF/CUS e IDs de Testiny; sin datos de propietarios o auditoría. |
| [automatizacion.json](automatizacion.json) | Revisión de cada resultado esperado, pruebas concretas obligatorias y huellas de sus aserciones y soporte. |
| [revision.md](revision.md) | Matriz histórica, notas de sincronización y ampliación de la cobertura. |
| [trazabilidad.csv](trazabilidad.csv) | Los 222 casos con RF, CUS, tipo, alcance revisado y selectores de prueba; abrir como UTF-8 en Excel. |
| [resultado-local.json](resultado-local.json) | Resultado local con los recuentos de cobertura y de ambas suites. |
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
El mínimo es el 80 % redondeado hacia arriba. Con 222 se necesitan 178. CI exige ese mínimo
antes de publicar cualquier fuente en Testiny. Si falta evidencia, falla el
publicador y conserva el diagnóstico en artefactos. Este control pertenece al
publicador posterior a las suites; no añade una dependencia al despliegue.

La fuente `gym-casos-documentados` contiene un resultado por caso del catálogo,
con estado omitido para los casos sin evidencia completa. Cada entrada conserva
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
