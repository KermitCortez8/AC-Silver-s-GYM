<template>
  <Teleport to="body">
    <dialog
      ref="dialog"
      class="workspace-view ws-dialog"
      :aria-label="title"
      @cancel.prevent="requestClose"
      @close="emit('close')"
    >
      <div class="ws-toolbar mb-5">
        <h2 class="ws-heading">{{ title }}</h2>
        <button
          type="button"
          class="ws-btn"
          :disabled="busy"
          @click="requestClose"
        >
          Cerrar <X :size="16" aria-hidden="true" />
        </button>
      </div>
      <slot v-if="open" />
    </dialog>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { X } from 'lucide-vue-next';
const props = defineProps({
  open: Boolean,
  title: { type: String, required: true },
  busy: Boolean,
});
const emit = defineEmits(['close']);
const dialog = ref(null);
const requestClose = () => {
  if (!props.busy) dialog.value?.close();
};
watch(
  () => props.open,
  async (open) => {
    await nextTick();
    if (open && !dialog.value?.open) dialog.value?.showModal();
    else if (!open && dialog.value?.open) dialog.value.close();
  },
  { immediate: true },
);
onBeforeUnmount(() => dialog.value?.close());
</script>
