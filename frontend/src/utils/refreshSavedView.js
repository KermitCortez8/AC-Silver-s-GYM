// A confirmed write must not be reported as failed if only the subsequent read fails.
export const refreshSavedView = async (reload, notify, message, toastMessage = message) => {
  try {
    await reload();
  } catch (error) {
    notify(`${message} No se pudo actualizar la vista: ${error?.message || 'comprueba tu conexión'}. Actualiza los datos antes de repetir la operación.`, 'info');
    return;
  }
  notify(message, 'success', toastMessage);
};
