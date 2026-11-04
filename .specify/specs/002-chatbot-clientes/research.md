# Decisiones de diseño sobre la base consultada

Fecha: 2026-11-03. Investigación del repositorio, no comparativa comercial de proveedores. Fuentes existentes en [contexto](context.md).

## Conversación IA y acciones guiadas

**Decisión:** puerto de proveedor, salida estructurada, herramientas enumeradas de lectura y acciones de UI separadas. La matrícula solo se envía por confirmación humana usando la capacidad existente.

**Motivo:** el usuario eligió expresamente conversación con IA y reglas. Ya existen servicios para cada paso; el chatbot no necesita un segundo sistema de cobro, identidad o matrícula.

**Alternativas:** un bot solo de botones no cumple la elección. Un agente con herramientas generales o escritura autónoma no cumple el control solicitado. Una base vectorial no aporta al catálogo pequeño y transaccional que ya consulta la aplicación.

## Identidad, preregistro y activación

**Decisión:** orientación pública y privada separadas. Login/Google, preregistro y retorno de pago siguen fuera de la conversación. El chat no habilita acceso a clientes pendientes/vencidos ni consulta solicitudes públicas por DNI/correo.

**Motivo:** `get_current_user` y las operaciones vigentes ya determinan elegibilidad y dueño. La creación efectiva del cliente tras pago y la activación son estados distintos.

**Alternativa:** dar al bot un acceso especial previo a activación cambiaría seguridad y contratos sin necesidad para acompañar el recorrido.

## Memoria y datos del proveedor

**Decisión:** memoria de pestaña, ocho mensajes depurados y limpieza por sesión. No guardar transcripciones. Quitar campos estructurados de identidad y pago; filtrar patrones de correo, DNI, teléfono, tarjeta y secretos antes de construir contexto. Una entrada sensible o dudosa se resuelve por guía local.

**Límite real:** ningún filtro de texto libre garantiza reconocer cualquier dato personal escrito de cualquier forma. No presentar el filtro como anonimización infalible. La revisión de privacidad de T001 debe evaluar las condiciones del proveedor; probar datos centinela y no enviar nunca los campos privados estructurados ni registros completos. La interfaz invita a usar formularios para datos personales.

**Alternativa:** historial persistente y almacenamiento de conversaciones aumentan alcance y no son necesarios para esta versión. No existe una promesa de continuidad entre dispositivos.

## Concurrencia y límites

**Decisión:** cuota compartida en Supabase mediante tabla/RPC técnica con reserva previa, permisos exclusivos backend y coste máximo por llamada. Mantener la RPC actual de matrícula y reconciliar resultados inciertos.

**Motivo:** un contador del proceso no controla varias réplicas; una propuesta conversacional no garantiza disponibilidad al confirmar. Supabase ya está en la arquitectura, por lo que no hace falta añadir Redis para este incremento.

**Alternativas:** memoria solo para fake de pruebas; Redis requeriría otra infraestructura. Añadir una segunda escritura de matrícula o una reserva conversacional duplicaría las reglas existentes.

## Proveedor y presupuesto

**Decisión de planificación:** el diseño no depende de una marca. T001 selecciona proveedor/modelo y verifica en sus fuentes oficiales salida estructurada, límites de tokens, timeout/cancelación, tokenizer, costes, tratamiento/retención de datos y disponibilidad. Registrar elección y dependencia exacta en este documento antes de implementar el adaptador.

**Configuración obligatoria para habilitar:** proveedor/modelo, secreto backend, tarifas o cota de coste verificable y presupuesto diario positivo. Si faltan o no puede reservarse presupuesto, guía local. No se inventa una cifra monetaria ni se contrata un servicio en este encargo.

**Pruebas:** fake por inyección; ninguna suite depende de una clave o cuenta pagada. Una eventual prueba real pertenece a una ejecución futura explícita, no a la aceptación automática.
