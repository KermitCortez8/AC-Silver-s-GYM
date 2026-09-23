<template>
  <Teleport to="body">
    <dialog ref="dialog" class="schedule-modal" :class="{ 'schedule-modal--wide': wide }" :aria-labelledby="titleId" :aria-busy="busy" @cancel.prevent="close">
      <header>
        <div><p class="modal-eyebrow">{{ eyebrow }}</p><h2 :id="titleId">{{ title }}</h2></div>
        <button type="button" class="modal-close" :disabled="busy" aria-label="Cerrar ventana" @click="close"><X :size="20" /></button>
      </header>
      <div class="modal-content"><slot /></div>
    </dialog>
  </Teleport>
</template>
<script>
let openModals = 0;
let originalOverflow;
</script>
<script setup>
import { onBeforeUnmount, onMounted, ref, useId } from 'vue';
import { X } from 'lucide-vue-next';
const props = defineProps({ title: { type: String, required: true }, eyebrow: { type: String, default: 'Horarios por servicio' }, busy: Boolean, wide: Boolean });
const emit = defineEmits(['close']);
const titleId = useId();
const dialog = ref(null);
const close = () => { if (!props.busy) emit('close'); };
onMounted(() => {
  if (openModals === 0) {
    originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }
  openModals += 1;
  dialog.value.showModal();
});
onBeforeUnmount(() => {
  dialog.value?.close();
  openModals -= 1;
  if (openModals === 0) document.body.style.overflow = originalOverflow;
});
</script>
<style scoped>
.schedule-modal { margin: auto; width: min(480px, calc(100% - 32px)); max-height: calc(100dvh - 32px); padding: 0; overflow-y: auto; border: 1px solid var(--app-border); border-radius: 20px; background: var(--app-canvas); color: var(--app-text); box-shadow: 0 24px 80px #0006; }
.schedule-modal--wide { width: min(680px, calc(100% - 32px)); }
.schedule-modal::backdrop { background: #080b14b8; backdrop-filter: blur(5px); }
header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; padding: 24px; border-bottom: 1px solid var(--app-border); background: var(--app-surface); }
h2 { margin: 5px 0 0; font-size: 23px; font-weight: 750; letter-spacing: -.025em; }
.modal-eyebrow { margin: 0; font-size: 11px; font-weight: 700; color: var(--app-accent-text); letter-spacing: .08em; text-transform: uppercase; }
.modal-close { display: grid; place-items: center; flex-shrink: 0; width: 44px; height: 44px; border: 1px solid var(--app-border); border-radius: 12px; color: var(--app-text-soft); background: var(--app-input); cursor: pointer; }
.modal-close:focus-visible { outline: 2px solid var(--app-accent); outline-offset: 3px; }
.modal-close:disabled { opacity: .5; cursor: wait; }
.modal-content { padding: 24px; }
@media (max-width: 480px) { header, .modal-content { padding: 20px; } }
</style>
