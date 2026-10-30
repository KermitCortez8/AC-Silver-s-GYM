<template>
  <div>
    <select
      v-if="!isAdding"
      :id="id"
      :value="modelValue"
      class="inv-input"
      :class="{ 'is-invalid': invalid }"
      @change="handleChange($event.target.value)"
    >
      <option value="" disabled>{{ placeholder }}</option>
      <option v-for="option in allOptions" :key="option" :value="option">{{ option }}</option>
      <option :value="ADD_VALUE">+ {{ addLabel }}...</option>
    </select>
    <div v-else class="flex gap-2">
      <input
        :id="id"
        ref="newInput"
        v-model="draft"
        class="inv-input"
        :maxlength="NAME_MAX_LENGTH"
        :placeholder="addPlaceholder"
        @beforeinput="handleBeforeInput"
        @keydown.enter.prevent="confirmNew"
        @keydown.esc.stop.prevent="cancelNew"
      />
      <button type="button" class="inv-btn-ghost is-active shrink-0" @click="confirmNew">Agregar</button>
      <button type="button" class="inv-btn-ghost shrink-0" aria-label="Cancelar" @click="cancelNew">
        <X :size="16" aria-hidden="true" />
      </button>
    </div>
    <p v-if="error" role="alert" class="inv-field-error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue';
import { X } from 'lucide-vue-next';
import { cleanText, isAllowedText, NAME_MAX_LENGTH, normalizeSearch, uniqueOptions } from '../../../domain/utils/inputRules.js';

const ADD_VALUE = '__agregar_nuevo__';

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  id: { type: String, default: undefined },
  placeholder: { type: String, default: 'Selecciona una opción' },
  addLabel: { type: String, default: 'Agregar nuevo' },
  addPlaceholder: { type: String, default: 'Escribe el nuevo valor' },
  invalid: Boolean,
});
const emit = defineEmits(['update:modelValue']);

const isAdding = ref(false);
const draft = ref('');
const error = ref('');
const created = ref([]);
const newInput = ref(null);

// Incluye el valor actual aunque no venga en la lista (registros antiguos).
const allOptions = computed(() => uniqueOptions([props.modelValue], props.options, created.value));

const handleChange = async (value) => {
  if (value !== ADD_VALUE) {
    emit('update:modelValue', value);
    return;
  }
  isAdding.value = true;
  draft.value = '';
  error.value = '';
  await nextTick();
  newInput.value?.focus();
};

const handleBeforeInput = (event) => {
  if (event.data && !isAllowedText(event.data)) {
    event.preventDefault();
    error.value = 'Solo se permiten letras, números y espacios.';
  }
};

/**
 * Crea el valor nuevo y lo deja seleccionado (si ya existia, usa el existente).
 */
const confirmNew = () => {
  const { value, rejected } = cleanText(draft.value, NAME_MAX_LENGTH);
  const text = value.trim().replace(/\s+/g, ' ');
  if (rejected) {
    error.value = 'Solo se permiten letras, números y espacios.';
    draft.value = value;
    return;
  }
  if (!text) {
    error.value = 'Escribe un valor para agregarlo.';
    return;
  }
  const existing = allOptions.value.find((option) => normalizeSearch(option) === normalizeSearch(text));
  if (!existing) created.value = [...created.value, text];
  emit('update:modelValue', existing || text);
  isAdding.value = false;
  error.value = '';
};

const cancelNew = () => {
  isAdding.value = false;
  error.value = '';
};
</script>
