<template>
  <input
    :value="String(modelValue ?? '').slice(0, 30)"
    type="search"
    maxlength="30"
    :aria-label="$attrs['aria-label'] || $attrs.placeholder || 'Buscar'"
    title="Búsqueda por coincidencia parcial. Máximo 30 caracteres."
    @input="update"
  />
</template>

<script setup>
defineProps({ modelValue: { type: String, default: '' } });
const emit = defineEmits(['update:modelValue']);
const update = (event) => {
  event.target.value = event.target.value.slice(0, 30);
  emit('update:modelValue', event.target.value);
};
</script>
