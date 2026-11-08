import { onMounted, onBeforeUnmount } from 'vue';

/** Reconsulta la vista activa sin recargar la página ni consultar pestañas ocultas. */
export const useVisibleRefresh = (refresh, { canRefresh = () => true, interval = 30000 } = {}) => {
  let timer;
  let running = false;
  let disposed = false;
  const update = async () => {
    if (disposed || running || document.hidden || !canRefresh()) return;
    running = true;
    try {
      await refresh();
    } finally {
      running = false;
    }
  };
  onMounted(() => {
    void update();
    window.addEventListener('focus', update);
    document.addEventListener('visibilitychange', update);
    timer = setInterval(update, interval);
  });
  onBeforeUnmount(() => {
    disposed = true;
    clearInterval(timer);
    window.removeEventListener('focus', update);
    document.removeEventListener('visibilitychange', update);
  });
};
