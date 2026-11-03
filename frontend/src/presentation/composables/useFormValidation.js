import { nextTick, reactive } from 'vue';

export const useFormValidation = (form, validator) => {
  const fieldErrors = reactive({});
  // Campos ya revisados (al salir de ellos o al enviar): desde ahi el aviso sigue a lo que se escribe.
  const checked = new Set();
  let submitted = false;
  const resetValidation = () => {
    Object.keys(fieldErrors).forEach(key => delete fieldErrors[key]);
    checked.clear();
    submitted = false;
  };
  const validateField = (field) => {
    checked.add(field);
    fieldErrors[field] = validator(form)[field] || '';
  };
  // Revalidate while typing so the error appears or clears with each change; the tick
  // keeps blur from moving the submit button during a click.
  const revalidateField = (field) => {
    if (submitted || checked.has(field) || fieldErrors[field]) return nextTick(() => validateField(field));
  };
  const validateForm = () => {
    resetValidation();
    submitted = true;
    Object.assign(fieldErrors, validator(form));
    return Object.keys(fieldErrors).length === 0;
  };
  return { fieldErrors, validateField, revalidateField, validateForm, resetValidation };
};
