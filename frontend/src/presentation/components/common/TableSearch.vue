<template>
  <div>
    <label class="inv-search block">
      <span class="sr-only">{{ label }}</span>
      <Search :size="16" class="inv-search-icon" aria-hidden="true" />
      <input
        :value="modelValue"
        type="search"
        class="inv-input text-sm"
        :class="{ 'is-invalid': message }"
        :maxlength="SEARCH_MAX_LENGTH"
        :placeholder="placeholder"
        :aria-describedby="message ? messageId : undefined"
        autocomplete="off"
        @beforeinput="handleBeforeInput"
        @input="handleInput"
      />
    </label>
    <p v-if="message" :id="messageId" role="alert" class="inv-field-error">{{ message }}</p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, useId } from 'vue';
import { Search } from 'lucide-vue-next';
import { cleanText, isAllowedText, SEARCH_MAX_LENGTH } from '../../../domain/utils/inputRules.js';

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: 'Buscar' },
  placeholder: { type: String, default: 'Buscar...' },
});
const emit = defineEmits(['update:modelValue']);

const messageId = `search-msg-${useId()}`;
const message = ref('');
let timer = null;

const warn = (text) => {
  message.value = text;
  clearTimeout(timer);
  timer = setTimeout(() => { message.value = ''; }, 3500);
};

/**
 * Bloquea al escribir los caracteres especiales y avisa al llegar al maximo (sin contador visible).
 */
const handleBeforeInput = (event) => {
  if (event.data && !isAllowedText(event.data)) {
    event.preventDefault();
    warn('Solo se permiten letras, números y espacios.');
    return;
  }
  const input = event.target;
  const selected = (input.selectionEnd ?? 0) - (input.selectionStart ?? 0);
  if (event.data && input.value.length - selected >= SEARCH_MAX_LENGTH) {
    warn(`Máximo ${SEARCH_MAX_LENGTH} caracteres.`);
  }
};

/**
 * Limpia lo pegado o arrastrado y respeta el maximo de caracteres.
 */
const handleInput = (event) => {
  const { value, rejected, truncated } = cleanText(event.target.value);
  if (value !== event.target.value) event.target.value = value;
  if (rejected) warn('Se quitaron los caracteres especiales: solo letras, números y espacios.');
  else if (truncated) warn(`Máximo ${SEARCH_MAX_LENGTH} caracteres.`);
  emit('update:modelValue', value);
};

onBeforeUnmount(() => clearTimeout(timer));
</script>
