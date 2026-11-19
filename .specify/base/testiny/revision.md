# Revisión de casos documentados

Fecha: 2026-11-15. Catálogo actual: **199**. Mínimo: **100**.

Resultado local: **100 aprobados / 199 (50,25 %)**, sin fallos ni omisiones entre los seleccionados. Se verificaron los oráculos antes de activar `--documented` en el publicador.

La [revisión técnica](automatizacion.json) contiene la evidencia exigida para cada paso. El [CSV completo](trazabilidad.csv) incluye también los 99 pendientes. La modalidad es API/servicios/componentes con dobles declarados, según el [alcance](README.md#alcance-comprobado).

## Hallazgos y exclusiones

- **TC-43:** regresión ejecutada: un plan inactivo permitía crear membresía por `/api/membresias`. Se añadió la validación en dominio; las variantes inexistente/inactivo rechazan sin cambios y el plan activo permite reintentar. La suite completa posterior pasó.
- **TC-101:** el mensaje exacto documentado no coincide cuando el producto tiene estado Agotado. No se cambió el resultado esperado para fabricar un PASS.
- **TC-104:** falta especificar método de pago en la variante API; el método por defecto exige pasarela. No se acredita el caso completo con la mera validación aislada de carrito vacío.
- **TC-51–53:** referencia heredada de capacidad hacia RF12/CUS12 pendiente de revisar frente al CUS de horarios del cliente.
- **TC-194:** redirección documentada al panel de rol distinta de `/` en `sessionGuard`; no se acredita la variante completa.
- **TC-102, 119 y 174:** existen pruebas parciales, pero faltan resultados concretos indicados en el CSV. Quedan fuera del porcentaje.
- Casos de proveedores externos, aceptación humana, compatibilidad entre navegadores, accesibilidad y SQL real conservan sus necesidades de entorno; no se sustituyen por un doble para declarar una certificación externa.

Los hallazgos no cambian los casos/runs manuales en Testiny. Los demás casos pendientes no se declaran incorrectos por carecer de esta automatización.

## Casos con revisión y ejecución completa

| TC | RF | CUS | Tipo documentado | Módulo | Resultado |
| --- | --- | --- | --- | --- | --- |
| [TC-10](https://app.testiny.io/SILVE/testcases/tc/10/edit) | RF02 | CUS02 | Funcional | MOD-01 | Aprobado |
| [TC-11](https://app.testiny.io/SILVE/testcases/tc/11/edit) | RF02 | CUS02 | Seguridad | MOD-01 | Aprobado |
| [TC-42](https://app.testiny.io/SILVE/testcases/tc/42/edit) | RF09 | CUS07 (nueva membresía/renovación); CUS03 y CUS06 relacionados | Funcional | MOD-03 | Aprobado |
| [TC-43](https://app.testiny.io/SILVE/testcases/tc/43/edit) | RF09 | CUS07 (nueva membresía/renovación); CUS03 y CUS06 relacionados | Funcional | MOD-03 | Aprobado |
| [TC-44](https://app.testiny.io/SILVE/testcases/tc/44/edit) | RF09 | CUS07 (nueva membresía/renovación); CUS03 y CUS06 relacionados | Funcional | MOD-03 | Aprobado |
| [TC-49](https://app.testiny.io/SILVE/testcases/tc/49/edit) | RF11 | CUS10 | Funcional | MOD-11 | Aprobado |
| [TC-50](https://app.testiny.io/SILVE/testcases/tc/50/edit) | RF11 | CUS10 | Funcional | MOD-11 | Aprobado |
| [TC-76](https://app.testiny.io/SILVE/testcases/tc/76/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Funcional | MOD-10 | Aprobado |
| [TC-77](https://app.testiny.io/SILVE/testcases/tc/77/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Funcional | MOD-10 | Aprobado |
| [TC-79](https://app.testiny.io/SILVE/testcases/tc/79/edit) | RF18 | CUS26/CUS27 relacionados por alcance; RF heredado sin equivalencia única | Funcional | MOD-07 | Aprobado |
| [TC-80](https://app.testiny.io/SILVE/testcases/tc/80/edit) | RF18 | CUS26/CUS27 relacionados por alcance; RF heredado sin equivalencia única | Funcional | MOD-07 | Aprobado |
| [TC-81](https://app.testiny.io/SILVE/testcases/tc/81/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-82](https://app.testiny.io/SILVE/testcases/tc/82/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-83](https://app.testiny.io/SILVE/testcases/tc/83/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-84](https://app.testiny.io/SILVE/testcases/tc/84/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-85](https://app.testiny.io/SILVE/testcases/tc/85/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-86](https://app.testiny.io/SILVE/testcases/tc/86/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-87](https://app.testiny.io/SILVE/testcases/tc/87/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-88](https://app.testiny.io/SILVE/testcases/tc/88/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-89](https://app.testiny.io/SILVE/testcases/tc/89/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-90](https://app.testiny.io/SILVE/testcases/tc/90/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-91](https://app.testiny.io/SILVE/testcases/tc/91/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-92](https://app.testiny.io/SILVE/testcases/tc/92/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-93](https://app.testiny.io/SILVE/testcases/tc/93/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-94](https://app.testiny.io/SILVE/testcases/tc/94/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-95](https://app.testiny.io/SILVE/testcases/tc/95/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-96](https://app.testiny.io/SILVE/testcases/tc/96/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-97](https://app.testiny.io/SILVE/testcases/tc/97/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-98](https://app.testiny.io/SILVE/testcases/tc/98/edit) | RF21 | CUS21 | Funcional | MOD-09 | Aprobado |
| [TC-99](https://app.testiny.io/SILVE/testcases/tc/99/edit) | RF22 | CUS22 | Funcional | MOD-09 | Aprobado |
| [TC-100](https://app.testiny.io/SILVE/testcases/tc/100/edit) | RF22 | CUS22 | Funcional | MOD-09 | Aprobado |
| [TC-103](https://app.testiny.io/SILVE/testcases/tc/103/edit) | RF23 | CUS23 | Funcional | MOD-09 | Aprobado |
| [TC-105](https://app.testiny.io/SILVE/testcases/tc/105/edit) | RF23 | CUS23 | Funcional | MOD-09 | Aprobado |
| [TC-106](https://app.testiny.io/SILVE/testcases/tc/106/edit) | RF24 | CUS31 (amplía CUS24; el documento está en carpeta CUS30) | Funcional | MOD-09 | Aprobado |
| [TC-107](https://app.testiny.io/SILVE/testcases/tc/107/edit) | RF24 | CUS31 (amplía CUS24; el documento está en carpeta CUS30) | Funcional | MOD-09 | Aprobado |
| [TC-108](https://app.testiny.io/SILVE/testcases/tc/108/edit) | RF24 | CUS31 (amplía CUS24; el documento está en carpeta CUS30) | Funcional | MOD-09 | Aprobado |
| [TC-109](https://app.testiny.io/SILVE/testcases/tc/109/edit) | RF25 | CUS25 | Funcional | MOD-07 | Aprobado |
| [TC-110](https://app.testiny.io/SILVE/testcases/tc/110/edit) | RF25 | CUS25 | Funcional | MOD-07 | Aprobado |
| [TC-111](https://app.testiny.io/SILVE/testcases/tc/111/edit) | RF25 | CUS25 | Funcional | MOD-07 | Aprobado |
| [TC-112](https://app.testiny.io/SILVE/testcases/tc/112/edit) | RF26 | CUS26 | Funcional | MOD-07 | Aprobado |
| [TC-113](https://app.testiny.io/SILVE/testcases/tc/113/edit) | RF26 | CUS26 | Funcional | MOD-07 | Aprobado |
| [TC-114](https://app.testiny.io/SILVE/testcases/tc/114/edit) | RF26 | CUS26 | Funcional | MOD-07 | Aprobado |
| [TC-115](https://app.testiny.io/SILVE/testcases/tc/115/edit) | RF26 | CUS26 | Funcional | MOD-07 | Aprobado |
| [TC-116](https://app.testiny.io/SILVE/testcases/tc/116/edit) | RF26 | CUS26 | Funcional | MOD-07 | Aprobado |
| [TC-117](https://app.testiny.io/SILVE/testcases/tc/117/edit) | RF27 | CUS27 | Funcional | MOD-07 | Aprobado |
| [TC-118](https://app.testiny.io/SILVE/testcases/tc/118/edit) | RF27 | CUS27 | Funcional | MOD-07 | Aprobado |
| [TC-120](https://app.testiny.io/SILVE/testcases/tc/120/edit) | RF28 | CUS28 | Funcional | MOD-07 | Aprobado |
| [TC-121](https://app.testiny.io/SILVE/testcases/tc/121/edit) | RF28 | CUS28 | Funcional | MOD-07 | Aprobado |
| [TC-122](https://app.testiny.io/SILVE/testcases/tc/122/edit) | RF28 | CUS28 | Funcional | MOD-07 | Aprobado |
| [TC-123](https://app.testiny.io/SILVE/testcases/tc/123/edit) | RF29 | CUS29 | Funcional | MOD-07 | Aprobado |
| [TC-124](https://app.testiny.io/SILVE/testcases/tc/124/edit) | RF29 | CUS29 | Funcional | MOD-07 | Aprobado |
| [TC-125](https://app.testiny.io/SILVE/testcases/tc/125/edit) | RF29 | CUS29 | Funcional | MOD-07 | Aprobado |
| [TC-128](https://app.testiny.io/SILVE/testcases/tc/128/edit) | RF07 | CUS07; pago relacionado CUS06 | Regresión | MOD-03 | Aprobado |
| [TC-129](https://app.testiny.io/SILVE/testcases/tc/129/edit) | RF07 | CUS07; pago relacionado CUS06 | Seguridad | MOD-03 | Aprobado |
| [TC-130](https://app.testiny.io/SILVE/testcases/tc/130/edit) | RF07 | CUS07; pago relacionado CUS06 | Seguridad | MOD-03 | Aprobado |
| [TC-131](https://app.testiny.io/SILVE/testcases/tc/131/edit) | RF09 | CUS07 (nueva membresía/renovación); CUS03 y CUS06 relacionados | Regresión | MOD-03 | Aprobado |
| [TC-134](https://app.testiny.io/SILVE/testcases/tc/134/edit) | RF14 | CUS12 y CUS13 | Seguridad | MOD-05 | Aprobado |
| [TC-135](https://app.testiny.io/SILVE/testcases/tc/135/edit) | RF13 | CUS11 | Regresión | MOD-05 | Aprobado |
| [TC-136](https://app.testiny.io/SILVE/testcases/tc/136/edit) | RF15 | CUS14 y CUS15 | Regresión | MOD-06 | Aprobado |
| [TC-139](https://app.testiny.io/SILVE/testcases/tc/139/edit) | RF19, RF20 | CUS20 | Integración | MOD-08 | Aprobado |
| [TC-141](https://app.testiny.io/SILVE/testcases/tc/141/edit) | RF23, RF24 | CUS23 | Seguridad | MOD-09 | Aprobado |
| [TC-143](https://app.testiny.io/SILVE/testcases/tc/143/edit) | RF01, RF27, RF29 | CUS29 | Seguridad | MOD-07 | Aprobado |
| [TC-144](https://app.testiny.io/SILVE/testcases/tc/144/edit) | RF11 | CUS10 | Integración | MOD-11 | Aprobado |
| [TC-148](https://app.testiny.io/SILVE/testcases/tc/148/edit) | RF01 | CUS01 | Unitaria | MOD-01 | Aprobado |
| [TC-149](https://app.testiny.io/SILVE/testcases/tc/149/edit) | RF05 | CUS05 | Unitaria | MOD-02 | Aprobado |
| [TC-150](https://app.testiny.io/SILVE/testcases/tc/150/edit) | RF07 | CUS07; pago relacionado CUS06 | Unitaria | MOD-03 | Aprobado |
| [TC-151](https://app.testiny.io/SILVE/testcases/tc/151/edit) | RF08 | CUS08 | Unitaria | MOD-04 | Aprobado |
| [TC-152](https://app.testiny.io/SILVE/testcases/tc/152/edit) | RF14 | CUS12 y CUS13 | Unitaria | MOD-05 | Aprobado |
| [TC-153](https://app.testiny.io/SILVE/testcases/tc/153/edit) | RF15 | CUS14 y CUS15 | Unitaria | MOD-06 | Aprobado |
| [TC-154](https://app.testiny.io/SILVE/testcases/tc/154/edit) | RF26 | CUS26 | Unitaria | MOD-07 | Aprobado |
| [TC-155](https://app.testiny.io/SILVE/testcases/tc/155/edit) | RF20 | CUS20 | Unitaria | MOD-08 | Aprobado |
| [TC-156](https://app.testiny.io/SILVE/testcases/tc/156/edit) | RF23 | CUS23 | Unitaria | MOD-09 | Aprobado |
| [TC-157](https://app.testiny.io/SILVE/testcases/tc/157/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Unitaria | MOD-10 | Aprobado |
| [TC-158](https://app.testiny.io/SILVE/testcases/tc/158/edit) | RF11 | CUS10 | Unitaria | MOD-11 | Aprobado |
| [TC-159](https://app.testiny.io/SILVE/testcases/tc/159/edit) | RF02 | CUS02 | Integración | MOD-01 | Aprobado |
| [TC-160](https://app.testiny.io/SILVE/testcases/tc/160/edit) | RF03 | CUS03 | Integración | MOD-02 | Aprobado |
| [TC-161](https://app.testiny.io/SILVE/testcases/tc/161/edit) | RF07 | CUS07; pago relacionado CUS06 | Integración | MOD-03 | Aprobado |
| [TC-162](https://app.testiny.io/SILVE/testcases/tc/162/edit) | RF08 | CUS08 | Integración | MOD-04 | Aprobado |
| [TC-165](https://app.testiny.io/SILVE/testcases/tc/165/edit) | RF27 | CUS27 | Integración | MOD-07 | Aprobado |
| [TC-166](https://app.testiny.io/SILVE/testcases/tc/166/edit) | RF20 | CUS20 | Integración | MOD-08 | Aprobado |
| [TC-167](https://app.testiny.io/SILVE/testcases/tc/167/edit) | RF24 | CUS31 (amplía CUS24; el documento está en carpeta CUS30) | Integración | MOD-09 | Aprobado |
| [TC-168](https://app.testiny.io/SILVE/testcases/tc/168/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Integración | MOD-10 | Aprobado |
| [TC-169](https://app.testiny.io/SILVE/testcases/tc/169/edit) | RF11 | CUS10 | Integración | MOD-11 | Aprobado |
| [TC-170](https://app.testiny.io/SILVE/testcases/tc/170/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-171](https://app.testiny.io/SILVE/testcases/tc/171/edit) | RF29 | CUS29 | Funcional | MOD-07 | Aprobado |
| [TC-172](https://app.testiny.io/SILVE/testcases/tc/172/edit) | RF21 | CUS21 | Seguridad | MOD-09 | Aprobado |
| [TC-173](https://app.testiny.io/SILVE/testcases/tc/173/edit) | RF11 | CUS10 | Seguridad | MOD-11 | Aprobado |
| [TC-175](https://app.testiny.io/SILVE/testcases/tc/175/edit) | RF15 | CUS14 y CUS15 | Regresión | MOD-06 | Aprobado |
| [TC-176](https://app.testiny.io/SILVE/testcases/tc/176/edit) | RF21 | CUS21 | Regresión | MOD-09 | Aprobado |
| [TC-178](https://app.testiny.io/SILVE/testcases/tc/178/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Rendimiento | MOD-10 | Aprobado |
| [TC-179](https://app.testiny.io/SILVE/testcases/tc/179/edit) | RF16 | CUS16 y CUS17 | Rendimiento | MOD-06 | Aprobado |
| [TC-181](https://app.testiny.io/SILVE/testcases/tc/181/edit) | RF26 | CUS26 | Compatibilidad | MOD-07 | Aprobado |
| [TC-184](https://app.testiny.io/SILVE/testcases/tc/184/edit) | RF01 | CUS01 | Arquitectura | MOD-01 | Aprobado |
| [TC-185](https://app.testiny.io/SILVE/testcases/tc/185/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Arquitectura | MOD-10 | Aprobado |
| [TC-187](https://app.testiny.io/SILVE/testcases/tc/187/edit) | RF17 | CUS18 (correspondencia por nombre de carpeta) | Comprobación básica (Sanity) | MOD-10 | Aprobado |
| [TC-192](https://app.testiny.io/SILVE/testcases/tc/192/edit) | RF20 | CUS20 | Funcional | MOD-08 | Aprobado |
| [TC-193](https://app.testiny.io/SILVE/testcases/tc/193/edit) | RF19 | CUS19 | Funcional | MOD-08 | Aprobado |
| [TC-196](https://app.testiny.io/SILVE/testcases/tc/196/edit) | RF23 | CUS23 | Integración | MOD-09 | Aprobado |
| [TC-197](https://app.testiny.io/SILVE/testcases/tc/197/edit) | RF24 | CUS24 | Funcional | MOD-09 | Aprobado |
| [TC-198](https://app.testiny.io/SILVE/testcases/tc/198/edit) | RF21, RF23, RF24 | CUS21, CUS23, CUS24 | Seguridad | MOD-09 | Aprobado |

Los tipos son los documentados en Testiny; cada prueba técnica conserva además su tipo por carpeta. No se suman pruebas unitarias, variantes o varios RF como si fueran casos manuales distintos.

## Revisión de fuentes · 2026-11-17

Se revisaron los cambios posteriores al registro inicial que invalidaban las
huellas de seis archivos (42 selectores). El catálogo de 199 casos, los 100
casos seleccionados, sus pasos y el mínimo del 50 % se mantienen.

- Inventario/tienda: se registra el saldo inicial del producto en movimientos;
  el fixture sin historial usa stock cero. Los selectores revisados mantienen
  sus aserciones de reserva, reposición, cancelación y conservación de ventas.
- Inventario genérico y concurrencia: los fixtures usan categoría `Limpieza`,
  sin unidades identificadas. Conservan las comprobaciones de stock, edición,
  validaciones, historial y exclusión concurrente. El flujo de equipos por unidad
  se comprueba por separado en `test_inventario_unidades.py`.
- Lecturas: la carga completa pasa de 19 a 20 tablas al incorporar
  `INVENTARIO_UNIDADES`; mantiene el máximo de seis conexiones.
- Navegación: Inventario y el panel compartido incluyen `/api/inventario/unidades`
  entre los recursos esperados; se conservan los contratos de carga por módulo.

Se actualizan únicamente las huellas SHA-256 de estas fuentes tras compararlas
con sus versiones revisadas. La nueva regresión ejecuta `load_review` sobre el
repositorio real para detectar futuras desactualizaciones durante el PR.
Esta revisión no acredita nuevamente por sí sola los 100 casos: su ejecución
completa exige informes nuevos de las suites, validados con `--documented`.

## Configuración SSR de frontend · 2026-11-18

La preparación de las pruebas que cargan módulos con Vite usa un servidor SSR
compartido con la optimización de dependencias del cliente desactivada. Se
revisaron los cambios en los selectores de frontend y sus fixtures. Las
aserciones, los datos y los resultados esperados permanecen iguales. Las
huellas de las fuentes afectadas y del nuevo soporte se registran en
`automatizacion.json`.
