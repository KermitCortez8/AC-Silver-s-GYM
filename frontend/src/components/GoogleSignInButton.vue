<template>
  <div class="space-y-3">
    <p v-if="!configured" class="text-center text-sm text-slate-500">El acceso con Google no está disponible por el momento.</p>
    <template v-else>
      <p v-if="loading" role="status" class="text-center text-sm text-slate-500">Cargando Google...</p>
      <div ref="container" :inert="disabled || loading" :class="{ 'pointer-events-none opacity-60': disabled }" class="flex min-h-[44px] justify-center"></div>
      <div v-if="error" role="alert" class="text-center text-sm text-amber-900">
        <p>{{ error }}</p>
        <button type="button" class="mt-2 font-bold underline" :disabled="disabled" @click="renderButton">Reintentar Google</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { GOOGLE_CONFIG } from '../config/googleConfig';
import { loadGoogleIdentityScript } from '../services/authService';

const props = defineProps({ text: { type: String, default: 'signin_with' }, disabled: Boolean });
const emit = defineEmits(['credential']);
const configured = Boolean(GOOGLE_CONFIG.webClientId);
const container = ref(null);
const loading = ref(false);
const error = ref('');
let active = true;

const renderButton = async () => {
  if (!configured || !active) return;
  loading.value = true;
  error.value = '';
  try {
    const google = await loadGoogleIdentityScript();
    if (!active || !container.value) return;
    google.accounts.id.initialize({
      client_id: GOOGLE_CONFIG.webClientId,
      callback: (response) => {
        if (active && !props.disabled && response.credential) emit('credential', response.credential);
      },
      ux_mode: 'popup',
      auto_select: false,
      cancel_on_tap_outside: true,
    });
    container.value.replaceChildren();
    google.accounts.id.renderButton(container.value, {
      type: 'standard', theme: 'outline', size: 'large', shape: 'pill',
      text: props.text, locale: 'es', width: Math.min(320, container.value.clientWidth || 280),
    });
  } catch (cause) {
    if (active) error.value = cause.message || 'No se pudo cargar Google';
  } finally {
    if (active) loading.value = false;
  }
};

onMounted(renderButton);
onBeforeUnmount(() => {
  active = false;
  window.google?.accounts?.id?.cancel();
});
</script>
