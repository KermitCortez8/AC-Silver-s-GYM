const invalidResponse = () => new Error('El servidor devolvió datos incompletos o inválidos. Actualiza la vista antes de repetir la operación.');

export const requireRecord = (value, idField) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw invalidResponse();
  if (idField) {
    const id = value[idField];
    const validType = typeof id === 'number' || (typeof id === 'string' && /^[0-9]+$/.test(id));
    if (!validType || !Number.isSafeInteger(Number(id)) || Number(id) <= 0) throw invalidResponse();
  }
  return value;
};

export const requireList = (value, idField) => {
  if (!Array.isArray(value)) throw invalidResponse();
  value.forEach(item => requireRecord(item, idField));
  return value;
};
