import { nextTick, reactive } from 'vue';

export const useFormValidation = (form, validator) => {
  const fieldErrors = reactive({});
  const resetValidation = () => Object.keys(fieldErrors).forEach(key => delete fieldErrors[key]);
  const validateField = (field) => { fieldErrors[field] = validator(form)[field] || ''; };
  // Clear corrected errors while typing so blur does not move the submit button during a click.
  const revalidateField = (field) => {
    if (fieldErrors[field]) return nextTick(() => validateField(field));
  };
  const validateForm = () => {
    resetValidation();
    Object.assign(fieldErrors, validator(form));
    return Object.keys(fieldErrors).length === 0;
  };
  return { fieldErrors, validateField, revalidateField, validateForm, resetValidation };
};
