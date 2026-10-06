# Scripts manuales del backend

Estos scripts conservan las comprobaciones manuales que estaban en la raíz de
`backend/`. No forman parte de la suite de pytest y solo se ejecutan al invocarlos
directamente. Importarlos no inicia las comprobaciones.

Desde `backend/`:

```bash
python tests/manual/fetch_memberships.py
python tests/manual/insert_membership.py
python tests/manual/register_client.py
```

Los imports se resuelven respecto a la ubicación del script, por lo que también
pueden ejecutarse desde la raíz del repositorio con el prefijo `backend/`.

Usan la configuración habitual del backend y las credenciales de Supabase.
`fetch_memberships.py` consulta membresías; `insert_membership.py` intenta insertar
una membresía; `register_client.py` intenta crear un cliente con membresía.
Antes de ejecutar los dos últimos, revisa los datos de ejemplo y utiliza una base
de pruebas: pueden escribir en la base configurada.

La suite automatizada mantiene su comando, desde `backend/`:

```bash
python -m pytest tests/ -q
```
