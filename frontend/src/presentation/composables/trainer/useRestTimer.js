import { ref, onScopeDispose } from 'vue';

/** Una sola cuenta de descanso compartida entre la pantalla y el diálogo. */
export const useRestTimer = () => {
  const timerSeconds = ref(0);
  const timerInitialSeconds = ref(60);
  const timerActive = ref(false);
  const timerFinished = ref(false);
  let timerInterval = null;
  const pauseTimer = () => {
    timerActive.value = false;
    if (timerInterval !== null) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  };
  const resetTimer = () => {
    pauseTimer();
    timerSeconds.value = 0;
    timerFinished.value = false;
  };
  const startTimer = () => {
    if (timerSeconds.value <= 0) return;
    pauseTimer();
    timerFinished.value = false;
    timerActive.value = true;
    timerInterval = setInterval(() => {
      if (timerSeconds.value > 0) timerSeconds.value -= 1;
      if (timerSeconds.value <= 0) {
        pauseTimer();
        timerFinished.value = true;
      }
    }, 1000);
  };
  const setRestTimer = (seconds) => {
    const duration = Math.max(1, Math.floor(Number(seconds) || 60));
    resetTimer();
    timerInitialSeconds.value = duration;
    timerSeconds.value = duration;
    startTimer();
  };
  const resumeTimer = () =>
    timerSeconds.value > 0
      ? startTimer()
      : setRestTimer(timerInitialSeconds.value);
  onScopeDispose(pauseTimer);
  return {
    seconds: timerSeconds,
    initialSeconds: timerInitialSeconds,
    active: timerActive,
    finished: timerFinished,
    pause: pauseTimer,
    reset: resetTimer,
    resume: resumeTimer,
    start: setRestTimer,
  };
};
