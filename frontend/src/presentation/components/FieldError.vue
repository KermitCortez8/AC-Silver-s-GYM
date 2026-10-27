<template>
  <p v-if="message" :id="id" role="alert" class="field-error mt-1 text-sm font-semibold">{{ message }}</p>
</template>

<script setup>
defineProps({ id: String, message: String });
</script>

<style>
.field-error { color: #fca5a5; }
[data-theme='light'] .field-error,
.public-page .field-error { color: #b91c1c; }
</style>
