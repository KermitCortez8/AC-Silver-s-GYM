# Plan de pruebas funcionales de AC Silver's GYM

**ID:** PP-GYM-001 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
**Base:** contratos de los once módulos y casos organizados en este directorio,
sobre `7744c6c` más los cambios del árbol de trabajo. Es un plan de verificación
del producto existente. Su redacción no ejecuta ni aprueba los casos programados.

## Objetivo y alcance

Verificar las funcionalidades utilizadas por los casos: identidad y permisos,
registro y edición de clientes, pagos/activación/renovación, oferta comercial,
matrícula por fecha, asistencia, rutinas, stock y pedidos, paneles y avisos.
La aceptación exige resultados correctos, aislamiento por usuario, conservación
de importes/fechas/historial y ausencia de escrituras parciales ante errores o reintentos.

El alcance de referencia tiene **89 escenarios CP** y **1.177 casos CT**:
805 backend y 372 frontend. La instantánea histórica registra 1.123 aprobados y
54 omitidos; esos resultados se consultan en [validation.md](../validation.md),
no constituyen una ejecución de este plan. Cada variante CP se registra por
separado; un escenario agrupado puede necesitar varios CT y pruebas de interfaz.

Se añaden como verificaciones complementarias del mismo comportamiento las
pruebas Deno de correo, los controles documentales/arquitectónicos, compilación
y los recorridos de aceptación en navegador. No se suman a los 1.177 CT catalogados.

Quedan fuera la integración productiva del prototipo de chatbot 002, cargas o
rendimiento sostenido sin umbral definido, penetración externa, despliegues,
cobros reales y entrega real de correo. La concurrencia SQL comprueba cupos,
stock e idempotencia, sin presentarla como prueba de carga.

## Alcance por módulo y trazabilidad

Cada plan de módulo identifica sus funcionalidades, CP/CA, tipos, prioridad,
datos, dependencias, regresión y evidencia. El catálogo CT se selecciona mediante
sus rutas/selectores exactos en el JSON. Los números de la tabla son propiedad
del catálogo por carpeta; una regresión de módulo también incluye fuentes
compartidas enlazadas por sus CP y puede ejecutar más casos que esa cifra.

| Módulo | Funcionalidades principales | CT backend / frontend | Escenarios CP | Plan de módulo |
| --- | --- | ---: | ---: | --- |
| MOD-01 · Identidad y acceso | Acceso, Google, revocación, identidad estable y navegación. | 10 / 19 | 6 | [Plan](01-identidad-acceso/plan-de-pruebas.md) |
| MOD-02 · Clientes | Búsqueda, alta, edición, preregistro, reconciliación y borrado con historial. | 66 / 36 | 9 | [Plan](02-clientes/plan-de-pruebas.md) |
| MOD-03 · Membresías y pagos | Estados, pago verificado, primera activación, vigencia, historial y renovación. | 91 / 17 | 9 | [Plan](03-membresias-pagos/plan-de-pruebas.md) |
| MOD-04 · Planes y promociones | Planes/duración, descuentos, vigencia, cupos y precio contratado. | 3 / 10 | 6 | [Plan](04-planes-promociones/plan-de-pruebas.md) |
| MOD-05 · Horarios y matrículas | Catálogo, identidad propia, reserva/cancelación por fecha y concurrencia. | 30 / 8 | 8 | [Plan](05-horarios-matriculas/plan-de-pruebas.md) |
| MOD-06 · Asistencias | Entrada/salida, aforo, horario/fecha, bloqueo cruzado, auditoría y automatización. | 101 / 17 | 15 | [Plan](06-asistencias/plan-de-pruebas.md) |
| MOD-07 · Rutinas y progreso | Ejercicios, asignación compatible, actor, progreso y descanso. | 7 / 8 | 5 | [Plan](07-rutinas-progreso/plan-de-pruebas.md) |
| MOD-08 · Inventario y movimientos | Reserva/reposición, movimientos, estados, archivo y validación de cantidades. | 63 / 27 | 7 | [Plan](08-inventario/plan-de-pruebas.md) |
| MOD-09 · Tienda y pedidos | Catálogo/carrito, checkout, stock, cancelación, privacidad, imágenes y Papelera. | 5 / 10 | 8 | [Plan](09-tienda-pedidos/plan-de-pruebas.md) |
| MOD-10 · Paneles y configuración | Indicadores, fechas, configuración, recursos por sección y sesiones aisladas. | 18 / 23 | 6 | [Plan](10-paneles-configuracion/plan-de-pruebas.md) |
| MOD-11 · Notificaciones | Confirmación, recordatorio por fecha, reintento, privacidad y deduplicación. | 21 / 0 | 6 | [Plan](11-notificaciones/plan-de-pruebas.md) |
| Transversal · Controles transversales | Errores HTTP, resultado incierto, validaciones, rollback y arquitectura. | 390 / 197 | 4 | [Plan](transversales/plan-de-pruebas.md) |

