# Arquitectura de AC Silver's GYM

El backend y el frontend se organizan en cuatro capas. Las reglas y los contratos
no importan implementaciones externas. Los puntos de ensamblaje conectan las
implementaciones con los servicios que las utilizan.

## Archivos `__init__.py`

Los archivos `__init__.py` identifican paquetes regulares de Python, como
`domain`, `application.services` o `infrastructure.repositories`. Python los
ejecuta al importar el paquete; pueden estar vacíos cuando no hay inicialización
que realizar. En este proyecto se mantienen vacíos de forma intencional para
evitar efectos secundarios y dependencias circulares durante los imports.

No son puntos de entrada del servidor ni necesitan importar todos los módulos
de su carpeta. El servidor arranca desde `app/main.py` y sus dependencias se
ensamblan en `app/bootstrap.py`. Python moderno también permite paquetes de espacio
de nombres sin `__init__.py`; aquí utilizamos paquetes regulares explícitos.

## Backend

| Capa | Ubicación | Responsabilidad |
| --- | --- | --- |
| Presentación | `backend/presentation/` | Rutas FastAPI, validación HTTP, permisos y traducción de errores. |
| Aplicación | `backend/application/` | Casos de uso, operaciones por módulo, contratos de repositorios, datos de lectura y coordinación de pagos y notificaciones. |
| Dominio | `backend/domain/` | Reglas de cuentas, membresías, promociones, asistencia, inventario, horarios y tienda, con sus modelos y contratos de contraseñas. |
| Infraestructura | `backend/infrastructure/` | Repositorios Supabase y memoria, transporte REST, seguridad, Stripe, Google, correo e imágenes. |

El ensamblaje está en `backend/app/bootstrap.py`. `app/main.py` conserva el punto
de entrada y `presentation/dependencies.py` conecta los servicios con FastAPI.
Las rutas obtienen sus adaptadores a través de este ensamblaje; las capas de
aplicación y dominio no importan infraestructura ni FastAPI.

```mermaid
flowchart LR
    API[Presentación: FastAPI] --> APP[Aplicación: casos de uso]
    APP --> DOM[Dominio: reglas por módulo]
    APP --> PORT[Contratos de repositorio e integraciones]
    INF[Infraestructura: Supabase, Stripe, Google y correo] -. implementa .-> PORT
    BOOT[app/bootstrap.py] -. conecta .-> APP
    BOOT -. construye .-> INF
```

### Reglas y persistencia

`GymDomainService` es un agregado en memoria compuesto por módulos de reglas:
`accounts_rules`, `memberships_rules`, `attendance_rules`, `inventory_rules`,
`schedules_rules`, `store_rules` y `dashboard_rules`. No lee archivos, guarda datos
ni consulta Supabase. Las contraseñas se procesan mediante `PasswordHasher`,
inyectado por la aplicación.

`GymService` coordina las operaciones de aplicación por módulo. El puerto recibe
comandos y consultas que declaran sus recursos mediante `Resource` y ejecutan
reglas a través de componentes explícitos. Las consultas y los resultados de comandos devuelven copias para evitar
que un consumidor modifique el estado persistido sin pasar por una operación.
Clientes y asistencia utilizan operaciones públicas y modelos de lectura en lugar
de acceder al estado, los bloqueos o los métodos privados de otro servicio.

`GymRepository` define las capacidades de lectura, cambio, refresco y operaciones
especializadas. `SupabaseGymRepository` y `MemoryGymRepository` implementan esas
capacidades mediante composición; no heredan del dominio.

Se conservan la caché y la detección diferencial de cambios. Las matrículas y
asistencias mantienen sus RPC específicas; una matrícula exige la RPC y nunca
recurre a un INSERT sin sus locks. Las demás mutaciones se confirman mediante
`commit_gym_transaction` (migración 015), incluyendo borrados y detalles de venta.
La RPC bloquea las tablas de los recursos declarados, comprueba que no cambiaron y confirma
todas las operaciones o ninguna. Ante un conflicto, el repositorio refresca y
recalcula las reglas, hasta tres intentos. No se usan compensaciones HTTP.

