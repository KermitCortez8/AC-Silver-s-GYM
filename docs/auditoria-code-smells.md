# Revisión de code smells y fallos asociados

Rama: `feat/reestructuracion`. Commit revisado: `b2fa5f6`. Fecha: 2026-10-23.

La revisión anterior fue acotada. Esta revisión abarca transversalmente el código versionado de backend, frontend, migraciones, tareas de correo y CI. Se utilizaron inspección de código, análisis de duplicación y referencias, análisis de Python y reproducciones locales con datos sintéticos. Durante la auditoría inicial no se modificó código del proyecto ni se llamó a la base de producción. Las referencias apuntan al commit auditado para conservar la evidencia aunque cambien los archivos. El seguimiento de las correcciones está en [correcciones-prioritarias.md](correcciones-prioritarias.md). No es una prueba de que no existan más problemas en ejecución o en configuración externa.

Se agrupan las repeticiones del mismo problema; los 42 grupos incluyen code smells de mantenimiento y fallos funcionales o de seguridad. Los riesgos no reproducidos se distinguen de los casos comprobados. La presencia de archivos `__init__.py` vacíos es intencional y no se considera un code smell.

## 01. Autorización inconsistente en la API — Crítica

[backend/presentation/routes/inventory_routes.py:26](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/inventory_routes.py#L26); [backend/presentation/routes/store_routes.py:50](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/store_routes.py#L50); [backend/presentation/routes/memberships_routes.py:24](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/memberships_routes.py#L24); [backend/presentation/dependencies.py:177](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/dependencies.py#L177)

Crear inventario, borrar productos y editar planes no exige un usuario autorizado. get_optional_actor_id identifica al actor si lo hay, pero admite None. GET /tienda/pedidos devuelve pedidos con datos de clientes sin autenticación. En una aplicación FastAPI en memoria, sustituyendo únicamente get_gym_service por un servicio simulado, las peticiones sin Authorization devolvieron 200, 204, 200 y 200, respectivamente. No se llamó a una base real.

**Orientación:** Definir permisos por operación, aplicarlos como dependencias y filtrar los pedidos según el usuario. Añadir pruebas negativas de acceso.

## 02. Identificadores de usuarios que colisionan entre roles — Alta

[backend/domain/services/accounts_rules.py:104](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/accounts_rules.py#L104); [backend/infrastructure/repositories/gym_repository.py:602](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L602)

Se genera un consecutivo por prefijo de rol, pero persistencia elimina el prefijo y usa solamente el número. Reproducción: SGADM001, SGTRA001 y SGSTA001 se convierten todos a id_usuario=1. _sync_table también indexa por ese número y puede confundir filas diferentes.

**Orientación:** Usar una identidad estable y única de base de datos, independiente del rol; conservar el código visible como atributo separado.

## 03. Mapeos incompletos de promociones y membresías — Alta

[backend/infrastructure/repositories/gym_repository.py:696](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L696); [backend/infrastructure/repositories/gym_repository.py:765](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L765)

Los mappers de promoción no leen ni escriben limite_cupos, usos_actuales, icono_etiqueta y palabra_clave. La asociación id_promocion de la membresía tampoco se conserva en los mappers. La conversión con datos sintéticos confirmó la pérdida de los campos de promoción, sin depender del estado de Supabase.

**Orientación:** Alinear contratos, esquema y ambos sentidos del mapeo; verificar guardar y volver a leer los mismos campos.

## 04. Mapeos incompletos de inventario y productos — Alta

[backend/infrastructure/repositories/gym_repository.py:851](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L851); [backend/infrastructure/repositories/gym_repository.py:904](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L904)

Inventario reemplaza unidad_venta, precio_venta, stock_minimo, ubicacion y observaciones por valores fijos. Productos pierde descripcion y unidad_venta. Reproducción de ida y vuelta: pack pasa a unidad, 12.5 pasa a 0, stock mínimo 7 pasa a 1 y una ubicación y observación se pierden.

**Orientación:** Persistir y recuperar los campos soportados o hacer explícito cuáles son derivados y cuáles no se guardan.

## 05. Eliminaciones que aparentan éxito aunque falle el servidor — Alta

[frontend/src/application/modules/clients.js:147](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/clients.js#L147); [frontend/src/application/modules/store.js:91](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L91)

deleteMember dispara la petición sin esperarla y borra el estado local. deleteProductoTienda no comprueba response.ok y también elimina localmente. Con un adaptador que siempre devuelve HTTP 500, ambos métodos terminaron dejando vacías las listas locales.

**Orientación:** Esperar y comprobar la respuesta antes de actualizar el estado, o implementar una actualización optimista con reversión y error visible.

## 06. Estado del gimnasio sin limpiar al cerrar sesión — Alta

[frontend/src/application/stores/authStore.js:192](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/stores/authStore.js#L192); [frontend/src/application/modules/state.js:7](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/state.js#L7); [frontend/src/application/modules/synchronization.js:19](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/synchronization.js#L19)

signOut limpia autenticación y almacenamiento de sesión, pero no usuarios, clientes, pedidos, carrito ni otros datos de gymStore. El cambio de scope limpia cachés y errores, no las referencias. Reproducción con Pinia: authenticated=false, pero permanecen un usuario interno, un cliente y el carrito anteriores.

**Orientación:** Añadir un reinicio del estado de negocio coordinado con cierre y sustitución de sesión, y controlar respuestas pendientes de la sesión anterior.

## 07. Cálculo de dinero y descuentos divergente — Alta

[frontend/src/application/modules/memberships.js:45](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/memberships.js#L45); [backend/domain/services/memberships_rules.py:379](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/memberships_rules.py#L379); [frontend/src/application/modules/store.js:137](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L137)

El frontend redondea el descuento porcentual a unidades enteras; el backend redondea el resultado a dos decimales. Caso confirmado: 79 con 10 % da 71 en frontend y 71.10 en backend. Además se opera con Number/float sin un criterio monetario único.

**Orientación:** Definir precisión monetaria y redondeo comunes; usar centavos enteros o Decimal en backend y devolver la cotización oficial desde el caso de uso.

## 08. Fechas y horas con zonas horarias distintas — Alta

[frontend/src/domain/utils/gymRules.js:36](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L36); [frontend/src/domain/utils/dates.js:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/dates.js#L1); [backend/domain/services/gym_values.py:35](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_values.py#L35)

todayISO usa fecha UTC, limaDate usa America/Lima, nowTime usa la zona del navegador y _now_time la del servidor. A las 01:00 UTC del 23/10/2026, las dos funciones de fecha frontend devolvieron 23/10 y 22/10 para el mismo instante. Hay reglas de vigencia, filtros y asistencia que consumen estos helpers.

**Orientación:** Unificar el calendario de negocio en America/Lima e inyectar un reloj para pruebas; separar fecha civil de instante UTC.

## 09. Duración de membresías derivada del nombre — Alta

[backend/domain/services/memberships_rules.py:32](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/memberships_rules.py#L32); [backend/domain/services/memberships_rules.py:799](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/memberships_rules.py#L799); [frontend/src/domain/utils/gymRules.js:126](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L126)

La activación calcula días a partir de nombre_plan y no del campo duracion guardado en el plan. Un plan llamado MENSUAL conserva 30 días aunque su duración se configure de otra forma. En frontend durationMonths también puede contener el número extraído de una duración expresada en días.

**Orientación:** Representar duración con una unidad explícita y hacer que la activación y la presentación usen ese mismo dato.

## 10. Compensación de escrituras incompleta — Alta

[backend/infrastructure/repositories/gym_repository.py:313](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L313); [backend/infrastructure/repositories/gym_repository.py:513](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L513); [backend/infrastructure/repositories/gym_repository.py:547](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L547)

Se registran inserciones y actualizaciones para compensarlas, pero no los borrados. _sync_orders borra y recrea detalles sin guardar su estado previo en esa compensación. Si falla una operación posterior, restaurar el estado en memoria no garantiza restaurar todas las tablas remotas. También se silencian errores de la propia compensación.

**Orientación:** Usar transacciones/RPC para unidades de negocio completas o registrar y reconciliar explícitamente todas las operaciones, incluidos borrados y detalles.

## 11. Operaciones bloqueantes dentro de rutas async — Alta

[backend/presentation/routes/clients_routes.py:266](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/clients_routes.py#L266); [backend/presentation/routes/store_routes.py:136](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/store_routes.py#L136)

El webhook async ejecuta Stripe y operaciones de persistencia síncronas. La subida async llama al almacenamiento con urlopen/write_bytes síncronos. Al ejecutarse dentro de async def pueden bloquear el bucle de eventos durante esas operaciones.

**Orientación:** Mover esas llamadas a un ejecutor de hilos o adoptar adaptadores asíncronos; mantener el límite de concurrencia adecuado.

## 12. Concurrencia protegida solo dentro de un proceso — Alta

[backend/infrastructure/repositories/gym_repository.py:60](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L60); [backend/infrastructure/repositories/gym_repository.py:313](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L313); [backend/domain/services/gym_domain_service.py:193](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_domain_service.py#L193)

El lock y la caché viven en el proceso; varios comandos generan identificadores max+1 y actualizan registros a partir de una instantánea. Dos instancias no comparten ese lock. Las RPC de matrícula y asistencia protegen sus casos específicos, pero no todas las escrituras de stock, promociones y registros.

**Orientación:** Llevar los cambios que requieren exclusión a transacciones de base de datos, con IDs generados allí y control de versión donde corresponda. Es un riesgo de concurrencia identificado por diseño, no una carga concurrente ejecutada contra producción.

## 13. Repositorio con demasiadas responsabilidades — Media

[backend/infrastructure/repositories/gym_repository.py:17](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L17)

SupabaseGymRepository reúne en unas 1.248 líneas validación de esquema, caché, consultas, mapeos de muchas entidades, RPC, sincronización, compensaciones y reglas derivadas. La longitud acompaña una mezcla concreta de responsabilidades, no es por sí sola el problema.

**Orientación:** Separar mapeos y repositorios por agregado y dejar las transacciones en coordinadores específicos.

## 14. Herencia múltiple que mantiene un agregado global — Media

[backend/domain/services/gym_domain_service.py:40](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_domain_service.py#L40); [backend/application/services/gym_service.py:24](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/services/gym_service.py#L24)

GymDomainService y GymService combinan siete mixins cada uno. Los módulos dependen de métodos y estado aportados por los otros; por ejemplo cuentas crea membresías y tienda usa capacidades de inventario. La separación de archivos no permite usar cada módulo de forma independiente.

**Orientación:** Hacer explícitas las dependencias entre servicios/agregados mediante composición, conservando juntos los invariantes que realmente comparten una transacción.

## 15. Contratos basados en diccionarios y despacho por cadenas — Media

[backend/application/ports/gym_repository.py:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/ports/gym_repository.py#L1); [backend/application/services/gym_service.py:42](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/services/gym_service.py#L42)

El puerto expone State=dict[str, Any] y callbacks que conocen sus claves. _execute decide lectura/escritura con un booleano y resuelve reglas mediante getattr sobre nombres de texto. Errores de contrato quedan para ejecución y un cambio de estructura afecta varias capas.

**Orientación:** Introducir comandos y modelos tipados, métodos de repositorio expresivos y unidades de trabajo específicas donde aporten valor.

## 16. Rutas que orquestan casos de uso de pagos — Media

[backend/presentation/routes/clients_routes.py:108](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/clients_routes.py#L108); [backend/presentation/routes/clients_routes.py:266](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/clients_routes.py#L266)

Las rutas registran clientes, construyen pasarelas, crean checkout, clasifican tipos de pago y preparan notificaciones. Además importan helpers privados _value y _is_store_checkout desde aplicación y construyen adaptadores desde bootstrap.

**Orientación:** Encapsular registro y checkout y el procesamiento de eventos en casos de uso completos inyectados; dejar en la ruta validación HTTP y permisos.

## 17. Recursos de persistencia seleccionados por URL — Media

[backend/presentation/dependencies.py:25](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/dependencies.py#L25); [backend/presentation/dependencies.py:59](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/dependencies.py#L59)

READ_RESOURCES y _resources_for_request relacionan cadenas de rutas HTTP con nombres internos de tablas/estado. Añadir o cambiar una ruta obliga a mantener ese mapa; la ausencia de una entrada puede activar una lectura completa en lugar de la esperada.

**Orientación:** Hacer que los casos de uso declaren sus datos y que las dependencias de las rutas conecten esas capacidades de forma explícita.

## 18. Consultas con efectos secundarios de escritura — Media

[backend/domain/services/accounts_rules.py:207](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/accounts_rules.py#L207); [backend/infrastructure/repositories/gym_repository.py:250](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L250); [backend/application/services/gym_service.py:55](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/services/gym_service.py#L55)

clientes_normalized invoca expire_memberships aun cuando se ejecuta mediante repository.read. El refresco de inventario llama _guardar_estados_automaticos y ensure_fresh puede persistir vencimientos. Leer puede desencadenar cambios, complicando permisos, caché y trazabilidad.

**Orientación:** Separar las proyecciones de lectura de comandos de vencimiento y reconciliación, o documentar y encapsular explícitamente esas unidades de trabajo.

## 19. Decisiones de control basadas en textos de error — Media

[backend/domain/errors.py:8](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/errors.py#L8); [backend/presentation/routes/store_routes.py:31](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/store_routes.py#L31); [backend/presentation/routes/trainer_routes.py:53](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/trainer_routes.py#L53); [backend/infrastructure/supabase_client.py:45](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/supabase_client.py#L45)

Se decide entre 404/400 buscando no encontrado, se identifica un problema de membresía buscando su frase y se interpretan códigos SQL dentro de RuntimeError serializado. Cambiar un mensaje puede cambiar la respuesta de la API.

**Orientación:** Conservar código, tipo, mensaje público y causa técnica por separado; traducir excepciones de dominio de forma centralizada.

## 20. Fallbacks de esquema que ocultan fallos — Media

[backend/infrastructure/repositories/gym_repository.py:117](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L117); [backend/infrastructure/repositories/gym_repository.py:130](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L130); [backend/infrastructure/repositories/gym_repository.py:524](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L524)

_select_optional considera tabla ausente cualquier error cuyo texto contenga PGRST. _filter_remote_columns elimina campos desconocidos, y _sync_table omite tablas marcadas como ausentes. Un fallo puede aparentar lista vacía o escritura exitosa sin guardar lo esperado.

**Orientación:** Clasificar códigos concretos de ausencia de esquema y fallar de forma visible si un campo o tabla requerido por el comando no está disponible.

## 21. Validación de entrada dispersa y poco expresiva — Media

[backend/domain/models/gym.py:25](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/models/gym.py#L25); [backend/domain/models/gym.py:50](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/models/gym.py#L50); [backend/domain/models/gym.py:242](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/models/gym.py#L242)

Varios contratos aceptan nombre/correo vacíos, precio de plan sin límite inferior y fechas/horas como cadenas libres. Algunas reglas completan o corrigen datos por defecto y otras fallan más tarde. No todos los flujos tienen las mismas validaciones.

**Orientación:** Usar tipos y restricciones apropiados y centralizar invariantes en dominio; mantener en presentación la validación de formato del contrato.

## 22. Carga completa y paginación desigual — Media

[backend/infrastructure/supabase_client.py:53](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/supabase_client.py#L53); [backend/infrastructure/repositories/gym_repository.py:183](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L183); [backend/presentation/routes/attendance_routes.py:40](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/attendance_routes.py#L40)

Hay consultas con select_all y otras con select que no recorren páginas. La API de historial filtra y pagina una lista ya cargada en memoria. Mutaciones generales toman y comparan instantáneas amplias. Si la API remota limita filas, algunas tablas pueden quedar incompletas; con mucho historial aumenta el coste de cada petición.

**Orientación:** Consultar por agregado, filtros y rango en la base; definir paginación y consistencia para todos los listados. No se presupone un límite concreto configurado en Supabase.

## 23. Implementaciones repetidas del transporte REST — Baja

[backend/infrastructure/supabase_client.py:17](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/supabase_client.py#L17); [backend/infrastructure/supabase_client.py:88](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/supabase_client.py#L88); [backend/infrastructure/services/supabase_storage_service.py:27](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/services/supabase_storage_service.py#L27)

_request y rpc repiten autenticación, serialización, urlopen y traducción de HTTPError. Storage y notificaciones añaden accesos similares, algunas veces al método privado _request. Cambiar política de errores o timeouts requiere revisar varios sitios.

**Orientación:** Reutilizar una primitiva de transporte y exponer operaciones públicas suficientes para los repositorios.

## 24. Políticas de correo mantenidas en dos runtimes — Media

[backend/application/services/schedule_notifications.py:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/services/schedule_notifications.py#L1); [backend/infrastructure/repositories/schedule_notifications.py:28](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/schedule_notifications.py#L28); [supabase/functions/schedule-emails/worker.ts:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/supabase/functions/schedule-emails/worker.ts#L1); [supabase/functions/schedule-emails/email.ts:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/supabase/functions/schedule-emails/email.ts#L1)

El aviso de horarios se procesa en Python y en la Edge Function de TypeScript, con lógica de payload, reintentos y finalización en ambas partes. Los dos runtimes pueden estar justificados, pero las políticas equivalentes deben mantenerse sincronizadas.

**Orientación:** Definir qué capacidades son de cada ejecutor y compartir contratos y casos de prueba de comportamiento, sin eliminar un worker por asumir que es una copia innecesaria.

## 25. Store global con contexto compartido entre módulos — Media

[frontend/src/application/stores/gymStore.js:15](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/stores/gymStore.js#L15); [frontend/src/application/modules/state.js:7](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/state.js#L7)

Object.assign agrega todos los métodos al mismo ctx. Clientes usa helpers de dashboard, tienda llama sincronización e inventario y otros módulos acceden a referencias de cualquier entidad. El orden de montaje y las dependencias quedan implícitos.

**Orientación:** Reducir el contexto por módulo e inyectar las operaciones necesarias; dividir stores cuando la propiedad del estado sea clara.

## 26. Dependencias globales y Proxies de configuración — Media

[frontend/src/application/ports/services.js:2](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/ports/services.js#L2); [frontend/src/application/services/appResources.js:4](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/services/appResources.js#L4)

Un registro mutable global suministra adaptadores y los Proxies resuelven configuración en cada acceso. Importar una función no revela las capacidades que necesita ni sus contratos; distintas instancias comparten ese registro.

**Orientación:** Preferir dependencias explícitas por caso de uso o una inyección acotada a cada aplicación; definir los contratos de los adaptadores.

## 27. Detalles HTTP en seis módulos de aplicación — Media

[frontend/src/application/modules/attendance.js:328](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/attendance.js#L328); [frontend/src/application/modules/clients.js:160](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/clients.js#L160); [frontend/src/application/modules/inventory.js:74](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/inventory.js#L74); [frontend/src/application/modules/memberships.js:91](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/memberships.js#L91); [frontend/src/application/modules/schedules.js:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/schedules.js#L1); [frontend/src/application/modules/store.js:28](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L28)

Estos módulos siguen construyendo URLs, verbos, cabeceras y JSON e interpretan ok/status/json de Response. Pasar fetch por backendGateway evita un import directo de infraestructura, pero no elimina el acoplamiento al transporte.

**Orientación:** Continuar el patrón ya introducido en usuarios y configuración: repositorios que reciben y devuelven datos de negocio.

## 28. Vistas Vue con demasiadas responsabilidades — Media

[frontend/src/presentation/views/ClientsView.vue:720](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/ClientsView.vue#L720); [frontend/src/presentation/views/StoreView.vue:715](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/StoreView.vue#L715); [frontend/src/presentation/views/TrainerRoutineMonitorView.vue:703](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/TrainerRoutineMonitorView.vue#L703); [frontend/src/presentation/views/AttendanceView.vue:435](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/AttendanceView.vue#L435)

Hay vistas de aproximadamente 1.665, 1.333, 1.174 y 1.111 líneas. Combinan formulario, validaciones, filtros, paginación, pagos, notificaciones, seguimiento y estilos. Los bloques script también son extensos; no se ha clasificado el problema únicamente por el tamaño del template.

**Orientación:** Extraer componentes por responsabilidad y composables de flujo con contratos claros, conservando la vista como composición.

## 29. Interfaz y estilos repetidos — Media

[frontend/src/presentation/views/LandingView.vue:356](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/LandingView.vue#L356); [frontend/src/presentation/views/NosotrosView.vue:163](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/NosotrosView.vue#L163); [frontend/src/presentation/views/PreguntasFrecuentesView.vue:65](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/PreguntasFrecuentesView.vue#L65); [frontend/src/presentation/components/store/StoreMovementsPanel.vue:145](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/components/store/StoreMovementsPanel.vue#L145); [frontend/src/presentation/views/StoreMovementsPanelView.vue:88](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/StoreMovementsPanelView.vue#L88)

Se repiten bloques de footer/header, controles de paginación y estilos field-input. La proyección de movimientos de tienda también existe en una vista antigua y el componente actual. Corregir una copia no actualiza las demás.

**Orientación:** Compartir componentes de estructura, paginación y estilos; retirar o delegar las variantes antiguas después de comprobar sus usos.

## 30. Reglas de negocio dentro de componentes — Media

[frontend/src/presentation/components/inventory/InventoryMovementsPanel.vue:164](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/components/inventory/InventoryMovementsPanel.vue#L164); [frontend/src/presentation/views/TrainerRoutineMonitorView.vue:857](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/TrainerRoutineMonitorView.vue#L857); [frontend/src/presentation/views/ClientsView.vue:863](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/ClientsView.vue#L863)

Los componentes clasifican movimientos por el texto de su descripción, proyectan stock, gestionan progreso de ejercicios y mantienen sus propias interpretaciones de estados. La validación de UX es útil, pero duplicar las reglas con otras capas facilita divergencias.

**Orientación:** Mantener en componentes la interacción y extraer cálculos reutilizables y clasificación a dominio; coordinar acciones en aplicación.

## 31. Flujos local y remoto con reglas duplicadas — Media

[frontend/src/application/modules/clients.js:64](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/clients.js#L64); [frontend/src/application/modules/store.js:7](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L7); [frontend/src/application/modules/memberships.js:79](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/memberships.js#L79); [frontend/src/application/modules/synchronization.js:8](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/synchronization.js#L8)

Crear y actualizar varias entidades tiene una implementación local y otra remota, con distintos IDs y campos derivados. El ensamblaje habitual siempre usa un apiBase por defecto, pero ambas ramas siguen siendo mantenidas como parte del módulo.

**Orientación:** Determinar si el modo local es una capacidad necesaria; si lo es, implementarlo como otro adaptador que cumpla el mismo contrato y no como reglas duplicadas.

## 32. Modelos normalizados de formas distintas e IDs inventados — Media

[frontend/src/domain/utils/gymRules.js:182](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L182); [frontend/src/application/modules/clients.js:300](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/clients.js#L300); [frontend/src/domain/utils/gymRules.js:99](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L99)

Hay dos normalizadores de clientes con defaults distintos: uno admite cliente-* y estado por defecto ACTIVO; otro fabrica SGCLI* y usa EN_TRAMITE. Varios normalizadores usan Date.now cuando falta el ID del servidor. Eso puede presentar como válido un registro mal formado y complicar actualizaciones.

**Orientación:** Definir un modelo canónico por entidad, un mapeo único del contrato y errores explícitos cuando falten identificadores obligatorios.

## 33. Uso de || que sustituye valores cero válidos — Media

[backend/infrastructure/repositories/gym_repository.py:919](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L919); [frontend/src/domain/utils/gymRules.js:115](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L115); [frontend/src/application/modules/store.js:38](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L38)

stock_minimo=0 se transforma en 5 mediante or 5 en persistencia de productos. Hay equivalentes en cantidades, subtotales y valores guardados del frontend. Se confunden cero, ausencia y cadena vacía.

**Orientación:** Distinguir ausencia de valor válido con comprobaciones de None y operadores ??, según el contrato de cada campo.

## 34. Duplicación de acciones de autenticación — Baja

[frontend/src/application/stores/authStore.js:123](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/stores/authStore.js#L123); [frontend/src/application/stores/authStore.js:158](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/stores/authStore.js#L158)

signIn y signUp repiten validación de datos, normalización, actualización de varias referencias, revisión de sesión y almacenamiento. signUp tampoco tiene consumidores de producción más allá de su reexportación en el composable.

**Orientación:** Reutilizar una operación de establecer sesión y decidir si la acción de registro antigua sigue siendo parte del contrato necesario.

## 35. Errores del frontend silenciados o interpretados de forma desigual — Media

[frontend/src/application/modules/schedules.js:360](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/schedules.js#L360); [frontend/src/application/modules/store.js:61](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/application/modules/store.js#L61); [frontend/src/infrastructure/services/storeImageService.js:9](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/infrastructure/services/storeImageService.js#L9); [frontend/src/infrastructure/services/apiResponse.js:26](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/infrastructure/services/apiResponse.js#L26)

Numerosos refresh posteriores a mutaciones terminan en catch vacío. Un refresh fallido puede dejar relaciones o listados antiguos sin explicación específica. Imágenes usa response.text completo, mientras el cliente JSON extrae detail y evita presentar HTML de gateways. Los errores varían según el módulo.

**Orientación:** Definir la política de fallo parcial tras guardar y reutilizar un traductor de errores de transporte también para imágenes y multipart. No todos los catch vacíos son incorrectos: algunos de navegación/caché son deliberados.

## 36. Código y pantallas sin consumidores de producción — Baja

[frontend/src/presentation/views/ScheduleView.vue:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/ScheduleView.vue#L1); [frontend/src/presentation/views/StoreMovementsPanelView.vue:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/StoreMovementsPanelView.vue#L1); [frontend/src/presentation/views/InventoryMovementsView.vue:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/InventoryMovementsView.vue#L1); [backend/infrastructure/repositories/gym_repository.py:805](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/repositories/gym_repository.py#L805); [backend/infrastructure/security.py:40](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/infrastructure/security.py#L40)

No encontré imports o rutas hacia esas tres vistas. _map_user_legacy y _mutate_users no tienen llamadas en producción. getUserRole/get_user_role conservan la antigua regla del dominio de correo administrativo, aunque el flujo actual obtiene roles desde la cuenta. Hay además normalizeState y signUp sin uso productivo claro. Las reexportaciones de compatibilidad se han distinguido de este inventario y no se consideran automáticamente código sobrante.

**Orientación:** Confirmar consumidores externos y retirar, deprecar o documentar el contrato que se conserva; evitar que una regla antigua de permisos vuelva a utilizarse por accidente.

## 37. Comentarios y nombres que no explican la intención — Baja

[backend/domain/services/accounts_rules.py:105](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/accounts_rules.py#L105); [frontend/src/presentation/views/StoreView.vue:1180](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/StoreView.vue#L1180); [backend/domain/services/gym_values.py:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_values.py#L1)

Abundan comentarios genéricos como Procesa esta operación o Gestiona esta acción de la vista, y algunos encabezados conservan el nombre de otro módulo. Se mezclan inglés y español y nombres heredados con conceptos nuevos. El ruido dificulta localizar la explicación de invariantes importantes.

**Orientación:** Conservar comentarios sobre decisiones y restricciones, eliminar los que repiten el nombre del método y acordar un vocabulario por contrato.

## 38. Pruebas acopladas a internals y huecos en contratos — Media

[backend/tests/test_supabase_refresh.py:17](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/tests/test_supabase_refresh.py#L17); [backend/tests/test_promocion_cupos.py:6](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/tests/test_promocion_cupos.py#L6); [frontend/tests/23-layer-boundaries.test.js:20](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/tests/23-layer-boundaries.test.js#L20)

Varias pruebas construyen objetos con __new__, escriben state/lock y llaman métodos privados. Las pruebas de arquitectura revisan imports y algunas sustituciones, pero no prueban todas las responsabilidades. Los fallos de mapeo, autorización y borrado descritos arriba no están impedidos por la suite existente; pasar las pruebas no demuestra esos contratos.

**Orientación:** Añadir pruebas de autorización, ida y vuelta de campos y fallos remotos sobre APIs públicas, usando fakes de puertos. Reducir la dependencia de atributos privados al refactorizar esas pruebas.

## 39. CI solo después de fusionar a main — Media

[.github/workflows/ci-cd.yml:3](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/.github/workflows/ci-cd.yml#L3)

El único evento del workflow es pull_request closed sobre main, condicionado a merged=true. Un PR abierto hacia develop no obtiene por este archivo la verificación de pruebas antes de ser fusionado. Es una política explícita en sus comentarios, pero deja ese control tardío.

**Orientación:** Separar validación previa en PR de despliegue posterior; valorar el cambio de política sin activar despliegues en ramas de trabajo.

## 40. Migraciones con identificadores ambiguos y referencias desactualizadas — Media

[backend/migrations/009_admin_client_stripe.sql:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/migrations/009_admin_client_stripe.sql#L1); [backend/migrations/009_add_store_order_payment_fields.sql:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/migrations/009_add_store_order_payment_fields.sql#L1); [backend/migrations/008_enlazar_tienda_inventario_rollback.sql:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/migrations/008_enlazar_tienda_inventario_rollback.sql#L1); [backend/domain/services/gym_values.py:26](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_values.py#L26)

Dos migraciones distintas comparten 009 y los rollback están en la misma carpeta que las migraciones hacia delante. Hay referencias a una migración 014 que no está en el repositorio. Actualmente se indica ejecución manual, por lo que un glob SQL ingenuo o la interpretación por número sería peligroso.

**Orientación:** Definir un historial inequívoco y un procedimiento de aplicación/versionado que distinga reversión. No renumerar migraciones ya aplicadas sin un plan explícito.

## 41. Límite de imagen comprobado después de cargarla completa — Media

[backend/presentation/routes/store_routes.py:136](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/presentation/routes/store_routes.py#L136); [backend/application/services/store_images_service.py:22](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/application/services/store_images_service.py#L22)

La ruta ejecuta await file.read() sin límite y solo después StoreImagesService comprueba len(data) contra 5 MB. El límite de negocio no acota esa asignación de memoria dentro de la aplicación. La política de extensiones también existe en más de un adaptador.

**Orientación:** Leer como máximo el límite permitido más un byte o validar por streaming y mantener una política central de formatos. No se ha probado ni asumido la configuración de límites del proxy en producción.

## 42. Catálogos y políticas configurables repetidos como constantes — Media

[backend/domain/models/gym.py:40](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/models/gym.py#L40); [backend/domain/services/gym_domain_service.py:64](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/backend/domain/services/gym_domain_service.py#L64); [frontend/src/domain/utils/gymRules.js:7](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/domain/utils/gymRules.js#L7); [frontend/src/presentation/views/RegisterView.vue:1](https://github.com/KermitCortez8/AC-Silver-s-GYM/blob/b2fa5f6971cb52be050d3d1cd946a709a716cae0/frontend/src/presentation/views/RegisterView.vue#L1)

Los nombres de los tres planes se repiten como Literal, semillas, opciones y mapas de duración. Servicios, roles y estados también se reconstruyen en distintos módulos y componentes. La API permite editar el catálogo, pero añadir un plan no modifica todas esas listas automáticamente.

**Orientación:** Distinguir políticas cerradas de catálogos editables y obtener estos últimos de una fuente única; reutilizar constantes o contratos para el vocabulario cerrado.

## Orden de intervención

Primero autorización, identidad de usuarios, persistencia de campos y eliminaciones fallidas. Después revisar sesión, dinero, tiempo y consistencia transaccional. La reducción de clases/vistas y la retirada de código antiguo deben apoyarse en esos contratos para conservar comportamiento.
