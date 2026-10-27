# Decisiones del piloto

## R-01 — Integración oficial y versión reproducible

**Decisión:** usar GitHub Spec Kit 1.2.3, fijado al commit oficial de esa release,
con integración Codex en modo skills y scripts Bash.
**Motivo:** respeta el entorno actual y ofrece plantillas, scripts y proceso SDD
sin añadir dependencias de ejecución a Vue o FastAPI.
**Alternativas:** solo Markdown manual, o adoptar otra herramienta. Se elige
Spec Kit por la solicitud explícita del usuario.

Fuentes: [instalación oficial](https://github.com/github/spec-kit/blob/v1.2.3/docs/installation.md)
y [release fijada](https://github.com/github/spec-kit/releases/tag/v1.2.3).
La inicialización se ensayó en `/tmp` antes de ejecutarla sobre el repositorio.

## R-02 — Adopción en la aplicación existente

**Decisión:** reutilizar el piloto `001-control-errores` y los IDs `ERR-*`.
**Motivo:** ya hay reglas documentadas y pruebas por módulo. Permite aprender el
proceso sin reescribir la aplicación ni duplicar pruebas.
**Alternativa:** especificar retrospectivamente todos los módulos; queda descartada
por su amplitud y por no aportar aceptación al próximo cambio concreto.

## R-03 — Cancelación de una escritura

**Decisión:** ERR-009 conserva `request_cancelled`, evita enviar si la señal ya
estaba cancelada y marca resultado incierto si la cancelación llega tras invocar
el transporte de una escritura.
**Motivo:** cancelar la espera del cliente no garantiza deshacer una operación
en el servidor. El aviso debe permitir consultar su estado antes de repetir.
**Alternativas:** tratar toda cancelación como fallo definitivo, o introducir
idempotencia en todos los endpoints. La primera no refleja la incertidumbre;
la segunda necesita un cambio separado de mayor alcance.
**Estado:** decisión de diseño definida; implementación y regresiones pendientes
en T013 y T014. No se presenta como comportamiento ya implementado.

## R-04 — Evidencia y alcance de esta entrega

**Decisión:** registrar la instalación y las pruebas ejecutadas por separado de
la aceptación total del piloto.
**Motivo:** la existencia de una suite o un resultado histórico no demuestra
todos los escenarios nuevos, permisos reales ni accesibilidad visual.
**Estado:** resultados y brechas en `verification.md`; trabajo pendiente en
`tasks.md`. Sin migraciones, endpoints ni entidades persistentes nuevas.
