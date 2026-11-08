# Revisión conjunta de Specs y prototipos

Entrega: diseño del chatbot de AC Silver's GYM, 2026-11-03.
Estado: especificación y prototipado para revisión. Integración productiva pendiente.

## Material para la revisión

1. [Spec del chatbot](spec.md): historias, criterios, reglas y casos borde.
2. [Tres casos de uso y ECU](casos-de-uso.md): actores, precondiciones, flujos, alternativas y postcondiciones.
3. [Prototipo navegable](prototipos/index.html): Specs resumidos y pantallas en una misma vista.
4. [Plan técnico](plan.md) y [desglose de implementación](tasks.md).
5. [Cinco tareas de programación y su relación con los prototipos](programacion-prototipos.md).

## Formatos de entrega

- [Demostración navegable](prototipos/index.html): tres recorridos, Specs visibles y escenarios alternativos.
- [Láminas con Specs, ECU y capturas](prototipos/laminas.html): lectura e impresión desde el navegador.
- [PDF para compartir](prototipos/Specs-y-prototipos-chatbot.pdf): Spec completa, tres ECU, cinco tareas de programación y 16 capturas.
- [Capturas PNG originales](prototipos/capturas/): 13 de escritorio y tres de móvil.
- [Resultado de la revisión en navegador](prototipos/resultados.json) y [validación de la entrega](prototipos/validation.md).

Abrir `prototipos/index.html` directamente en un navegador; no requiere instalar
dependencias ni conectarse a servicios. Todo el contenido de negocio es de ejemplo.
La demostración no guarda información en la base, no cobra y no inicia sesiones reales.

## Relación entre pantallas y criterios

| Pantalla | Caso de uso | Qué revisar | Criterios de la spec |
| --- | --- | --- | --- |
| P01 · Planes y bienvenida | CU-CHAT-01 / US1 | Pregunta libre, ayuda y selección de plan | CA-01, CA-02 |
| P02 · Formulario de preregistro | CU-CHAT-01 / US1 | Datos fuera del chat, límites y validación | CA-02, CA-07, CA-08 |
| P03 · Continuidad del preregistro | CU-CHAT-01 / US1 | Distinguir solicitud, pago y activación | CA-02 |
| P04 · Acceso | CU-CHAT-02 / US2 | Uso del formulario, no de la conversación | CA-03, CA-07 |
| P05 · Cuenta no habilitada | CU-CHAT-02 / US2 | Activación pendiente o membresía vencida | CA-03 |
| P06 · Panel de cliente | CU-CHAT-02 / US2 | Acciones propias y limpieza al salir | CA-03 |
| P07 · Búsqueda de horarios | CU-CHAT-03 / US3 | Servicio y fecha concretos, resultados | CA-04 |
| P08 · Revisión de matrícula | CU-CHAT-03 / US3 | Resumen y confirmación humana separada | CA-05 |
| P09 · Matrícula simulada | CU-CHAT-03 / US3 | Resultado, inscripción única y Mi horario | CA-05, CA-06 |
| P10 · Cupo agotado o resultado incierto | CU-CHAT-03 / US3 | Rechazo realista y reconciliación sin reenvío automático | CA-06 |
| Estado transversal · Ayuda guiada | Los tres | Continuar cuando la IA no está disponible | CA-08, CA-09 |

Esta tabla identifica cobertura del diseño. No marca los CA como aprobados en producción.

## Orden de las ocho tareas acordadas

| Orden | Tarea | Entrega revisable |
| --- | --- | --- |
| 1 | Caso de uso y ECU de preregistro | CU-CHAT-01 y P01–P03 |
| 2 | Caso de uso y ECU de acceso | CU-CHAT-02 y P04–P06 |
| 3 | Caso de uso y ECU de horarios/matrícula | CU-CHAT-03 y P07–P10 |
| 4 | PG01 · Programar las reglas de control | Permisos, privacidad, alcance, límites y pruebas de servidor |
| 5 | PG02 · Integrar IA en backend | Proveedor/modelo y herramientas restringidas |
| 6 | PG03 · Programar interfaz | El prototipo sirve de referencia para construir panel y tarjetas reales |
| 7 | PG04 · Conectar preregistro y acceso | Integración con servicios y formularios existentes |
| 8 | PG05 · Conectar horarios y matrícula | Consultas reales, confirmación, concurrencia y pruebas completas |

Las primeras tres tareas tienen sus ECU documentadas. El prototipo es un avance
de diseño de la interfaz, no la finalización de las cinco tareas de programación.
Las 24 tareas técnicas de `tasks.md` mantienen el desglose necesario para realizarlas.

## Guion para mostrar al profesor

1. Seleccionar «Preregistro», consultar los planes y abrir el formulario. Mostrar la ECU y los CA relacionados en el panel izquierdo.
   Relacionar la barra «Programación asociada» con PG01–PG04 y explicar qué se simula y qué se conectará después.
2. Continuar hasta el estado de solicitud de ejemplo y explicar por qué pagar no activa automáticamente la cuenta.
3. Abrir «Acceso», probar los escenarios «Cuenta pendiente» y «Membresía vencida» y volver a «Flujo normal».
4. Simular el ingreso y abrir «Horarios y matrícula». Seleccionar servicio/fecha, revisar la tarjeta y confirmar con el botón.
5. Reiniciar el caso y probar «Cupo agotado» y «Respuesta perdida». Mostrar que una propuesta no es una inscripción y que no hay reintento automático.
6. Probar «IA no disponible»: los botones mantienen el recorrido guiado.

Frase de presentación: «Traemos las Specs y las ECU del chatbot junto con un
prototipo navegable. Queremos validar el recorrido, las reglas y las alternativas
antes de conectar la IA y los servicios reales».
