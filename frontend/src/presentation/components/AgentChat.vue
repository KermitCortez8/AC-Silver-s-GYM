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
        <button type="button" class="rounded px-2 text-2xl" aria-label="Cerrar asistente" @click="open = false">×</button>
      </header>
      <div class="flex-1 space-y-3 overflow-y-auto p-4" role="log" aria-live="polite">
        <p class="rounded-xl bg-slate-100 p-3 text-sm">Hola. Pregúntame por planes, clases, tipos de entrenamiento o cómo empezar.</p>
        <div v-for="(item, index) in messages" :key="index" class="space-y-1">
          <p :class="item.from === 'user' ? 'ml-8 bg-red-50' : 'mr-8 bg-slate-100'" class="rounded-xl p-3 text-sm whitespace-pre-wrap">{{ item.text }}</p>
          <div v-if="item.links?.length" class="flex gap-2">
            <router-link v-for="link in item.links" :key="link.ruta" :to="link.ruta" class="text-sm font-semibold text-red-700 underline">{{ link.texto }}</router-link>
          </div>
        </div>
        <p v-if="busy" class="text-sm text-slate-500">Consultando…</p>
      </div>
      <form class="border-t border-slate-200 p-3" @submit.prevent="send">
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
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { createAgentService } from '../../application/services/agentService.js';

const route = useRoute();
const open = ref(false);
const draft = ref('');
const busy = ref(false);
const messages = ref([]);
const conversationId = ref(null);
watch(() => route.fullPath, () => {
  open.value = false;
  messages.value = [];
  conversationId.value = null;
});

async function send() {
  const text = draft.value.trim();
  if (!text || busy.value) return;
  messages.value.push({ from: 'user', text });
  draft.value = '';
  busy.value = true;
  try {
    const response = await createAgentService().send(text, conversationId.value);
    conversationId.value = response.id_conversacion;
    messages.value.push({ from: 'agent', text: response.texto, links: response.enlaces || [] });
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
