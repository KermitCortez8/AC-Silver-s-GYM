const sequence = ['servicios', 'nosotros', 'membresias', 'ubicacion'];
const requiredSelections = sequence.length * 4;

// Compartido entre la landing y Nosotros; se reinicia al recargar la página.
let progress = 0;

export const registerLandingSelection = (selection) => {
  if (selection === sequence[progress % sequence.length]) {
    progress += 1;
  } else {
    progress = selection === sequence[0] ? 1 : 0;
  }

  if (progress === requiredSelections) {
    progress = 0;
    return true;
  }

  return false;
};
