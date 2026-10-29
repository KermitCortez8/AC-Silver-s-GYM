# Backend y contratos HTTP

Consultar [arquitectura](../../docs/arquitectura.md), [seguridad](seguridad.md)
y el [contrato del módulo](../../base/modulos/README.md).

- Presentación conserva rutas, esquemas, permisos y traducción de errores.
- Aplicación coordina casos de uso y contratos; dominio mantiene reglas.
  Aplicación y dominio no importan FastAPI ni implementaciones de infraestructura.
- Conectar adaptadores en `app/bootstrap.py` y dependencias de presentación;
  reutilizar `GymService`, servicios por módulo y puertos existentes.
- Conservar contratos públicos y sus pruebas. Una operación que cambia datos
  declara recursos y utiliza el mecanismo atómico que le corresponde.
- Mantener autenticación y alcance de datos en servidor, incluso para nuevas
  interfaces o integraciones. Actualizar el documento del módulo al cambiar un contrato.
