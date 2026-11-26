<template>
  <Teleport to="body" :disabled="inDialog">
    <div v-if="message" class="floating-notice"
      :class="[feedbackClass(tone), { 'in-dialog': inDialog, 'notice-warning': tone === 'warning', 'mobile-top': topOnMobile }]">
      <component :is="icon" :size="20" aria-hidden="true" />
      <div>
        <p :role="tone === 'error' ? 'alert' : 'status'">{{ message }}</p>
        <button v-if="actionLabel" type="button" class="floating-notice-action" @click="$emit('action')">{{ actionLabel }}</button>
      </div>
      <button type="button" aria-label="Cerrar aviso" @click="$emit('dismiss')">
        <X :size="18" aria-hidden="true" />
      </button>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { CircleAlert, CircleCheck, Info, TriangleAlert, X } from 'lucide-vue-next';
import { feedbackClass } from '../utils/feedback.js';

const props = defineProps({ message: String, tone: String, inDialog: Boolean, actionLabel: String, topOnMobile: Boolean });
defineEmits(['dismiss', 'action']);
const icon = computed(() => ({ success: CircleCheck, error: CircleAlert, warning: TriangleAlert })[props.tone] || Info);
</script>

<style scoped>
.floating-notice {
  position: fixed;
  z-index: 90;
  inset-inline-end: 1rem;
  inset-block-end: max(1rem, env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: start;
  gap: 0.65rem;
  width: min(29rem, calc(100vw - 2rem));
  padding: 0.85rem;
  border: 1px solid;
  border-radius: 1rem;
  box-shadow: 0 12px 32px rgb(0 0 0 / 26%);
}
.floating-notice > svg { margin-top: 0.2rem; }
.floating-notice p { margin: 0; line-height: 1.5; overflow-wrap: anywhere; }
.floating-notice button {
  display: grid;
  place-items: center;
  min-width: 2rem;
  min-height: 2rem;
  border-radius: 0.5rem;
  color: inherit;
}
.floating-notice button:hover { background: color-mix(in srgb, currentColor 12%, transparent); }
.floating-notice button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.floating-notice .floating-notice-action { display: inline-block; padding-inline: 0.3rem; text-decoration: underline; }
.floating-notice.notice-warning { --notice-ink: #f8d28a; --notice-background: #3a2f1d; --notice-border: #b3894e; }
:global(:root[data-theme='light'] .floating-notice.notice-warning) {
  --notice-ink: #80550b; --notice-background: #fff4d8; --notice-border: #d3ad66;
}
@media (max-width: 767px) {
  .floating-notice:not(.in-dialog) { inset-block-end: calc(5rem + env(safe-area-inset-bottom)); }
}
@media (max-width: 1023px) {
  .floating-notice.mobile-top {
    inset-block-start: calc(4.75rem + env(safe-area-inset-top));
    inset-block-end: auto;
  }
}
</style>
