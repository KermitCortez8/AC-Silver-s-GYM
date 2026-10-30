# Verificación local

Desde backend, con dependencias de requirements-dev.txt instaladas:

```bash
python -m pytest tests/test_client_flow_control.py tests/test_admin_client_payment.py -q
python -m pytest tests/ -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

Desde frontend: `npm test` y `npm run build`. Desde raíz: validador documental,
hook de cierre de esta feature y unittest de .specify/tests. PostgreSQL solo en contenedor
desechable según DoD; ninguna prueba se ejecuta contra Supabase real.
