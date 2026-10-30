# Seguridad y límites de acceso actuales

Las fuentes son [dependencies.py](../../../backend/presentation/dependencies.py),
las rutas por módulo y los servicios de autenticación y pagos. La matriz refleja
dependencias HTTP; no debe inferirse autorización desde menús visibles.

## Matriz de acceso

| Operación | Acceso observado |
| --- | --- |
| Consultar planes, promociones, catálogo de tienda/imágenes y horarios públicos | Público. |
| Registro público, Google, contraseña y confirmación de retorno de pago | Endpoints públicos con validaciones propias de identidad/pago. |
| Clientes, pagos de membresía, planes editables, horarios editables, inventario, usuarios internos, resumen y configuración | `admin` o `staff`. |
| Crear, editar o borrar promociones | Solo `admin`. |
| Registrar/corregir/anular asistencia y consultar resumen/DNI de asistencia | Solo `admin`. |
| Leer asistencia e historial/exportación | `admin` o `user`; `user` limitado a sí mismo y sin auditoría interna. |
| Matrículas | `admin`, `staff`, `user`; el último opera sobre su identidad de sesión. |
| Rutinas y seguimiento en `/trainer` | `admin`, `staff`, `trainer`. |
| Pedidos y membresías consultables | Personal autorizado ve el conjunto; otras sesiones quedan filtradas por cliente vinculado. |
| Crear productos, subir imágenes y cambiar estado de pedidos | `admin` o `staff`. |

## Sesión e identidad

La API exige Bearer válido y vuelve a resolver la cuenta mediante
[AuthService](../../../backend/application/services/auth_service.py). Desactivar una
cuenta interna revoca su acceso aunque el token todavía no haya expirado.
Google se verifica en el servidor; una vinculación requerida se informa como
conflicto. El cliente necesita activación y membresía pagada/vigente para el acceso
que controla el servicio. Los usuarios internos no requieren membresía.

Las claves privadas de Supabase, Stripe y Resend permanecen fuera del frontend.
Los valores `VITE_*` se incluyen en la compilación pública; no colocar allí
claves de servicio. Los archivos de entorno reales quedan ignorados por Git.

## Datos y pagos

- Derivar el cliente y el actor desde la sesión en operaciones de autoservicio,
  movimientos y progreso. No confiar en identificadores enviados para suplantarlos.
- Filtrar historial en persistencia. Un filtro de DNI no amplía el alcance de
  una sesión de cliente ni revela auditorías administrativas.
- Verificar firma del webhook con el cuerpo original, sesión, importe,
  metadatos y modo de Stripe. El retorno del navegador no acredita un pago por sí solo.
- No reactivar membresías vencidas por confirmaciones duplicadas ni extender
  fechas por volver a activar una membresía ya activa.
- Mantener las RPC privadas de transacción accesibles solo a `service_role`;
  conservar las RPC especializadas y sus reglas de concurrencia.

## Imágenes y correo

Las subidas de tienda requieren personal autorizado y validan extensión, MIME,
archivo no vacío y límite de 5 MiB. Se admiten JPEG, PNG, WebP y GIF; se pueden
listar SVG históricos, pero no subir SVG nuevos. La validación actual no es
un análisis antivirus ni una decodificación completa del archivo.

Los errores de proveedores no deben exponer respuestas con credenciales o datos
personales. Un envío solo se marca entregado cuando el proveedor devuelve su ID.
La función de recordatorios tiene configuración privada y validación propia;
su despliegue/configuración no se demuestra por tener su código en el repositorio.

## Evidencia

Reutilizar [test_priority_fixes.py](../../../backend/tests/test_priority_fixes.py),
[test_review_regressions.py](../../../backend/tests/test_review_regressions.py),
[test_scoped_operations.py](../../../backend/tests/test_scoped_operations.py),
[test_stripe_confirmation.py](../../../backend/tests/test_stripe_confirmation.py),
[test_store_images.py](../../../backend/tests/test_store_images.py) y
[test_resend_email.py](../../../backend/tests/test_resend_email.py) según el alcance.
Los documentos de auditoría registran problemas y correcciones históricas;
no son una declaración de ausencia de vulnerabilidades.

## Configuración de Codex y herramientas

Los permisos efectivos de herramientas, red y sandbox pertenecen al entorno de
Codex. `.specify/.codex/settings.json` declara reglas y verificaciones; no concede
permisos ni cambia el modelo. Las preferencias de `AGENTS.local.md` no deben
contener credenciales, tokens ni datos personales reales.