Los comandos de horarios y tienda declaran sus dependencias de lectura y escritura
por operación. Guardar una rutina necesita solamente el catálogo; matricular carga
clientes, membresías, catálogo, horarios de servicio y matrículas antes de ejecutar
su RPC. El resumen de asistencia usa conteos filtrados, visitas abiertas y ocho
entradas recientes; no materializa el historial cerrado. El historial conserva su
consulta paginada independiente.

`gym_identity_floors` combina los IDs actuales, las secuencias y una marca creciente
para evitar colisiones entre procesos y reutilización después de borrar. El código
visible del usuario se persiste en `codigo_usuario` y no cambia al modificar su rol.
La migración 016 concede a `service_role` los permisos sobre las secuencias que
necesitan esas RPC para consultar y avanzar identidades bajo `SECURITY INVOKER`.
Las RPC genéricas solo son ejecutables con `service_role`; no se exponen a usuarios
anónimos ni autenticados directamente. La migración 014 conserva los campos de
promociones, membresías, inventario y productos que ahora leen y escriben los mappers.

### Integraciones y compatibilidad

La verificación de Google, las sesiones firmadas, los pagos y los envíos de correo
se conectan mediante capacidades inyectadas. Los servicios de notificaciones
reciben explícitamente su repositorio de cola y su proveedor de envío; las
plantillas no dependen del transporte. El servicio de imágenes valida el archivo y
utiliza un adaptador de almacenamiento local o Supabase.

Los constructores históricos `SupabaseGymService` y `LocalGymService` se conservan
como fachadas de compatibilidad para consumidores y pruebas anteriores. Pueden
exponer los atributos internos antiguos, pero el ensamblaje de producción utiliza
`GymService` y los contratos públicos. No contienen una segunda implementación de
las reglas de negocio.

Los modelos Pydantic siguen siendo contratos de datos compartidos, no modelos ORM.
Las migraciones SQL y las pruebas permanecen en sus carpetas originales. El
procedimiento para las nuevas migraciones y la evidencia de las doce correcciones
están en [correcciones-prioritarias.md](correcciones-prioritarias.md).

## Frontend

| Capa | Ubicación | Responsabilidad |
| --- | --- | --- |
| Presentación | `frontend/src/presentation/` | Pantallas, componentes, navegación, estilos y aplicación visual del tema. |
| Aplicación | `frontend/src/application/` | Estado de Pinia, operaciones por módulo, sesión, sincronización, pagos, catálogo y contratos de adaptadores. |
| Dominio | `frontend/src/domain/` | Cálculos, normalización y validaciones de clientes, membresías, pagos, asistencia y calendarios. |
| Infraestructura | `frontend/src/infrastructure/` | HTTP, SDK de Google, configuración del entorno, almacenamiento de sesión y preferencias del navegador. |

`frontend/src/bootstrap.js` instala los adaptadores explícitamente para una
instancia de Pinia antes de montar Vue. `application/ports/services.js` los asocia
con su propietario mediante un `WeakMap`, impide reinstalarlos y conserva una copia
inmutable de la configuración. Los servicios capturan sus adaptadores y la sesión
de esa instancia al construirse. Instalar otra aplicación no redirige consumidores
existentes. Las pruebas pueden inyectar capacidades sin realizar solicitudes reales.
Las vistas utilizan servicios de aplicación con operaciones de catálogo, pagos,
asistencia e imágenes.

`gymStore.js` conserva su nombre y su interfaz pública como fachada de Pinia.
Las operaciones están separadas en `application/modules/`: clientes, membresías,
asistencia, inventario, horarios, usuarios, tienda, panel y sincronización. Los
módulos reciben contextos acotados con las referencias y capacidades que necesitan,
ensamblados en `application/services/gymModules.js`. Al cambiar o cerrar sesión
se vacían los datos de negocio y las cachés. `sessionStore` aporta una generación
independiente de HTTP y autenticación; los adaptadores de aplicación rechazan
respuestas de una generación anterior antes de publicar datos.

Los módulos reciben repositorios con operaciones que
devuelven datos (`save`, `remove` y `load`). Su transporte HTTP está en
`infrastructure/repositories/` y se conecta en `bootstrap.js`; los módulos
ya no construyen solicitudes ni interpretan respuestas HTTP. Sincronización recibe
su gateway al ensamblarse. La actualización de
usuarios reutiliza una única función de normalización e inserción o reemplazo.

