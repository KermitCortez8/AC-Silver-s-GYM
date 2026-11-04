"""Reconciliación periódica; solo archiva tras comprobar el estado del proveedor."""
import asyncio
import logging

logger = logging.getLogger(__name__)


async def maintain_preregistrations(factory):
    while True:
        try:
            await asyncio.to_thread(lambda: factory().archive_due_preregistrations())
        except Exception as error:
            logger.warning('Reconciliación de preregistros pendiente (%s)', type(error).__name__)
        await asyncio.sleep(60)