## Estrategia y tipos de prueba

| Tipo | Funcionalidades o riesgos comprobados | Evidencia esperada |
| --- | --- | --- |
| Unitaria/modelos | Validación, dinero, duraciones, fechas, identidad, cantidades y fronteras. | Resultado de cada CT y su variante; sin escrituras ante dato inválido. |
| Integración HTTP/aplicación con dobles | Permisos reales de ruta, actor, estados, errores, reintento, gateways y consistencia local. | Respuesta/código HTTP, llamadas observadas y estado anterior/posterior. |
| PostgreSQL real | RPC, RLS/permisos, migración repetible, recarga, rollback, conflictos y cupo/stock en paralelo. | Consultas del contenedor y resultado de carreras; ninguna escritura parcial. |
| Interfaz Node/SSR | Stores/composables/componentes, borrador, doble clic, respuestas obsoletas y sesiones. | Estado/payload y resultado del runner; separado de la revisión visual. |
| Navegador y aceptación | Recorridos de negocio, errores visibles, teclado, móvil/escritorio y temas. | Pasos y capturas de la interfaz real; indicar si API es simulada o local integrada. |
| Edge Function | Fecha del aviso, ID de entrega, reintentos, secreto de acceso y errores seguros. | `deno check`/`deno test`; Resend y repositorio inyectados, sin entrega real. |
| Regresión y controles | Cruces entre módulos, capas, enlaces, build y errores Python críticos. | Suite de la versión final y controles complementarios diferenciados. |

Las pruebas de rol, fronteras, error, concurrencia e idempotencia se ejecutan en
el tipo que las demuestra. No se considera equivalente un mock a PostgreSQL,
una pantalla simulada a un recorrido integrado, ni build a aceptación funcional.

## Entorno y datos de prueba

Preparar dependencias declaradas en backend/frontend y las imágenes de pruebas
con sus versiones registradas. Utilizar las instrucciones del [DoD](../../../docs/DoD.md)
y [CI](../../../../.github/workflows/pr-validation.yml). Mantener las herramientas
adicionales de navegador fuera del producto cuando el procedimiento existente lo indica.

| Recurso / datos | Preparación y variantes |
| --- | --- |
| Identidades y roles | Visitante, admin, staff, trainer y user; C1/C2 distintos; cuenta interna desactivada, primera compra pendiente, cliente vigente/vencido/futuro. Contraseña/token sintéticos. |
| Datos personales | DNI de ocho y teléfono de nueve dígitos, ceros iniciales, correo permitido `.com`; máximo y máximo+1 según cada campo. Sin datos de personas reales. |
| Oferta y dinero | Plan 100, promoción 10 % e importe 90; importe guardado cero; cambio posterior del catálogo y redondeo en céntimos. |
| Fechas | Reloj controlado `America/Lima`; D es hoy de negocio y F fin inclusivo de membresía. Casos a medianoche, cambio de mes/año, F−8/F−7 y F/F+1. |
| Sesiones y asistencia | Horario 09:00–10:00, entrada inicio inclusivo/fin exclusivo, salida hasta 11:00 inclusive; después incompleta. General a 09:00 completa a 12:00 y cierre automático solo al superar tres horas. |
| Visita cruzada | Aviso en franja de clase ampliada ±30 min inclusivos, misma fecha y cruce de medianoche; fuera del aviso la visita abierta continúa bloqueando una nueva entrada. |
| Stock y cupos | Reserva 10/tienda 2, reposición 3; último cupo/unidad con dos solicitudes concurrentes; corrección que daría saldo negativo y rollback forzado. |
| Proveedores | Google, Stripe y Resend con dobles; sesiones pagada/impaga/alterada, timeout y duplicado; respuesta de correo con/sin ID. |
| SQL | PostgreSQL desechable `gym_test`, usuario `postgres`, `GYM_TEST_POSTGRES_CONTAINER` explícito; credenciales sintéticas, sin puertos publicados y sin red para la corrida. Imagen con pg_cron para automatización real. |
| Interfaz | Escritorio y móvil, teclado y temas claro/oscuro; red fallida, respuesta demorada, datos vacíos y catálogo no disponible. |

