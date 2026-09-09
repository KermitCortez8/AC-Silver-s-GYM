// Continúa cargando las secciones disponibles y comunica cuáles fallaron.
export const syncResources = async (tasks, onFailure = () => {}) => {
  const failures = [];
  for (const [label, load] of tasks) {
    try {
      await load();
    } catch (error) {
      const reason = error instanceof SyntaxError
        ? 'El servidor devolvió datos inválidos. Inténtalo de nuevo.'
        : error instanceof TypeError
        ? 'No se pudieron recibir los datos. Comprueba la conexión e inténtalo de nuevo.'
        : error.message || 'No se pudieron cargar los datos.';
      failures.push(`${label}: ${reason}`);
      onFailure(failures.join(' '));
    }
  }
  if (failures.length) throw new Error(failures.join(' '));
};
