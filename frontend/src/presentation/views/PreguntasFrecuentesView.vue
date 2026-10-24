<template>
  <div class="public-page faq-page min-h-screen bg-[#faf7f5] text-slate-950">
    <header class="sticky top-0 z-40 border-b border-orange-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic tracking-tight text-orange-600">
          Silver Gym Surco
        </router-link>

        <nav class="hidden items-center gap-6 text-sm font-bold uppercase tracking-[0.04em] text-slate-700 lg:flex">
          <router-link :to="{ path: '/', hash: '#servicios' }" class="transition hover:text-orange-600">Servicios</router-link>
          <router-link to="/nosotros" class="transition hover:text-orange-600">Nosotros</router-link>
          <router-link :to="{ path: '/', hash: '#membresias' }" class="transition hover:text-orange-600">Membresias</router-link>
          <router-link :to="{ path: '/', hash: '#ubicacion' }" class="transition hover:text-orange-600">Ubicacion</router-link>
        </nav>

        <div class="flex items-center gap-2">
          <router-link to="/registro" class="btn-cta rounded-full bg-orange-500 px-4 py-2 text-sm text-white shadow-lg shadow-orange-500/20 transition hover:bg-orange-600">
            Registrarse
          </router-link>
          <router-link to="/login" class="btn-cta hidden rounded-full border border-orange-200 bg-transparent px-4 py-2 text-sm text-orange-700/80 transition hover:bg-orange-50 hover:text-orange-700 sm:inline-flex">
            Acceso a plataforma digital
          </router-link>
        </div>
      </div>
    </header>

    <main>
      <section class="bg-[#141110] px-4 py-16 text-white sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1600px]">
          <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300">
            <span class="h-[2px] w-[18px] bg-orange-300"></span>
            Ayuda
          </span>
          <h1 class="mt-3 max-w-2xl text-3xl font-black leading-tight sm:text-4xl">Preguntas Frecuentes.</h1>
          <p class="mt-4 max-w-2xl text-sm leading-7 text-white/60">
            Resolvemos las dudas mas comunes sobre membresias, horarios y servicios de Silver Gym Surco.
          </p>

          <div class="mt-8 flex flex-col gap-3">
            <div
              v-for="(faq, index) in faqs"
              :key="faq.question"
              class="overflow-hidden rounded-2xl border border-white/15 bg-[#1c1816]"
            >
              <button
                type="button"
                @click="toggleFaq(index)"
                class="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
              >
                <span class="text-base font-black text-white">{{ faq.question }}</span>
                <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-orange-300 text-orange-300">
                  {{ openFaq === index ? '−' : '+' }}
                </span>
              </button>
              <Transition name="faq-panel">
                <div v-if="openFaq === index" class="px-6 pb-5">
                  <p class="text-sm leading-7 text-white/65">{{ faq.answer }}</p>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="bg-[#080808] px-4 pt-14 pb-8 text-white sm:px-6 lg:px-8">
      <div class="mx-auto max-w-[1600px]">
        <div class="grid gap-8 border-b border-white/10 pb-8 sm:grid-cols-3">
          <div>
            <p class="text-lg font-black italic text-white">Silver Gym Surco</p>
            <p class="mt-3 max-w-[30ch] text-sm leading-6 text-white/45">Ubicacion, horarios y registro en un mismo lugar.</p>
          </div>

          <div>
            <p class="text-xs font-black uppercase tracking-[0.08em] text-orange-300">Explorar</p>
            <nav class="mt-4 flex flex-col gap-2.5">
              <router-link :to="{ path: '/', hash: '#servicios' }" class="text-sm font-semibold text-white/65 transition hover:text-white">Servicios</router-link>
              <router-link to="/nosotros" class="text-sm font-semibold text-white/65 transition hover:text-white">Nosotros</router-link>
              <router-link :to="{ path: '/', hash: '#membresias' }" class="text-sm font-semibold text-white/65 transition hover:text-white">Membresias</router-link>
              <router-link :to="{ path: '/', hash: '#ubicacion' }" class="text-sm font-semibold text-white/65 transition hover:text-white">Ubicacion</router-link>
            </nav>
          </div>

          <div>
            <p class="text-xs font-black uppercase tracking-[0.08em] text-orange-300">Contacto</p>
            <div class="mt-4 flex flex-col gap-2.5">
              <span class="flex items-start gap-2 text-sm font-semibold text-white/65">
                <svg class="mt-0.5 h-3.5 w-3.5 flex-none text-orange-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s7-7.2 7-12.5A7 7 0 0 0 5 9.5C5 14.8 12 22 12 22z"/><circle cx="12" cy="9.5" r="2.5"/></svg>
                Jirón Vista Alegre 606, Lima 15056
              </span>
              <span class="flex items-center gap-2 text-sm font-semibold text-white/65">
                <svg class="h-3.5 w-3.5 flex-none text-orange-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Lun a sab
              </span>
            </div>
          </div>
        </div>

        <div class="flex flex-col items-center gap-2 pt-6 text-center sm:flex-row sm:justify-between sm:text-left">
          <p class="text-xs text-white/35">© 2026 Silver Gym Surco. Todos los derechos reservados.</p>
          <p class="text-xs text-white/25">Hecho por el equipo Silver Gym Surco</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const openFaq = ref(null);

const toggleFaq = (index) => {
  openFaq.value = openFaq.value === index ? null : index;
};

const faqs = [
  {
    question: '¿Necesito experiencia previa para inscribirme?',
    answer: 'No, contamos con rutinas para todos los niveles. Nuestros entrenadores te guían desde el primer día para que entrenes de forma segura y efectiva.',
  },
  {
    question: '¿Puedo cambiar de plan de membresia despues de inscribirme?',
    answer: 'Sí, puedes actualizar tu plan en cualquier momento desde la plataforma digital o consultando directamente en recepción.',
  },
  {
    question: '¿Qué debo llevar el primer día?',
    answer: 'Ropa cómoda, zapatillas deportivas, una botella de agua y una toalla pequeña. Nosotros nos encargamos del resto.',
  },
  {
    question: '¿Los horarios de clases grupales tienen cupo limitado?',
    answer: 'Sí, cada clase tiene un cupo máximo para garantizar una buena atención. Puedes revisar la disponibilidad en la sección de Servicios.',
  },
  {
    question: '¿Hay estacionamiento disponible?',
    answer: 'Sí, contamos con estacionamiento cercano en la misma cuadra del gimnasio.',
  },
  {
    question: '¿Cómo cancelo o pauso mi membresia?',
    answer: 'Puedes hacerlo desde tu cuenta en la plataforma digital o acercándote a recepción, donde te orientaremos según tu plan actual.',
  },
];
</script>

<style scoped>
.faq-page {
  font-family: 'Manrope', 'Segoe UI', 'Trebuchet MS', sans-serif;
}
.faq-page h1 {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
}
.faq-page .btn-cta {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.faq-panel-enter-active,
.faq-panel-leave-active {
  transition: all 0.25s ease;
}
.faq-panel-enter-from,
.faq-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>