Cada caso/variante parte de fixtures limpios. Para recorridos compuestos se
mantienen sus entidades entre pasos y se limpian al cerrar. Las migraciones
se aplican por dependencias declaradas por cada fixture, no por orden alfabético.
Concurrencia dentro de una prueba sí; dos suites que truncan la misma base se
programan secuencialmente. Cada ejecución utiliza un contenedor propio.

## Criterios de entrada

1. Registrar commit y estado del árbol, versiones, entorno y catálogo seleccionado;
   conciliar sus CT/CP con la fuente. Si cambian las pruebas, actualizar el alcance.
2. Tener datos ficticios, roles y relojes controlados; gateways inyectados y
   configuración privada fuera de evidencia/logs. La sesión backend usa una clave sintética.
3. Comprobar dependencias del módulo y datos previos del recorrido. Las variantes
   SQL/cron solo inician con su contenedor/esquema/extensión disponibles.
4. Identificar antes de ejecutar los bloqueos conocidos y variantes sin evidencia
   directa. Se pueden ejecutar otras fases independientes; no dar por aprobado el bloque afectado.
5. Crear un registro de ejecución por versión con responsables y ubicación de
   evidencias. Las personas se asignan al comenzar la corrida, sin atribuir trabajo ya realizado.

## Orden de ejecución por hitos

| Hito | Actividad y orden funcional | Condición para avanzar |
| --- | --- | --- |
| H0 · Preparación | Conciliar catálogo, roles/datos, dependencias y bloqueos; preparar evidencia. | Criterios de entrada satisfechos para el bloque que se va a probar. |
| H1 · Reglas | Unitarias/modelos de identidad, oferta/dinero, fechas, cantidades y validación. | Resultados esperados y frontera inválida sin mutación. |
| H2 · Servicios y API | MOD-01/04 → MOD-02/03 → MOD-05/07/06; MOD-08 → MOD-09; MOD-10/11 observan resultados. Añadir transversales a cada cambio. | Flujos locales, permisos e idempotencia comprobados; defectos registrados. |
| H3 · Persistencia | Ejecutar serialmente las suites SQL de todos los módulos, después variantes pg_cron. | Evidencia de recarga/locks/rollback; declarar bloques pendientes por falta de esquema. |
| H4 · Aceptación | Recorrer R01–R05 en interfaz/API local con datos sintéticos; estados feliz/error, fechas y sesiones. | Cada CP y variante programados tiene resultado y evidencia del mecanismo exigido. |
| H5 · Regresión final | Tras corregir fallos, repetir afectados/dependientes y ejecutar suites completas, Deno y controles. | Evidencia de la misma versión final; sin introducir fallos ni perder CT. |
| H6 · Informe | Conciliar resultados, defectos, omisiones, evidencias y limpieza. | Criterios de salida; cierre aprobado o informe explícitamente parcial/bloqueado. |

Los hitos expresan dependencia y orden, no fechas ni duración comprometidas.
Un bloqueo de una rama no detiene pruebas independientes. Una corrección requiere
reverificar lo afectado y registrar la versión; no mezclar resultados de commits
como si fueran una sola corrida completa.

## Recorridos funcionales entre módulos