Se retiró la función vacía `persist()` y sus llamadas: los cambios remotos siguen
guardándose mediante las operaciones del backend que ya existían. Los cambios
locales mantienen sus referencias reactivas de Vue.

Las transformaciones comunes viven en `domain/utils/gymRules.js` y las validaciones
de autenticación en `domain/utils/authRules.js`. El almacenamiento de sesión vive
en `infrastructure/services/sessionStorage.js`. El módulo anterior `authUtils.js`
reexporta las funciones para conservar la compatibilidad.

Los módulos de aplicación usan el contrato del backend; los detalles de transporte
se conectan desde infraestructura. Las vistas y las reglas no ejecutan `fetch`
ni acceden a `localStorage`. Los cálculos de calendarios tampoco dependen de las
utilidades de presentación.

Las vistas de clientes y tienda delegan formularios, pagos de membresía y selección
de imágenes en composables de presentación. Sus diálogos tienen componentes
propios. El registro de asistencia por código resuelve al cliente y reutiliza la
misma operación de registro por ID.

`TrainerRoutineMonitorView` ensambla búsqueda, asignaciones, progreso y descanso
mediante composables con capacidades explícitas. La asignación directa y la del
diálogo reutilizan el mismo guardado. Las fichas de matrícula, el historial y los
diálogos son componentes separados; un solo temporizador alimenta sus dos
representaciones. Los borradores de ejercicios y las confirmaciones de
desvinculación tienen selección independiente.

`AttendanceView` coordina pestañas y compone resumen, búsqueda, visitas generales,
horarios y salidas pendientes. `useAttendanceControl` coordina mutaciones y
refrescos; `useAttendanceLookup` descarta búsquedas reemplazadas. Los componentes
reciben datos y emiten acciones; no acceden al transporte. Los estilos de control
se comparten bajo `.attendance-page` para conservar su alcance tras la extracción.

## Límites actuales de la separación

La organización y las dependencias principales siguen las cuatro capas, pero
todavía existen decisiones que limitan su independencia:

- `GymService` y `gymStore` siguen siendo fachadas centrales de varios módulos.
  El dominio conserva un estado compartido internamente y métodos antiguos de
  compatibilidad; los registros de negocio siguen siendo diccionarios.
- La transacción general compara instantáneas completas de cada recurso elegido
  y bloquea tablas. Acotar los recursos reduce conflictos ajenos, pero no aporta
  concurrencia por fila ni elimina el coste de cargar una tabla seleccionada.
- Clientes, membresías y pedidos todavía tienen consultas que devuelven listas
  completas. La paginación de asistencia y su resumen especializado no equivalen
  a paginación uniforme de toda la API.
- Los módulos del frontend conservan coordinación explícita detrás de una fachada
  de Pinia. Las vistas de clientes y tienda son más pequeñas, pero aún reúnen
  listados, filtros y acciones; otras pantallas extensas requieren revisión propia.

Las pruebas de imports comprueban dependencias entre capas; por sí solas no
demuestran que todas las responsabilidades estén completamente separadas.
La evaluación de los objetivos y su evidencia se recoge en
[revision-refactorizacion.md](revision-refactorizacion.md).

## Compatibilidad y verificación

Se mantienen los endpoints, los esquemas públicos de la API, las pantallas, las
claves de sesión, los nombres de variables de entorno y las rutas públicas de
imágenes. La ubicación predeterminada de las imágenes sigue siendo
`backend/db/store-images` y `/app/db/store-images` dentro de Docker.

Además de las pruebas funcionales existentes, las pruebas de arquitectura
comprueban las direcciones de importación, la sustitución de proveedores y la
ausencia de herencia entre persistencia y dominio. Se verifican también la
protección de los datos devueltos, los errores de persistencia, la liberación de
stock pendiente y la validación y publicación de imágenes.

Los comandos de desarrollo conservan su forma:

```bash
cd backend
python -m app.main
```

```bash
cd frontend
npm run dev
```

Para verificar los cambios:

```bash
cd backend
python -m pytest tests/ -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

```bash
cd frontend
npm test
npm run build
```

Los Dockerfiles incluyen los cuatro paquetes y los módulos nuevos. Los targets
`test` permiten ejecutar las mismas comprobaciones sin credenciales de producción.
