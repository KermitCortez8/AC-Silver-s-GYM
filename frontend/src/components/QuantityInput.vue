<template>
  <input
    :value="modelValue"
    type="text"
    inputmode="numeric"
    pattern="[0-9]+"
    maxlength="10"
    required
    title="Ingresa solo dígitos enteros, sin signos, decimales ni exponentes"
    @beforeinput="blockNonDigits"
    @input="handleInput"
  />
</template>

<script setup>
import { cleanInteger, isAllowedInteger } from '../../domain/utils/inputRules.js';

defineProps({ modelValue: { type: [Number, String], default: 0 } });
const emit = defineEmits(['update:modelValue']);

// Solo se pueden escribir números: letras y signos se bloquean al teclear.
const blockNonDigits = (event) => {
  if (event.data && !isAllowedInteger(event.data)) event.preventDefault();
};

// Lo pegado o arrastrado también se limpia.
const handleInput = (event) => {
  const clean = cleanInteger(event.target.value);
  if (clean !== event.target.value) event.target.value = clean;
  emit('update:modelValue', clean);
};
</script>
