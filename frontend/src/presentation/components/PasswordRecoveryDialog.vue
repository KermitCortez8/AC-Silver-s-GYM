<template>
  <dialog ref="dialog" aria-labelledby="recovery-title"
    class="public-page m-auto max-h-[calc(100dvh-2rem)] w-[min(30rem,calc(100%-2rem))] overflow-auto rounded-3xl border border-slate-200 bg-white p-5 text-slate-950 shadow-2xl backdrop:bg-slate-950/60 sm:p-7"
    @cancel.prevent="close" @close="$emit('close')">
    <header class="flex items-start justify-between gap-4">
      <h2 id="recovery-title" class="text-xl font-extrabold">Recuperar contraseña</h2>
      <button type="button" aria-label="Cerrar recuperación" class="rounded-xl p-2 text-slate-600 hover:bg-slate-100"
        :disabled="sending" @click="close">
        <X :size="20" aria-hidden="true" />
      </button>
    </header>
    <div v-if="sent" class="mt-5 space-y-4">
      <p role="status" class="rounded-2xl bg-emerald-50 p-4 text-sm leading-relaxed text-emerald-900">
        Si el correo está registrado, recibirás un enlace para crear una contraseña nueva.
        Revisa también la carpeta de spam.
      </p>
      <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 font-bold" @click="close">Entendido</button>
    </div>
    <form v-else novalidate class="mt-4 space-y-4" :aria-busy="sending" @submit.prevent="submit">
      <p class="text-sm text-slate-600">Ingresa el correo asociado a tu cuenta.</p>
      <div>
        <label for="recovery-email" class="block text-sm font-bold">Correo</label>
        <input id="recovery-email" ref="emailInput" v-model.trim="email" type="email" autofocus required autocomplete="email"
          :disabled="sending" :maxlength="FORM_LIMITS.shortText" :aria-invalid="Boolean(emailProblem)"
          :aria-describedby="emailProblem ? 'recovery-email-error' : undefined" @input="emailProblem = ''" />
        <FieldError id="recovery-email-error" :message="emailProblem" />
      </div>
      <button type="submit" class="w-full rounded-xl bg-red-700 px-4 py-3 text-sm font-bold text-white hover:bg-red-800 disabled:opacity-60"
        :disabled="sending">
        {{ sending ? 'Enviando…' : 'Enviar enlace de recuperación' }}
      </button>
      <FloatingNotice in-dialog :message="error" tone="error" @dismiss="error = ''" />
    </form>
  </dialog>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue';
import { X } from 'lucide-vue-next';
import { useAuthentication } from '../../application/services/authentication.js';
import { FORM_LIMITS } from '../../domain/utils/formLimits.js';
import { emailError } from '../../domain/utils/formValidation.js';
import FieldError from './FieldError.vue';
import FloatingNotice from './FloatingNotice.vue';

defineEmits(['close']);
const { requestPasswordRecovery } = useAuthentication();
const dialog = ref(null);
const emailInput = ref(null);
const email = ref('');
const emailProblem = ref('');
const error = ref('');
const sending = ref(false);
const sent = ref(false);

onMounted(() => dialog.value?.showModal());
const close = () => {
  if (!sending.value) dialog.value?.close();
};

const submit = async () => {
  if (sending.value) return;
  error.value = '';
  emailProblem.value = emailError(email.value, { account: false });
  if (emailProblem.value) {
    await nextTick();
    emailInput.value?.focus();
    return;
  }
  sending.value = true;
  try {
    await requestPasswordRecovery({ correo: email.value });
    sent.value = true;
  } catch (cause) {
    error.value = cause?.message || 'No se pudo enviar la solicitud. Inténtalo de nuevo.';
  } finally {
    sending.value = false;
  }
};
</script>

<style scoped>
input {
  width: 100%;
  margin-top: .35rem;
  padding: .65rem .8rem;
  border: 1px solid #cbd5e1;
  border-radius: .75rem;
}
input[aria-invalid='true'] { border-color: #b91c1c; }
input:focus-visible { outline: 2px solid #b91c1c; outline-offset: 2px; }
</style>
