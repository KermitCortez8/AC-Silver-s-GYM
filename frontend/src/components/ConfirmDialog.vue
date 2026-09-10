<template>
  <Teleport to="body">
    <dialog
      ref="dialog"
      :aria-labelledby="titleId"
      :aria-describedby="messageId"
      :aria-busy="busy"
      class="w-[calc(100%-2rem)] max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-slate-950 shadow-2xl"
      @cancel.prevent="cancel"
      @click="handleBackdrop"
    >
      <h2 :id="titleId" class="text-xl font-black">{{ title }}</h2>
      <p :id="messageId" class="mt-3 text-sm leading-6 text-slate-600">{{ message }}</p>
      <p v-if="error" role="alert" class="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-900">{{ error }}</p>
      <div class="mt-6 flex justify-end gap-3">
        <button type="button" autofocus :disabled="busy" class="rounded-xl border border-slate-300 px-4 py-3 font-bold disabled:opacity-50" @click="cancel">Cancelar</button>
        <button type="button" :disabled="busy" class="rounded-xl bg-red-600 px-4 py-3 font-bold text-white disabled:opacity-50" @click="confirm">{{ busy ? 'Activando...' : confirmLabel }}</button>
      </div>
    </dialog>
  </Teleport>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, useId } from 'vue';

const props = defineProps({
  title: { type: String, required: true },
  message: { type: String, required: true },
  confirmLabel: { type: String, default: 'Confirmar' },
  busy: Boolean,
  error: { type: String, default: '' },
});
const emit = defineEmits(['confirm', 'cancel']);
const dialog = ref(null);
const titleId = useId();
const messageId = useId();
const cancel = () => { if (!props.busy) emit('cancel'); };
const confirm = () => { if (!props.busy) emit('confirm'); };
const handleBackdrop = (event) => {
  if (event.target !== dialog.value) return;
  const bounds = dialog.value.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) cancel();
};
onMounted(() => dialog.value.showModal());
onBeforeUnmount(() => dialog.value?.close());
</script>

<style scoped>
dialog { margin: auto; }
dialog::backdrop { background: rgb(15 23 42 / 65%); }
</style>
