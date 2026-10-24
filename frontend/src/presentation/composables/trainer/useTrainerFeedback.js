import { reactive, ref, onScopeDispose } from 'vue';
export const useTrainerFeedback = () => {
  const feedback = ref('');
  const feedbackTone = ref('success');
  const toast = reactive({ show: false, message: '', type: 'success' });
  let toastTimeout = null;
  const showToast = (message, type = 'success') => {
    toast.message = message;
    toast.type = type;
    toast.show = true;
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      toast.show = false;
      toastTimeout = null;
    }, 4000);
  };
  const setFeedback = (message, type = 'success') => {
    feedbackTone.value = type;
    feedback.value = message;
  };
  const notify = (message, type = 'success', toastMessage = message) => {
    setFeedback(message, type);
    showToast(toastMessage, type);
  };
  onScopeDispose(() => clearTimeout(toastTimeout));
  return { feedback, feedbackTone, toast, notify, setFeedback, showToast };
};
