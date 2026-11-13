<template>
  <div class="fixed bottom-5 right-5 z-50 font-sans">
    <button
      v-if="!open"
      type="button"
      class="rounded-full bg-red-700 px-5 py-3 font-bold text-white shadow-xl hover:bg-red-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
      aria-label="Abrir asistente del gimnasio"
      @click="open = true"
    >
      Pregúntale a Silver
    </button>
    <section
      v-else
      aria-label="Asistente del gimnasio"
      class="flex h-[min(34rem,calc(100vh-2.5rem))] w-[min(23rem,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-slate-300 bg-white text-slate-900 shadow-2xl"
    >
      <header class="flex items-center justify-between bg-red-800 px-4 py-3 text-white">
        <div>
          <h2 class="font-bold">Pregúntale a Silver</h2>
          <p class="text-xs text-red-100">Información pública del gimnasio</p>
        </div>
        <button type="button" class="rounded px-2 text-2xl" aria-label="Cerrar asistente" @click="closeChat">×</button>
      </header>
      <div ref="logRef" class="flex-1 space-y-3 overflow-y-auto p-4" role="log" aria-live="polite">
        <p class="rounded-xl bg-slate-100 p-3 text-sm">Hola. Pregúntame por planes, clases, tipos de entrenamiento o cómo empezar.</p>
        <div v-for="(item, index) in messages" :key="index" class="space-y-1">
          <p :class="item.from === 'user' ? 'ml-8 bg-red-50' : 'mr-8 bg-slate-100'" class="rounded-xl p-3 text-sm whitespace-pre-wrap">{{ item.text }}</p>
          <div v-if="item.links?.length" class="flex gap-2">
            <router-link v-for="link in item.links" :key="link.ruta" :to="link.ruta" class="text-sm font-semibold text-red-700 underline">{{ link.texto }}</router-link>
          </div>
        </div>
        <p v-if="busy" class="text-sm text-slate-500">Consultando…</p>
      </div>
      <form v-if="recoveryActive" class="space-y-2 border-t border-slate-200 p-3" @submit.prevent="collectRecovery">
        <p class="text-xs text-slate-600">Solo para esta demostración. Estos datos no salen de tu navegador.</p>
        <label class="block text-xs font-semibold text-slate-700" for="recovery-email">Correo</label>
        <input id="recovery-email" v-model.trim="recoveryDraft.correo" type="email" required autocomplete="off" class="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-xs font-semibold text-slate-700" for="recovery-dni">DNI</label>
            <input id="recovery-dni" v-model.trim="recoveryDraft.dni" type="text" inputmode="numeric" pattern="[0-9]{8}" maxlength="8" required autocomplete="off" class="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700" for="recovery-phone">Número telefónico</label>
            <input id="recovery-phone" v-model.trim="recoveryDraft.telefono" type="tel" inputmode="numeric" pattern="[0-9]{9}" maxlength="9" required autocomplete="off" class="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
          </div>
        </div>
        <div class="flex gap-2">
          <button type="submit" class="flex-1 rounded-lg bg-red-700 px-3 py-2 text-sm font-bold text-white">Reunir datos aquí</button>
          <button type="button" class="rounded-lg border border-slate-300 px-3 py-2 text-sm" @click="cancelRecovery">Cancelar</button>
        </div>
      </form>
      <form v-else class="border-t border-slate-200 p-3" @submit.prevent="send">
        <label for="agent-message" class="sr-only">Tu pregunta para Silver</label>
        <div class="flex gap-2">
          <input id="agent-message" v-model="draft" maxlength="150" autocomplete="off" class="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900" placeholder="Pregunta sobre el gimnasio" :disabled="busy" />
          <button type="submit" class="rounded-lg bg-red-700 px-3 py-2 text-sm font-bold text-white disabled:opacity-50" :disabled="busy || !draft.trim()">Enviar</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { createAgentService } from '../../application/services/agentService.js';

const route = useRoute();
const open = ref(false);
const draft = ref('');
const busy = ref(false);
const messages = ref([]);
const conversationId = ref(null);
const logRef = ref(null);
const recoveryActive = ref(false);
const recoveryDraft = ref({ correo: '', dni: '', telefono: '' });
const pendingRecovery = ref(null);
const privateText = /[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b\d{8,9}\b|\b(?:contrase(?:ñ|n)a|password|clave)\s*(?:es|:|=)/i;

function cancelRecovery() {
  recoveryActive.value = false;
  recoveryDraft.value = { correo: '', dni: '', telefono: '' };
}

function closeChat() {
  open.value = false;
  cancelRecovery();
  pendingRecovery.value = null;
  messages.value = [];
  conversationId.value = null;
}

function collectRecovery() {
  pendingRecovery.value = { ...recoveryDraft.value };
  cancelRecovery();
  messages.value.push({
    from: 'agent',
    text: 'Reuní los datos solo en esta pestaña. Todavía no se enviaron ni se guardaron en el servidor; el dueño no recibió una solicitud. Al cerrar el chat, se borrarán.',
  });
}
watch([() => messages.value.length, busy], async () => {
  await nextTick();
  if (logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight;
});
watch(() => route.fullPath, () => {
  closeChat();
});

async function send() {
  const text = draft.value.trim();
  if (!text || busy.value) return;
  if (privateText.test(text)) {
    draft.value = '';
    messages.value.push({ from: 'agent', text: 'Por seguridad, no escribas datos personales o claves en el chat. Usa el formulario de recuperación si aparece.' });
    return;
  }
  messages.value.push({ from: 'user', text });
  draft.value = '';
  busy.value = true;
  try {
    const response = await createAgentService().send(text, conversationId.value);
    conversationId.value = response.id_conversacion;
    messages.value.push({ from: 'agent', text: response.texto, links: response.enlaces || [] });
    if (response.accion === 'recuperacion_local') recoveryActive.value = true;
  } catch (error) {
    const text = error?.status === 429
      ? 'Se alcanzó el límite temporal de consultas. Inténtalo de nuevo en un minuto.'
      : 'No pude consultar el servidor ahora. Inténtalo de nuevo o revisa la información pública en la página.';
    messages.value.push({ from: 'agent', text });
  } finally {
    busy.value = false;
  }
}
</script>
