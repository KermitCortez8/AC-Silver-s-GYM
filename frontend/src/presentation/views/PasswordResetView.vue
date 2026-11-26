<template>
  <main class="public-page grid min-h-screen place-items-center bg-slate-100 p-4 text-slate-950">
    <section class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
      <h1 class="text-2xl font-extrabold">Crear contraseña nueva</h1>
      <div v-if="saved" class="mt-5 space-y-4">
        <p role="status" class="rounded-2xl bg-emerald-50 p-4 text-emerald-900">
          Tu contraseña se actualizó. Ya puedes usarla para iniciar sesión.
        </p>
        <router-link :to="{ name: 'Login' }" class="inline-flex rounded-xl bg-red-700 px-4 py-3 text-sm font-bold text-white">
          Ir a iniciar sesión
        </router-link>
      </div>
      <p v-else-if="!token" role="alert" class="mt-4 text-sm text-slate-600">
        Abre el enlace completo del correo de recuperación.
      </p>
      <form v-else class="mt-5 space-y-4" novalidate @submit.prevent="save">
        <fieldset class="space-y-4" :disabled="saving" :aria-busy="saving">
          <div>
            <label for="reset-password" class="block text-sm font-bold">Contraseña nueva</label>
            <input id="reset-password" v-model="password" type="password" required autocomplete="new-password"
              maxlength="256" :aria-invalid="Boolean(passwordProblem)"
              :aria-describedby="passwordProblem ? 'reset-password-error' : undefined" @input="clearFieldErrors" />
            <FieldError id="reset-password-error" :message="passwordProblem" />
          </div>
          <div>
            <label for="reset-confirm" class="block text-sm font-bold">Repite la contraseña nueva</label>
            <input id="reset-confirm" v-model="confirmation" type="password" required autocomplete="new-password"
              maxlength="256" :aria-invalid="Boolean(confirmProblem)"
              :aria-describedby="confirmProblem ? 'reset-confirm-error' : undefined" @input="confirmProblem = ''" />
            <FieldError id="reset-confirm-error" :message="confirmProblem" />
          </div>
          <button type="submit" class="w-full rounded-xl bg-red-700 px-4 py-3 text-sm font-bold text-white hover:bg-red-800 disabled:opacity-60">
            {{ saving ? 'Guardando…' : 'Guardar contraseña' }}
          </button>
        </fieldset>
      </form>
      <router-link v-if="!saved" :to="{ name: 'Login', query: { recuperar: '1' } }"
        class="mt-5 inline-block text-sm font-bold text-red-700 underline underline-offset-4">
        Solicitar otro enlace
      </router-link>
    </section>
    <FloatingNotice :message="error" tone="error" @dismiss="error = ''" />
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthentication } from '../../application/services/authentication.js';
import { passwordError } from '../../domain/utils/formValidation.js';
import FieldError from '../components/FieldError.vue';
import FloatingNotice from '../components/FloatingNotice.vue';

const route = useRoute();
const router = useRouter();
const { resetPassword } = useAuthentication();
const token = ref(new URLSearchParams(route.hash.slice(1)).get('token') || '');
const password = ref('');
const confirmation = ref('');
const passwordProblem = ref('');
const confirmProblem = ref('');
const error = ref('');
const saving = ref(false);
const saved = ref(false);

onMounted(() => {
  if (route.hash) void router.replace({ name: 'PasswordReset' });
});

const clearFieldErrors = () => {
  passwordProblem.value = '';
  confirmProblem.value = '';
};

const save = async () => {
  if (!token.value || saving.value) return;
  error.value = '';
  passwordProblem.value = passwordError(password.value);
  confirmProblem.value = password.value === confirmation.value ? '' : 'Las contraseñas no coinciden.';
  if (passwordProblem.value || confirmProblem.value) return;

  saving.value = true;
  try {
    await resetPassword(token.value, password.value);
    saved.value = true;
    token.value = '';
    password.value = '';
    confirmation.value = '';
  } catch (cause) {
    error.value = cause?.message || 'No se pudo guardar la contraseña.';
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
input {
  width: 100%;
  margin-top: .35rem;
  padding: .7rem .85rem;
  border: 1px solid #cbd5e1;
  border-radius: .75rem;
}
input[aria-invalid='true'] { border-color: #b91c1c; }
input:focus-visible { outline: 2px solid #b91c1c; outline-offset: 2px; }
</style>