| Recorrido | Secuencia programada | Comprobación final y referencias |
| --- | --- | --- |
| R01 · Alta a uso del gimnasio | Consultar oferta → preregistrar → verificar pago simulado → primera activación admin → acceder como cliente → reservar fecha → asignar rutina → entrada/salida admin → consultar historial y avisos. | Un cliente/membresía/pago, identidad propia, cupo/aforo coherentes, ejercicio/fecha y privacidad conservados. CP de [clientes](02-clientes/casos-de-uso.md), [pagos](03-membresias-pagos/casos-de-uso.md), [matrículas](05-horarios-matriculas/casos-de-uso.md), [asistencia](06-asistencias/casos-de-uso.md), [rutinas](07-rutinas-progreso/casos-de-uso.md) y [avisos](11-notificaciones/casos-de-uso.md). |
| R02 · Vencimiento y renovación | Llegar a F/F+1; comprobar acceso → revisar renovación F−8/F−7/vencida → efectivo con recibo o Stripe simulado → repetir confirmación → consultar fechas, historial y aviso. | Primera compra no elude activación; renovación pagada se habilita sin otra aprobación y conserva días; duplicado no extiende ni duplica cargo. CP-M03-03/05/07/08/09 y CP-M11-06. |
| R03 · Reserva a pedido | Alta de reserva → reponer tienda → dos compradores intentan última unidad → crear checkout → cancelar pendiente o confirmar pago y tramitar pedido → archivar/restaurar producto. | Stocks y movimientos exactos; devolución única; cancelación no oculta pago concurrente; historial comercial preservado. CP de [inventario](08-inventario/casos-de-uso.md) y [tienda](09-tienda-pedidos/casos-de-uso.md); la entrega impaga exige verificación directa pendiente. |
| R04 · Borrar cliente con historial | Crear cliente con venta, matrícula y progreso → borrar en entorno aislado → recargar cuenta, dependencias, cupos, venta y comprador; repetir con fallo de transacción. | Borrado y rollback atómicos, venta/líneas/importes/stock conservados y otro cliente intacto. CP-M02-07, CP-M09-04 y CP-TR-03. |
| R05 · Fallo y cambio de sesión | Dejar consulta/escritura demorada → cambiar/cerrar sesión → responder desde sesión previa → navegar a otro módulo → simular fallo de proveedor/cola. | Sin datos de otro usuario, sin éxito falso ni reintento ciego de una escritura incierta; operación confirmada no se revierte por correo. CP-M01-04, CP-M10-03/04/06, CP-M11-03 y CP-TR-01/02. |

Los CP completos fijan los pasos y variantes. Para un recorrido integrado usar
la API local y la misma persistencia aislada, con proveedores dobles. Una revisión
visual con API interceptada acredita solo esa interacción, no todo el recorrido.

## Comandos y evidencia reproducible

Desde la raíz, con el entorno preparado:

