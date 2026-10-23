"""Errores de los puertos que presentación puede traducir sin conocer proveedores."""


class PersistenceUnavailable(RuntimeError):
    """El proveedor de datos no pudo completar la operación."""


class SchemaNotReady(PersistenceUnavailable):
    def __init__(self, migration):
        self.migration = migration
        super().__init__(f"Falta ejecutar backend/migrations/{migration} en Supabase")
