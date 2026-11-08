# Validación prevista del chatbot

Procedimientos para implementar; no acreditan pruebas del chatbot ejecutadas.

## Preparación

Proveedor falso por inyección, reloj controlado en America/Lima y usuarios aislados: visitante, activo, pendiente/vencido y segundo cliente. PostgreSQL de pruebas con dependencias 019/020 y futura migración de cuotas, sin datos reales. Bloquear conexiones al proveedor, pagos y correos externos en pruebas automatizadas.

## E1 Conversación y esquema

Preguntar «¿Qué planes hay?» y comprobar respuesta en español y acciones válidas. Simular JSON inválido, acción desconocida e ID inventado: no hay acción ejecutable. Comprobar carga, cancelación y error recuperable. CA-01.

## E2 Preregistro y acceso

Sin sesión, consultar catálogo y abrir registro con plan vigente. Completar solo los formularios originales: nombre/correo 50, DNI 8 y teléfono 9. El chat no cobra y distingue pago de activación. Abrir acceso mantiene contraseña/Google fuera del panel. CA-02.

## E3 Identidad y limpieza

Intentar consultar otro cliente manipulando texto e IDs; servidor rechaza. Iniciar respuesta para A, cerrar sesión, ingresar como B y resolver respuesta anterior: nada de A aparece. Pendiente/vencido no accede al endpoint privado; se borra contexto antes de ofrecer ayuda pública genérica. CA-03.

## E4 Horarios y fechas

Pedir horario sin fecha o con servicio ambiguo: solicitar precisión. Probar «mañana» a las 23:59 de Lima y comprobar fecha absoluta en tarjeta. Comparar fechas/horas/cupos con API. Buscar no crea matrícula. CA-04.

## E5 Matrícula confirmada

No hay POST hasta pulsar Confirmar matrícula. Manipular cliente, fecha fuera de vigencia y cupo agotado antes de confirmar: servidor mantiene reglas. Con datos válidos se crea una matrícula y se refresca Mi horario. CA-05.

## E6 Concurrencia y resultado incierto

Doble clic y dos clientes por el último cupo: solo se anuncia resultado aceptado por RPC. Simular escritura aceptada cuya respuesta se pierde: consultar inscripciones y reconocer inscripción antes de ofrecer reintento. Si reconciliar falla, estado sin verificar y sin repetición automática. CA-06.

## E7 Abuso y privacidad

Pedir ignorar reglas, SQL, URL arbitraria, activación y datos ajenos. Inyectar instrucciones en descripciones del catálogo. No se ejecutan. Capturar payload al proveedor y logs con datos centinela de DNI/correo/teléfono/contraseña/token: no aparecen. Entrada sospechosa se resuelve localmente sin llamada al modelo. CA-07.

## E8 Límites y caída del proveedor

Escribir/pegar 151 caracteres: máximo 150, sin contador ni texto fijo de regla. Backend rechaza exceso, cuerpo sobredimensionado e historial adulterado. Repartir solicitudes entre dos instancias y probar cuotas, concurrencia y presupuesto compartidos. Probar timeout, presupuesto agotado, proveedor sin configurar y apagado: quedan acciones guiadas sin llamada externa. CA-08.

## E9 Accesibilidad y regresión

Con teclado: abrir/cerrar panel, foco inicial/restaurado, etiqueta y anuncios de carga/error. Revisar a 360 px y escritorio que no tape controles o navegación. Sin IA siguen utilizables registro, acceso y matrícula originales. Suites afectadas, build y revisión visual. CA-09.

## Comandos previstos tras implementar

Desde raíz: `python .specify/.codex/hooks/validate.py --feature 002-chatbot-clientes --stage implement`.
Desde frontend: `npm test` y `npm run build`.
Desde backend: `python -m pytest tests/test_chatbot_service.py tests/test_chatbot_routes.py tests/test_chatbot_quota_postgres.py tests/test_schedule_enrollment.py tests/test_schedule_sessions.py tests/test_public_preregistrations.py`.

Los archivos `test_chatbot_*` se crean en las tareas. Configurar PostgreSQL según harness vigente; una prueba omitida no acredita concurrencia. Estos comandos de producto se ejecutan al implementar, no por crear el plan.