```bash
(cd backend && python -m pytest tests/ -q)
(cd backend && python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics)
(cd frontend && npm test)
(cd frontend && npm run build)
deno check supabase/functions/schedule-emails/index.ts
deno test supabase/tests/
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

La corrida sin contenedor puede omitir SQL. Para cubrirlo, seleccionar sus ocho
archivos con `GYM_TEST_POSTGRES_CONTAINER` configurado exclusivamente para la
base desechable; los [planes de módulos](#alcance-por-módulo-y-trazabilidad) y
[DoD](../../../docs/DoD.md) enlazan sus suites. Comprobar aparte pg_cron.
El job SQL de CI enumera seis suites; las de borrado de clientes y avisos de
renovación también se programan en este plan, aunque ese job no las invoque.
El archivo de 023 debe resolverse para ejecutar sus cuatro casos generales.

Los recorridos de navegador se preparan con los procedimientos/fixtures del
[inventario histórico](../pruebas-por-modulo.md); los reportes y capturas deben
pertenecer a esta corrida. Los scripts manuales de inserción no son requisito
para aprobar la suite: usar datos sintéticos y fixtures del entorno aislado.

## Roles durante la ejecución

| Rol de trabajo | Responsabilidad prevista |
| --- | --- |
| Coordinación de pruebas | Fijar versión/selección, asignar ejecutores, conciliar resultados y emitir informe. |
| Ejecución backend/datos | Preparar fixtures, API y contenedor; verificar permisos, dinero, SQL, concurrencia y limpieza. |
| Ejecución frontend/aceptación | Verificar flujos, errores, sesiones, navegación, teclado y evidencias visuales. |
| Mantenimiento | Corregir defectos encontrados y aportar una versión verificable con regresión pertinente. |
| Revisión funcional | Contrastar resultados de los recorridos CP con reglas del módulo y aceptar o registrar cobertura pendiente. |

Son responsabilidades, no personas asignadas ni agentes adicionales. Una persona
puede cubrir varias; el informe registra quién realizó cada comprobación.

## Prioridades, defectos y criterios de suspensión

P1 incluye acceso/privacidad, cobros, activación/vigencia, cupos, stock,
idempotencia, auditoría y atomicidad. P2 incluye listados, navegación, filtros,
presentación y ergonomía. Todo P1 se verifica antes del cierre del bloque que depende de él.

| Severidad | Ejemplo e intervención prevista |
| --- | --- |
| S1 · Crítica | Acceso ajeno, pago/stock/cupo incorrecto, pérdida de historial o escritura parcial: detener el recorrido afectado, conservar evidencia y volver a estado limpio. |
| S2 · Alta | Flujo principal no utilizable o resultado falso sin alternativa fiable: bloquear aceptación de la funcionalidad y ejecutar regresión tras corregir. |
| S3 · Media | Fallo funcional acotado con alternativa válida: registrar variante, impacto y resolución prevista; no marcar aprobado el caso fallido. |
| S4 · Baja | Problema visual/textual sin afectar reglas: registrar evidencia y seguimiento; el estado del caso sigue reflejando lo observado. |

Si faltan esquema, contenedor o proveedor de prueba, registrar Bloqueado/Omitido
con causa. Si se detectan datos de un entorno compartido o inconsistencias de
fixtures, detener esa ejecución y rehacer el entorno. Reanudar el bloque solo
tras corregir la causa, comprobar su preparación y repetir el caso afectado.

## Riesgos y cobertura pendiente ya identificados

| Dependencia o brecha | Impacto y tratamiento en la ejecución |
| --- | --- |
| [023 vacía](../../../../backend/migrations/023_general_attendance_three_hour_close.sql) | CP-M06-13 y cuatro CT SQL generales quedan bloqueados. Probar cierre con dobles no aprueba cron/RPC real. La resolución SQL es trabajo distinto a redactar este plan. |
| Caso de checkout/entrega de tienda con fuente de código | CP-M09-01 y variante impaga de CP-M09-03 requieren prueba directa y evidencia del resultado; la suite compartida Stripe no cierra automáticamente esos casos. |
| PostgreSQL sin pg_cron | Pruebas de RPC pueden pasar; variantes del programador se registran omitidas hasta preparar imagen/extensión adecuada. |
| Proveedores externos simulados | Verifica lógica, no configuración ni entrega/cobro reales. No declarar operación productiva certificada. |
| Diferencia de fechas/versión | Congelar reloj Lima y registrar versión/datos; actualizar catálogo y repetir afectados si cambia la fuente. |
| SQL truncando una misma base | Ejecutar suites secuencialmente y usar un contenedor exclusivo para evitar resultados contaminados. |
| Respuesta incierta | Consultar/reconciliar estado antes de ofrecer otro intento; no reenviar automáticamente la escritura. |

## Registro, métricas y gestión de evidencia

Por ejecución registrar: ID de corrida, commit/árbol, entorno/versiones, rol,
CP/variante, CT/selector o procedimiento manual, datos/reloj, resultado esperado,
observado, responsable, defecto y evidencia. Usar estados Pendiente, Aprobado,
Fallido, Omitido y Bloqueado. Conservar archivos de runner y capturas/consultas
sintéticas; las credenciales y tokens no forman parte del informe.

Conciliar CT únicos por selector y componente; repetir uno en varios módulos no
lo convierte en un caso nuevo. Mantener el registro de CP/variantes separado
para no contar una aceptación manual como otro CT automatizado.

- Cobertura de ejecución CT = (aprobados + fallidos) / CT programados.
- Aprobación de ejecutados = aprobados / (aprobados + fallidos).
- Resolución de escenarios = CP con todas sus variantes verificadas / CP programados.
- Informar además omisiones, bloqueos, defectos por severidad y criterios CA sin evidencia.

Sin denominador registrar «no aplica». No sumar omisiones como aprobación ni
combinar corridas históricas como una ejecución. Estos indicadores no son
cobertura de líneas, rendimiento ni disponibilidad de producción.

## Criterios de salida y entregables

Para declarar aprobado el alcance completo: todos los CT y CP/variantes
programados están ejecutados y aprobados, sin omisiones/bloqueos, sin defectos
S1/S2 abiertos y con evidencia del mecanismo requerido. Los criterios CA tienen
trazabilidad al resultado; SQL y navegador exigidos no quedan sustituidos por dobles/SSR.

Si falta un bloque, emitir informe **parcial o bloqueado** que identifique las
funcionalidades no verificadas y sus causas; no declarar el plan completo aprobado.
Con 023 vacía, el cierre general SQL mantiene ese impedimento aunque el resto pase.

Entregar selección/versión, resultados por módulo/tipo/CP/CT, evidencias,
registro de defectos/repruebas, matriz de cobertura y omisiones, estado del
entorno/limpieza y conclusión del alcance. Retirar contenedor y datos sintéticos
al finalizar. Registrar la corrida en [validation.md](../validation.md) o en un
informe enlazado desde allí, siguiendo el [DoD](../../../docs/DoD.md).
