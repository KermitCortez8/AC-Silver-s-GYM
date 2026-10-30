# Implementation Plan: Control del flujo de clientes

**Feature:** `001-control-flujo-clientes` · **Fecha:** 2026-10-29.
**Spec:** [spec.md](spec.md). **Contexto consultado:** [context.md](context.md).

## Summary

Corregir éxito falso de borrado, edición destructiva de membresías, sustitución de importe
cero, horarios inválidos y aceptación de fechas inválidas en asistencia. Añadir recorrido
integrado y conservar los controles existentes de registro, activación, cupos y privacidad.

## Technical Context

Python/FastAPI/Pydantic y Vue 3/Vite/Pinia actuales. Persistencia mediante comandos y
RPC existentes. LocalGymService y dobles de proveedores en pruebas; no servicios reales.
Se corrigen estados y acciones de las pantallas existentes, conservando dependencias. Los errores reutilizan el traductor HTTP global.

## Constitution Check

- [x] I: siete componentes y contexto completados antes del plan.
- [x] II: conservar capas, usar membership_current y validadores compartidos.
- [x] III: validar dentro de comandos, conservar recursos y RPC sin escritura parcial.
- [x] IV: conservar permisos y privacidad con suites de HTTP e identidad.
- [x] V: conservar importes guardados, activación independiente y reloj de Perú.
- [x] VI: regresiones, integración, suites y omisiones explícitas.
- [x] VII: actualizar MOD-02, MOD-03, MOD-05 y MOD-06.

## Project Structure

- `backend/application/services/clients_service.py`: propagar error de borrado y validar importe guardado.
- `backend/domain/services/memberships_rules.py`: proteger edición y confirmación económica.
- `backend/domain/services/schedules_rules.py`: día válido y horas canónicas al guardar.
- `backend/application/services/attendance_service.py`: usar vigencia compartida.
- `backend/tests/test_client_flow_control.py`: regresiones e integración.
- `.specify/base/modulos/`: contratos afectados.

## Diseño del cambio

1. Borrado: parsear identificador válido y ejecutar el comando sin capturar fallos.
2. Membresía: identificar registro existente dentro del comando; rechazar cambio de dueño
   o edición de una compra pagada/activa/vencida. Una pendiente conserva pago pendiente
   y fechas vacías; el alta existente mantiene sus reglas.
3. Pago: precio de plan solo cuando importe falta o es null en registros históricos;
   cero guardado nunca se reemplaza. No crear flujo de compra gratuita.
4. Horarios: exigir día semanal válido; validar toda la hora, conservar formatos históricos
   de AM/PM y guardar HH:MM; admitir segundos cero, rechazar segundos no cero.
5. Asistencia: membership_current valida fechas reales, pago y vigencia inclusiva.
6. Integración: alta, reintento, pago, activación, matrícula, cupo lleno, asistencia,
   salida, cancelación y vencimiento con reloj fijo y datos sintéticos.

## Datos y migraciones

Sin cambios de esquema o migraciones. Preservar entidad, propietario y metadatos de pago.
Persistencia atómica y RPC actuales no se sustituyen ni se modifican.

## Verificación y trazabilidad

| Criterio | Prueba / archivos | Resultado esperado |
| --- | --- | --- |
| CA-01 | test_admin_client_payment.py y test_client_flow_control.py | Reintento sin duplicación y sin suplantación |
| CA-02 | test_client_flow_control.py / clients_service.py | Error HTTP 503 y 400 sin éxito falso |
| CA-03 | test_client_flow_control.py / memberships_rules.py | Rechazo sin mutación de compra |
| CA-04 | test_client_flow_control.py / clientes y membresías | Cero no convertido a precio actual |
| CA-05 | test_client_flow_control.py / schedules_rules.py | Día válido y hora compatible con asistencia |
| CA-06 | test_client_flow_control.py / attendance_service.py | Fechas inválidas no conceden acceso |
| CA-07 | test_client_flow_control.py y suites completas | Recorrido y controles existentes pasan |

## Complexity Tracking

Sin excepciones. PostgreSQL depende de Docker desechable disponible; las pruebas locales
no acreditan Stripe, Google, Resend o Supabase reales. Ver [research.md](research.md),
[data-model.md](data-model.md), [contrato](contracts/control.md) y [quickstart.md](quickstart.md).

## Ampliación de corrección en frontend

La revisión adicional solicitada por el usuario incorpora PaymentView, el composable
useClientMembershipActions, ClientsView y ClientDetailsDialog. La pantalla de retorno
mostrará error/pendiente como estados terminados y permitirá volver a consultar la misma
sesión sin iniciar otro cobro. Validará el cliente devuelto por servidor y descartará
respuestas de rutas anteriores. El pago manual se bloquea mientras está en curso;
tras activar se actualizan los detalles del cliente con la respuesta confirmada.
Pruebas de regresión en frontend/tests/36-client-flow-control.test.js y capturas en
navegador con API simulada. Se mantienen los servicios y el tema actuales.
