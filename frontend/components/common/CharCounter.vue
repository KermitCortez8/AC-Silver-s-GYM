<template>
  <span class="inv-counter" :class="{ 'is-near': isNear, 'is-limit': isLimit }" :title="`Máximo ${max} caracteres`">
    {{ length }}/{{ max }}
  </span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  value: { type: [String, Number], default: '' },
  max: { type: Number, required: true },
});

const length = computed(() => String(props.value ?? '').length);
const isLimit = computed(() => length.value >= props.max);
const isNear = computed(() => length.value >= Math.floor(props.max * 0.9));
</script>
