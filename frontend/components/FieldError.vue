<template>
  <p v-if="message" :id="id" role="alert" class="field-error mt-1 flex items-start gap-1.5 text-sm font-semibold">
    <AlertCircle :size="14" class="field-error-icon" aria-hidden="true" />
    <span>{{ message }}</span>
  </p>
</template>

<script setup>
import { AlertCircle } from 'lucide-vue-next';

defineProps({ id: String, message: String });
</script>

<style>
.field-error { color: #fca5a5; }
.field-error-icon { flex-shrink: 0; margin-top: 0.1em; }
[data-theme='light'] .field-error,
.public-page .field-error { color: #b91c1c; }
</style>
