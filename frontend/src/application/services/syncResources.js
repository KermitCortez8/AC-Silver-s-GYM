// Hasta tres consultas independientes a la vez, sin abandonar las demás
// secciones cuando una falla ni saturar el backend con toda la carga de golpe.
export const syncResources = async (tasks, onFailure = () => {}) => {
  const failures = [];
  let next = 0;
  const worker = async () => {
    while (next < tasks.length) {
      const index = next++;
      const [label, load] = tasks[index];
      try {
        await load();
      } catch (error) {
        const reason = error instanceof SyntaxError
          ? 'El servidor devolvió datos inválidos. Inténtalo de nuevo.'
          : error instanceof TypeError
          ? 'No se pudieron recibir los datos. Comprueba la conexión e inténtalo de nuevo.'
          : error?.message || 'No se pudieron cargar los datos.';
        failures[index] = `${label}: ${reason}`;
        onFailure(failures.filter(Boolean).join(' '));
      }
    }
  };
  await Promise.all(Array.from({ length: Math.min(3, tasks.length) }, worker));
  if (failures.length) throw new Error(failures.filter(Boolean).join(' '));
};
