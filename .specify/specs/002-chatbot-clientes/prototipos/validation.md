# Validación de Specs y prototipos

Fecha: 2026-11-03. Alcance: documentos y demostración local independiente.
La integración productiva del chatbot sigue pendiente.

## Resultado ejecutado

- Chromium/Playwright: **18 comprobaciones aprobadas**, cero errores JavaScript,
  cero llamadas de API y cero peticiones a proveedores externos.
- **16 capturas**: 13 de escritorio a 1440×1000 y tres de móvil a 390×844.
  Captura de página completa; no se detectó desbordamiento horizontal en móvil.
- Navegación verificada también abriendo `index.html` como archivo local,
  sin servidor o dependencias instaladas por el usuario.
- Revisión visual propia de confirmación en escritorio y planes en móvil.
- Exportación de un PDF de **26 páginas** con los siete componentes de la Spec, tres ECU y capturas.
  Se comprobó por extracción de texto que cada ECU contiene sus alternativas y trazabilidad.
- Sintaxis JavaScript y validador documental comprobados durante la entrega.
- Prerrequisitos de la feature correctos y 13 pruebas del flujo documental aprobadas.

La revisión cubre formularios y límites 50/8/9, mensaje 150 sin contador, consulta,
acceso simulado, cuenta pendiente/vencida, confirmación explícita, doble clic,
cupo agotado, reconciliación local, limpieza al salir y ayuda sin IA.

Evidencia: [resultados.json](resultados.json), [capturas](capturas/),
[script de revisión](revision.cjs) y [PDF](Specs-y-prototipos-chatbot.pdf).

## Reproducción

Abrir `index.html` directamente para usar la demostración.
Para repetir la revisión automatizada, instalar Playwright fuera del repositorio
y servir esta feature con `python -m http.server 8768 --directory .specify/specs/002-chatbot-clientes`.
Ejecutar `revision.cjs` con `NODE_PATH` apuntando a la instalación de Playwright y,
si hace falta, `CHROMIUM_EXECUTABLE` apuntando al Chromium disponible.

`python generar-laminas.py` reconstruye las láminas desde Spec, ECU y capturas.
`exportar-pdf.cjs` exporta el PDF usando el mismo navegador. Los scripts reciben
URLs por `PROTOTYPE_BASE_URL` / `PROTOTYPE_REPORT_URL` cuando se usa otro puerto.

## Límites de la evidencia

Son comprobaciones de navegación de un prototipo con respuestas fijas.
No verifican comprensión real de IA, permisos de servidor, autenticación,
pagos, persistencia, cupos concurrentes o presupuesto distribuido.
No se declara ejecutada una prueba de aceptación del producto ni una UAT con
el profesor/usuarios. La matriz de revisión sirve para recoger esa validación.
No se modifica el frontend/backend, no se publica el prototipo y no se altera el PR.

## Actualización: programación asociada

Se relacionaron las pantallas con PG01–PG05 y se añadió el alcance de código
local frente a integración posterior. Se regeneraron las 16 capturas y se
repitieron las 18 comprobaciones de navegación, todas aprobadas, sin errores
JavaScript ni llamadas API. El PDF incorpora las cinco tareas de programación.
