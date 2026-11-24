<template>
  <fieldset class="membership-payment-methods space-y-3" :disabled="disabled">
    <legend class="mb-2 text-sm font-bold">Método de pago</legend>
    <div class="grid gap-2 sm:grid-cols-2">
      <label v-for="option in options" :key="option.value" class="payment-option">
        <input v-model="selected" type="radio" :name="groupName" :value="option.value" />
        <span>
          <strong class="block text-sm">{{ option.label }}</strong>
          <span v-if="option.description" class="payment-description mt-0.5 block text-xs">{{ option.description }}</span>
        </span>
      </label>
    </div>
  </fieldset>
</template>

<script setup>
import { useId } from 'vue';

const selected = defineModel({ type: String, required: true });
defineProps({ options: { type: Array, required: true }, disabled: Boolean });
const groupName = useId();
</script>

<style scoped>
.membership-payment-methods { color: var(--app-text); min-width: 0; }
.payment-option {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-height: 3.25rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--app-border);
  border-radius: 0.75rem;
  background: var(--app-input);
  cursor: pointer;
}
.payment-option:has(input:checked) { border-color: var(--app-accent); }
.payment-option:focus-within { outline: 2px solid var(--app-accent); outline-offset: 2px; }
.payment-option input { accent-color: var(--app-accent); }
.payment-description { color: var(--app-text-muted); }
.membership-payment-methods:disabled .payment-option { cursor: default; opacity: 0.65; }
</style>
