/** Un guardado confirmado sigue siendo exitoso aunque falle la recarga posterior. */
export const refreshAfterMutation = async (ctx, refresh, label = 'Datos relacionados') => {
  const generation = ctx.generation;
  const key = `refresh:${label}`;
  try {
    await refresh();
    if (generation !== ctx.generation) return false;
    ctx.resourceErrors?.delete(key);
    if (ctx.syncError) ctx.syncError.value = [...(ctx.resourceErrors?.values() || [])].join(' ');
    return true;
  } catch (error) {
    if (generation !== ctx.generation) return false;
    const message = `El cambio se guardó, pero no se pudo actualizar ${label.toLowerCase()}: ${error.message || 'Inténtalo de nuevo.'}`;
    ctx.resourceErrors?.set(key, message);
    if (ctx.syncError) ctx.syncError.value = [...(ctx.resourceErrors?.values() || [message])].join(' ');
    return false;
  }
};
