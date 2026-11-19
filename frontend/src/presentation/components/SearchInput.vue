<template>
  <input
    :value="String(modelValue ?? '').slice(0, maxlength)"
    type="search"
    :maxlength="maxlength"
    :aria-label="$attrs['aria-label'] || $attrs.placeholder || 'Buscar'"
    @input="update"
  />
</template>

<script setup>
import { FORM_LIMITS } from "../../domain/utils/formLimits.js";
const props = defineProps({
  modelValue: { type: String, default: '' },
  maxlength: { type: Number, default: FORM_LIMITS.shortText },
});
const emit = defineEmits(['update:modelValue']);
const update = (event) => {
  event.target.value = event.target.value.slice(0, props.maxlength);
  emit('update:modelValue', event.target.value);
};
</script>
