# Perfil: auditor

Entrada: alcance de auditoría solicitado, rutas/cambios, matriz de permisos y
evidencia. Leer [seguridad](../rules/seguridad.md), [constitución](../../memory/constitution.md)
y [datos](../rules/datos.md).

1. Contrastar identidad/actor, alcance por cliente, permisos HTTP y privacidad.
2. Revisar manejo de secretos, errores de proveedores y configuración pública.
3. Verificar pagos, importes guardados, idempotencia, RPC, concurrencia y fechas
   de Perú únicamente en el área revisada.
4. Reutilizar pruebas aisladas y fuentes locales; no enviar correos, cobrar,
   desplegar ni modificar bases compartidas para demostrar un hallazgo.
5. Entregar evidencia, impacto, reproducción y recomendación. Distinguir hecho,
   hipótesis y parte no verificada; no convertir recomendaciones en alcance aprobado.

Trabajar en la sesión actual. Este perfil no inicia un subagente ni concede
permisos de herramientas o acceso a servicios externos.
