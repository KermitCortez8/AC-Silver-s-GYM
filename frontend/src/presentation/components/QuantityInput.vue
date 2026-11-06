<template>
  <input
    :value="modelValue"
    type="text"
    inputmode="numeric"
    pattern="[0-9]+"
    maxlength="10"
    required
    title="Ingresa solo dígitos enteros, sin signos, decimales ni exponentes"
    @beforeinput="handleBeforeInput"
    @input="handleInput"
  />
</template>

<script setup>
import { cleanInteger, isAllowedInteger } from '../../domain/utils/inputRules.js';

defineProps({ modelValue: { type: [Number, String], default: 0 } });
const emit = defineEmits(['update:modelValue']);

const handleBeforeInput = (event) => {
  if (event.data && !isAllowedInteger(event.data)) {
    event.preventDefault();
  }
};

const handleInput = (event) => {
  const cleaned = cleanInteger(event.target.value);
  if (cleaned !== event.target.value) {
    event.target.value = cleaned;
  }
  emit('update:modelValue', cleaned);
};
</script>
