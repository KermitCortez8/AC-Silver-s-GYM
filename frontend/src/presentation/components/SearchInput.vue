<template>
  <input
    :value="String(modelValue ?? '').slice(0, FORM_LIMITS.shortText)"
    type="search"
    :maxlength="FORM_LIMITS.shortText"
    :aria-label="$attrs['aria-label'] || $attrs.placeholder || 'Buscar'"
    @input="update"
  />
</template>

<script setup>
import { FORM_LIMITS } from "../../domain/utils/formLimits.js";
defineProps({ modelValue: { type: String, default: '' } });
const emit = defineEmits(['update:modelValue']);
const update = (event) => {
  event.target.value = event.target.value.slice(0, FORM_LIMITS.shortText);
  emit('update:modelValue', event.target.value);
};
</script>
