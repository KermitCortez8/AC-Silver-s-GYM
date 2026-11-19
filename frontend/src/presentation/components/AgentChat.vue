<template>
  <div class="fixed bottom-5 right-5 z-50 font-sans">
    <button
      v-if="!open"
      type="button"
      class="group relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-red-500 via-red-600 to-red-800 text-white shadow-[0_8px_24px_rgba(127,29,29,0.32)] ring-4 ring-white/90 motion-safe:transition-transform motion-safe:duration-200 hover:-translate-y-1 hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-red-700"
      aria-label="Abrir asistente del gimnasio"
      @click="open = true"
    >
      <svg class="h-11 w-11" viewBox="0 0 64 64" fill="none" aria-hidden="true">
        <path d="M32 14V9" stroke="white" stroke-width="3.5" stroke-linecap="round" />
        <circle cx="32" cy="7" r="3" fill="white" />
        <path d="M18 28a14 14 0 0 1 14-14h1a14 14 0 0 1 14 14v12a10 10 0 0 1-10 10H29l-8 5v-8a10 10 0 0 1-3-7V28Z" stroke="white" stroke-width="3.5" stroke-linejoin="round" />
        <path d="M17 30h-2a5 5 0 0 0-5 5v3a5 5 0 0 0 5 5h2m30-13h2a5 5 0 0 1 5 5v3a5 5 0 0 1-5 5h-2" stroke="white" stroke-width="3.5" stroke-linecap="round" />
        <path d="M26 32v4m13-4v4" stroke="white" stroke-width="4" stroke-linecap="round" />
        <path d="M28 42c2.5 2.5 6.5 2.5 9 0" stroke="white" stroke-width="3.5" stroke-linecap="round" />
      </svg>
      <span class="pointer-events-none absolute right-full mr-3 hidden whitespace-nowrap rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 sm:block">Pregúntale a Silver</span>
    </button>
    <section
      v-else
      aria-label="Asistente del gimnasio"
      class="flex h-[min(36rem,calc(100dvh-2.5rem))] w-[min(24rem,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white text-slate-900 shadow-[0_18px_60px_rgba(15,23,42,0.24)]"
    >
      <header class="flex items-center gap-3 bg-gradient-to-r from-red-900 via-red-800 to-red-700 px-4 py-3.5 text-white">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/25" aria-hidden="true">
          <svg class="h-7 w-7" viewBox="0 0 32 32" fill="none">
            <path d="M16 6V3m-8 9a7 7 0 0 1 7-7h2a7 7 0 0 1 7 7v7a6 6 0 0 1-6 6h-5l-5 3v-6a6 6 0 0 1-1-3v-7Z" stroke="white" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
            <path d="M12 15v2m8-2v2m-6 3c1 1 3 1 4 0" stroke="white" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <h2 class="text-sm font-bold tracking-wide">Pregúntale a Silver</h2>
          <p class="mt-0.5 text-xs text-red-100">Planes, clases y horarios</p>
        </div>
        <button type="button" class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xl leading-none text-white transition-colors hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white" aria-label="Cerrar asistente" @click="closeChat">×</button>
      </header>
      <div ref="logRef" class="flex-1 space-y-4 overflow-y-auto bg-gradient-to-b from-[#faf7f6] to-white p-4" role="log" aria-live="polite">
        <div class="flex items-end gap-2">
          <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-red-700 text-xs font-bold text-white" aria-hidden="true">S</span>
          <p class="max-w-[85%] rounded-2xl rounded-bl-md bg-white px-3.5 py-3 text-[13px] leading-5 text-slate-700 shadow-sm ring-1 ring-slate-200">Hola. Pregúntame por planes, clases, tipos de entrenamiento o cómo empezar.</p>
        </div>
        <div v-for="(item, index) in messages" :key="index" class="flex flex-col gap-2" :class="item.from === 'user' ? 'items-end' : 'items-start'">
          <p :class="item.from === 'user' ? 'rounded-br-md bg-red-100 text-slate-900' : 'rounded-bl-md bg-white text-slate-700 ring-1 ring-slate-200'" class="max-w-[88%] break-words whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-[13px] leading-5 shadow-sm">{{ item.text }}</p>
          <div v-if="item.links?.length" class="flex flex-wrap gap-2 pl-1">
            <router-link v-for="link in item.links" :key="link.ruta" :to="link.ruta" class="rounded-full border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 no-underline transition-colors hover:bg-red-50">{{ link.texto }}</router-link>
          </div>
        </div>
        <p v-if="busy" class="pl-9 text-xs text-slate-500">Silver está escribiendo…</p>
      </div>
      <form v-if="recoveryActive" class="space-y-2 border-t border-slate-200 p-3" @submit.prevent="collectRecovery">
        <p class="text-xs text-slate-600">Tu solicitud aún no se enviará al gimnasio.</p>
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
          <button type="submit" class="flex-1 rounded-lg bg-red-700 px-3 py-2 text-sm font-bold text-white">Dejar datos listos</button>
          <button type="button" class="rounded-lg border border-slate-300 px-3 py-2 text-sm" @click="cancelRecovery">Cancelar</button>
        </div>
      </form>
      <form v-else class="border-t border-slate-200 bg-white p-3 shadow-[0_-8px_24px_rgba(15,23,42,0.04)]" @submit.prevent="send">
        <label for="agent-message" class="sr-only">Tu pregunta para Silver</label>
        <div class="flex items-end gap-1.5 rounded-2xl border border-slate-200 bg-slate-50 p-1.5 transition-colors focus-within:border-red-400 focus-within:ring-2 focus-within:ring-red-100">
          <textarea id="agent-message" ref="composerRef" v-model="draft" rows="1" wrap="soft" maxlength="500" autocomplete="off" class="agent-composer block min-h-11 max-h-28 min-w-0 flex-1 resize-none overflow-y-auto rounded-xl border-0 bg-transparent px-2.5 py-2.5 text-sm leading-5 text-slate-900 placeholder:text-slate-400 focus:outline-none" placeholder="Escribe tu pregunta…" :disabled="busy" @keydown="handleComposerKeydown" />
          <button type="submit" class="h-11 shrink-0 rounded-xl bg-red-700 px-3.5 text-sm font-semibold text-white transition-colors hover:bg-red-800 disabled:opacity-50" :disabled="busy || !draft.trim()">Enviar</button>
        </div>
        <p class="mt-1.5 hidden px-2 text-[11px] text-slate-400 sm:block">Enter para enviar · Shift + Enter para otra línea</p>
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
const composerRef = ref(null);
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
    text: 'Listo, tus datos quedaron preparados en esta sesión. La solicitud aún no se ha enviado al gimnasio.',
  });
}
function resizeComposer() {
  const composer = composerRef.value;
  if (!composer) return;
  composer.style.height = 'auto';
  composer.style.height = `${Math.min(composer.scrollHeight, 112)}px`;
}
function handleComposerKeydown(event) {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  send();
}
watch(draft, async () => {
  await nextTick();
  resizeComposer();
});
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

<style scoped>
.agent-composer {
  scrollbar-width: none;
}

.agent-composer::-webkit-scrollbar {
  display: none;
}
</style>
