# Pruebas y evidencia

Seguir el [DoD](../../docs/DoD.md) y las pruebas enlazadas desde el módulo afectado.

- Reutilizar pruebas existentes y añadir regresión cuando cambie una regla.
  Ejecutar las comprobaciones proporcionales al alcance, sin afirmar ejecuciones omitidas.
- Documentación: `python .specify/.codex/hooks/validate.py`.
- Flujo SDD, ajustes, scripts o hooks: `python .specify/.codex/hooks/validate.py` y `python -B -m unittest discover -s .specify/tests -v`.
- Backend: `(cd backend && python -m pytest tests/ -q)` y
  `(cd backend && python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics)`.
- Frontend: `(cd frontend && npm test)` y `(cd frontend && npm run build)`.
- Edge Function: `deno check supabase/functions/schedule-emails/index.ts` y
  `deno test supabase/tests/`.
- Usar los targets Docker `test` cuando se compruebe en contenedores; los comandos
  están en la [guía práctica](../../guias/guia-spec-driven-chatbot.md).
- PostgreSQL requiere un contenedor desechable explícito según DoD; su fixture
  modifica tablas. Registrar omisiones cuando no esté preparado.
- Cambios de UI requieren evidencia visual propia; arranque saludable o build
  no prueban por sí solos el comportamiento de pantalla.
- Los checks y hooks de etapa comprueban artefactos y trazabilidad; las suites
  del producto comprueban comportamiento. Registrar ambos por separado.
