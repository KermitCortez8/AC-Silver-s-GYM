<template>
  <input
    :value="modelValue"
    type="text"
    inputmode="numeric"
    pattern="[0-9]+"
    maxlength="10"
    required
    title="Ingresa solo dígitos enteros, sin signos, decimales ni exponentes"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
defineProps({ modelValue: { type: [Number, String], default: 0 } });
defineEmits(['update:modelValue']);
</script>
