export const EMAIL_DOMAIN_MESSAGE = 'Solo se permiten correos que terminen en .com.';

export const emailError = (value, { account = true } = {}) => {
  const email = String(value ?? '').trim();
  if (!email) return 'El correo es obligatorio.';
  const parts = email.split('@');
  const local = parts[0];
  const domain = parts[1] || '';
  if (parts.length !== 2 || email.length > 254 || local.length > 64
    || !/^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*$/i.test(local)
    || !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i.test(domain)) {
    return 'Ingresa un correo válido, por ejemplo nombre@gmail.com.';
  }
  if (account && !/\.com$/i.test(domain)) return EMAIL_DOMAIN_MESSAGE;
  return '';
};

export const requiredTextError = (value, label = 'El nombre', max = 120) => {
  const text = String(value ?? '').trim();
  if (!text) return `${label} es obligatorio.`;
  if (text.length > max) return `${label} no debe superar ${max} caracteres.`;
  return '';
};

export const dniError = (value, required = true) => {
  const text = String(value ?? '').trim();
  if (!text) return required ? 'El DNI es obligatorio.' : '';
  return /^[0-9]{8}$/.test(text) ? '' : 'El DNI debe tener exactamente 8 dígitos.';
};

export const phoneError = (value, required = false) => {
  const text = String(value ?? '').trim();
  if (!text) return required ? 'El teléfono es obligatorio.' : '';
  return /^[0-9]{7,9}$/.test(text) ? '' : 'El teléfono debe tener entre 7 y 9 dígitos, sin espacios ni letras.';
};

export const passwordError = (value, required = true) => {
  const text = String(value ?? '');
  if (!text) return required ? 'La contraseña es obligatoria.' : '';
  if (text.trim().length < 6) return 'La contraseña debe tener al menos 6 caracteres.';
  return '';
};

export const validateAccountForm = (form, { requirePassword = true, requireDni = true, requirePhone = false, google = false } = {}) => {
  const errors = {
    nombre: requiredTextError(form.nombre),
    correo: emailError(form.correo),
    dni: dniError(form.dni, requireDni),
    telefono: phoneError(form.telefono, requirePhone),
    password: google ? '' : passwordError(form.password, requirePassword),
  };
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message));
};

export const amountError = (value, label = 'El precio') => {
  if (value === '' || value == null) return `${label} es obligatorio.`;
  if (!/^[0-9]+(?:\.[0-9]{1,2})?$/.test(String(value)) || !Number.isFinite(Number(value))) {
    return `${label} debe ser un número mayor o igual a 0, con hasta 2 decimales.`;
  }
  return '';
};

export const durationError = (value) => {
  const text = String(value ?? '').trim();
  if (!text) return 'La duración es obligatoria.';
  return /^[1-9][0-9]*\s*(d[ií]as?|mes(?:es)?|a[ñn]os?)$/i.test(text)
    ? '' : 'Indica una duración válida, por ejemplo 30 días, 3 meses o 1 año.';
};

export const promotionErrors = (form) => {
  const errors = {};
  const name = requiredTextError(form.name, 'El nombre de la promoción');
  if (name) errors.name = name;
  const amount = amountError(form.discountValue, 'El descuento');
  if (amount) errors.discountValue = amount;
  else if (form.discountType === 'percent' && Number(form.discountValue) > 100) errors.discountValue = 'El descuento porcentual debe estar entre 0 y 100.';
  if (form.startsAt && form.validUntil && form.startsAt > form.validUntil) errors.validUntil = 'La fecha de fin debe ser igual o posterior a la de inicio.';
  if (!Array.isArray(form.appliesTo) || form.appliesTo.length !== 1) errors.appliesTo = 'Selecciona exactamente un plan para la promoción.';
  if (form.limite_cupos !== '' && form.limite_cupos != null && (!/^[0-9]+$/.test(String(form.limite_cupos)) || Number(form.limite_cupos) < 1)) errors.limite_cupos = 'El límite de cupos debe ser un entero mayor que cero.';
  return errors;
};
