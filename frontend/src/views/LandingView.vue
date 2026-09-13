<template>
  <div class="landing-page min-h-screen bg-[#faf7f5] text-slate-950">
    <header class="sticky top-0 z-40 border-b border-orange-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic tracking-tight text-orange-600">
          Silver Gym Surco
        </router-link>

        <nav class="hidden items-center gap-6 text-sm font-bold uppercase tracking-[0.04em] text-slate-700 lg:flex">
          <a href="#servicios" class="transition hover:text-orange-600">Servicios</a>
          <router-link to="/nosotros" class="transition hover:text-orange-600">Nosotros</router-link>
          <a href="#membresias" class="transition hover:text-orange-600">Membresias</a>
          <a href="#ubicacion" class="transition hover:text-orange-600">Ubicacion</a>
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
      <Transition name="toast-slide">
        <div
          v-if="showRegistrationNotice"
          class="fixed right-4 top-20 z-50 w-[calc(100%-2rem)] max-w-sm sm:right-6 sm:top-24"
          role="status"
        >
          <div
            class="flex items-start gap-3 rounded-2xl bg-white p-4"
            style="border: 1px solid #a7f3d0; box-shadow: 0 20px 45px rgba(6, 95, 70, 0.18);"
          >
            <div
              class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-base font-black"
              style="background-color: #d1fae5; color: #047857;"
            >
              ✓
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-xs font-black uppercase tracking-[0.07em]" style="color: #047857;">Registro completado</p>
              <p class="mt-1 text-sm font-bold leading-5" style="color: #064e3b;">
                Su cuenta ha sido inicializada. A la espera de activación de membresía.
              </p>
              <p v-if="registrationCode" class="mt-1 text-xs" style="color: #059669;">Solicitud {{ registrationCode }}</p>
            </div>
            <button
              type="button"
              class="toast-close -mr-1 -mt-1 rounded-full p-1.5 text-lg leading-none transition"
              style="color: #059669;"
              aria-label="Cerrar aviso"
              @click="dismissRegistrationNotice"
            >
              ×
            </button>
          </div>
        </div>
      </Transition>

      <section class="relative overflow-hidden px-4 py-16 sm:px-6 lg:px-8 lg:min-h-[34rem] lg:py-20">
        <img
          :src="heroBanner"
          alt=""
          class="absolute inset-0 h-full w-full object-cover"
        />
        <div class="absolute inset-0 bg-[linear-gradient(100deg,rgba(15,12,11,0.94)_0%,rgba(15,12,11,0.78)_38%,rgba(15,12,11,0.35)_70%,rgba(15,12,11,0.12)_100%)]"></div>

        <div class="relative mx-auto flex max-w-[1600px] flex-col lg:min-h-[26rem] lg:justify-center">
          <div class="max-w-xl">
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-500">
              <span class="h-[2px] w-[18px] bg-orange-500"></span>
              Gimnasio · Salud y disciplina
            </span>
            <h1 class="mt-5 text-4xl font-black leading-[1.05] text-white sm:text-5xl lg:text-[3.1rem]">
              Entrena fuerte,<br /><span class="text-orange-500">cerca de casa.</span>
            </h1>
            <p class="mt-6 max-w-[46ch] text-lg leading-8 text-white/75">
              En Silver Gym Surco ofrecemos entrenamiento funcional, musculacion, cardio y clases grupales con horarios pensados para tu rutina diaria.
            </p>

            <div class="mt-8 flex flex-wrap gap-3">
              <router-link to="/registro" class="btn-cta rounded-full bg-orange-500 px-6 py-3.5 text-center text-sm text-white shadow-xl shadow-orange-500/25 transition hover:-translate-y-0.5 hover:bg-orange-600">
                Registrarme ahora
              </router-link>
              <router-link to="/login" class="btn-cta rounded-full border border-white bg-white px-6 py-3.5 text-center text-sm text-slate-900 shadow-lg shadow-black/20 transition hover:bg-white/90">
                Acceso a plataforma digital
              </router-link>
            </div>

            <div class="mt-10 flex flex-wrap justify-start gap-x-8 gap-y-4 divide-x divide-white/15 text-left">
              <div v-for="stat in stats" :key="stat.label" class="px-8 first:pl-0 last:pr-0">
                <p class="text-xs font-bold uppercase tracking-[0.06em] text-orange-400">{{ stat.label }}</p>
                <p class="mt-1 text-base font-black tabular-nums text-white">{{ stat.value }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="servicios" class="mx-auto max-w-[1600px] px-4 pt-16 pb-8 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-black uppercase tracking-[0.08em] text-orange-500">Servicios</p>
            <h2 class="mt-3 max-w-2xl text-3xl font-black leading-tight sm:text-4xl">Todo lo que necesitas para entrenar mejor.</h2>
          </div>
          <p class="max-w-2xl text-base leading-7 text-slate-600">
            Nuestro objetivo es que cada cliente tenga una ruta clara: elegir membresia, matricular horarios y registrar asistencia desde la plataforma digital.
          </p>
        </div>

        <p class="mt-6 flex items-center gap-2 text-sm font-semibold text-slate-500">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" /></svg>
          Selecciona un servicio para ver los horarios disponibles
        </p>

        <div class="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <article
            v-for="service in services"
            :key="service.title"
            @click="toggleService(service.title)"
            :class="[
              'service-card group relative flex aspect-[3/4] cursor-pointer flex-col overflow-hidden rounded-2xl transition-all duration-300',
              selectedService === service.title
                ? 'ring-2 ring-orange-500 -translate-y-1 shadow-[0_22px_50px_rgba(220,38,38,0.35)]'
                : 'ring-1 ring-black/5 hover:-translate-y-1 hover:shadow-[0_22px_48px_rgba(220,38,38,0.20)]'
            ]"
          >
            <img
              :src="service.image"
              alt=""
              :class="['absolute inset-0 h-full w-full transition-transform duration-500 group-hover:scale-105', service.imageClass]"
              loading="lazy"
              @error="handleImageError"
            />
            <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,12,11,0.05)_0%,rgba(15,12,11,0.22)_38%,rgba(15,12,11,0.95)_100%)]"></div>

            <span class="relative z-10 m-3 inline-flex w-fit items-center rounded-full bg-black/40 px-2.5 py-1 font-black text-white backdrop-blur-sm" style="font-family:'Anton','Manrope',sans-serif; font-size:0.8rem; letter-spacing:0.04em;">{{ service.tag }}</span>

            <div
              :class="[
                'absolute right-3 top-3 z-10 flex h-7 w-7 items-center justify-center rounded-full transition-all duration-300',
                selectedService === service.title
                  ? 'scale-100 opacity-100'
                  : 'scale-75 bg-white/80 opacity-0 group-hover:scale-100 group-hover:opacity-70'
              ]"
              :style="selectedService === service.title ? { backgroundColor: '#dc2626' } : {}"
            >
              <svg xmlns="http://www.w3.org/2000/svg" :class="selectedService === service.title ? 'h-4 w-4 text-white' : 'h-4 w-4 text-orange-600'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <div class="relative z-10 mt-auto flex flex-col gap-1.5 p-5">
              <h3 class="text-xl font-black text-white">{{ service.title }}</h3>
              <p class="line-clamp-2 text-sm leading-6 text-white/70">{{ service.description }}</p>
              <div
                :class="[
                  'mt-1 flex items-center gap-1 text-xs font-black uppercase tracking-[0.06em] transition-colors duration-200',
                  selectedService === service.title ? 'text-orange-400' : 'text-white/55 group-hover:text-orange-300'
                ]"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ selectedService === service.title ? 'Horarios visibles ↓' : 'Ver horarios' }}
              </div>
            </div>
          </article>
        </div>
        <Transition name="schedule-panel">
          <div
            v-if="selectedService"
            class="mt-6 overflow-hidden rounded-2xl border border-orange-200 bg-white shadow-[0_18px_40px_rgba(249,115,22,0.12)]"
          >
            <!-- Panel header -->
            <div class="flex items-center justify-between bg-gradient-to-r from-orange-500 to-orange-600 px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <p class="text-xs font-bold uppercase tracking-[0.06em] text-orange-100">Horarios disponibles</p>
                  <h3 class="text-xl font-black text-white">{{ selectedService }}</h3>
                </div>
              </div>
              <button
                @click="selectedService = null"
                class="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 text-white transition hover:bg-white/30"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Schedule table -->
            <div class="overflow-x-auto">
              <table class="w-full table-fixed text-sm">
                <colgroup>
                  <col class="w-[22%]" />
                  <col class="w-[28%]" />
                  <col class="w-[50%]" />
                </colgroup>
                <thead>
                  <tr class="border-b border-orange-100 bg-orange-50">
                    <th class="px-6 py-3 text-left text-xs font-black uppercase tracking-[0.06em] text-orange-600">Día</th>
                    <th class="px-6 py-3 text-left text-xs font-black uppercase tracking-[0.06em] text-orange-600">Hora</th>
                    <th class="px-6 py-3 text-left text-xs font-black uppercase tracking-[0.06em] text-orange-600">Entrenador</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(sched, index) in filteredSchedules"
                    :key="index"
                    :class="['sched-row border-b border-slate-50 transition-colors', index % 2 === 0 ? 'bg-white' : 'bg-slate-50/40']"
                  >
                    <td class="px-6 py-4">
                      <span class="inline-flex items-center rounded-full bg-orange-100 px-3 py-1 text-xs font-black text-orange-700">{{ sched.dia }}</span>
                    </td>
                    <td class="px-6 py-4">
                      <span class="sched-hour flex items-center gap-1.5 whitespace-nowrap font-black text-slate-950">
                        <svg xmlns="http://www.w3.org/2000/svg" class="sched-icon h-3.5 w-3.5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {{ sched.hora }}
                      </span>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex min-w-0 items-center gap-2">
                        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-xs font-black text-white">
                          {{ sched.entrenador.charAt(0) }}
                        </div>
                        <span class="sched-name truncate font-semibold text-slate-700">{{ sched.entrenador }}</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="border-t border-orange-100 bg-orange-50/50 px-6 py-3">
              <p class="text-xs text-slate-500">{{ filteredSchedules.length }} sesiones semanales disponibles para <strong class="text-orange-600">{{ selectedService }}</strong></p>
            </div>
          </div>
        </Transition>
      </section>

      <section id="membresias" class="bg-[#faf7f5] px-4 pt-8 pb-8 sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1600px]">
          <div class="rounded-[1.75rem] border border-white/10 bg-[#141110] p-6 text-white shadow-2xl shadow-red-950/20 lg:p-10">
            <div>
              <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300">
                <span class="h-[2px] w-[18px] bg-orange-300"></span>
                Membresias
              </span>
              <h2 class="mt-3 text-3xl font-black uppercase leading-tight text-white">Elige el plan que acompane tu ritmo.</h2>
            </div>

            <div class="mt-8 grid gap-4 lg:grid-cols-3">
              <router-link
                v-for="plan in plans"
                :key="plan.id"
                :to="{ path: '/registro', query: { plan: plan.id } }"
                :class="[
                  'relative flex flex-col gap-3 rounded-2xl border p-6 transition hover:-translate-y-1',
                  plan.id === '3 MESES'
                    ? 'border-2'
                    : 'border-white/15 hover:border-white/30'
                ]"
                :style="plan.id === '3 MESES' ? { borderColor: '#ff4d56', background: 'linear-gradient(180deg, rgba(220,38,38,0.16), rgba(220,38,38,0.02) 60%)' } : {}"
              >
                <span
                  v-if="plan.id === '3 MESES'"
                  class="absolute -top-3 right-6 rounded-full bg-orange-500 px-3 py-1 text-[0.65rem] font-black uppercase tracking-[0.05em] text-white shadow"
                >
                  Mas elegido
                </span>
                <p class="text-sm font-black uppercase tracking-[0.06em] text-orange-300">{{ plan.label }}</p>
                <p class="text-3xl font-black tabular-nums text-white">S/ {{ plan.price }}</p>
                <p class="flex items-center gap-2 text-sm leading-6 text-white/60">
                  <span class="font-black text-emerald-400">✓</span>{{ plan.description }}
                </p>
                <span
                  :class="[
                    'btn-cta mt-1 inline-flex w-fit items-center justify-center rounded-full px-4 py-2 text-xs',
                    plan.id === '3 MESES' ? 'bg-orange-500 text-white' : 'border border-white/25 text-white'
                  ]"
                >
                  Elegir plan
                </span>
              </router-link>
            </div>
            <p v-if="!plans.length" class="mt-8 rounded-2xl border border-white/15 bg-white/5 p-5 text-sm font-bold text-white/70">
              Planes pendientes de configuracion.
            </p>
          </div>
        </div>
      </section>

      <section id="ubicacion" class="px-4 pt-8 pb-16 sm:px-6 lg:px-8">
        <div class="mx-auto grid max-w-[1600px] overflow-hidden rounded-[1.75rem] bg-[#141110] text-white shadow-2xl shadow-red-950/20 lg:grid-cols-[1fr_1.15fr]">
          <div class="flex flex-col justify-center gap-4 p-8 lg:p-10">
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300">
              <span class="h-[2px] w-[18px] bg-orange-300"></span>
              Ubicacion
            </span>
            <h2 class="text-2xl font-black leading-tight sm:text-3xl">Ven a conocer el gym.</h2>
            <p class="text-sm leading-6 text-white/70">A pocos minutos del parque, con estacionamiento en la cuadra.</p>
            <p class="flex items-start gap-2 text-sm font-semibold text-white/90">
              <svg class="mt-0.5 h-4 w-4 flex-none text-orange-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s7-7.2 7-12.5A7 7 0 0 0 5 9.5C5 14.8 12 22 12 22z"/><circle cx="12" cy="9.5" r="2.5"/></svg>
              {{ gymAddress }}
            </p>
            <a
              :href="`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(gymAddress)}`"
              target="_blank"
              rel="noopener"
              class="btn-cta mt-1 inline-flex w-fit items-center rounded-full border border-white/25 px-5 py-2.5 text-xs text-white transition hover:bg-white/10"
            >
              Como llegar
            </a>
          </div>
          <div class="min-h-[18rem] lg:min-h-[26rem]">
            <iframe
              :src="mapEmbedUrl"
              title="Mapa de ubicacion de Silver Gym Surco"
              class="h-full min-h-[18rem] w-full border-0 lg:min-h-[26rem]"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              allowfullscreen
            ></iframe>
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
              <a href="#servicios" class="text-sm font-semibold text-white/65 transition hover:text-white">Servicios</a>
              <router-link to="/nosotros" class="text-sm font-semibold text-white/65 transition hover:text-white">Nosotros</router-link>
              <a href="#membresias" class="text-sm font-semibold text-white/65 transition hover:text-white">Membresias</a>
              <a href="#ubicacion" class="text-sm font-semibold text-white/65 transition hover:text-white">Ubicacion</a>
            </nav>
          </div>

          <div>
            <p class="text-xs font-black uppercase tracking-[0.08em] text-orange-300">Contacto</p>
            <div class="mt-4 flex flex-col gap-2.5">
              <span class="flex items-start gap-2 text-sm font-semibold text-white/65">
                <svg class="mt-0.5 h-3.5 w-3.5 flex-none text-orange-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s7-7.2 7-12.5A7 7 0 0 0 5 9.5C5 14.8 12 22 12 22z"/><circle cx="12" cy="9.5" r="2.5"/></svg>
                {{ gymAddress }}
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
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { serviceImages } from '../config/serviceImages';
import { apiGet } from '../services/apiClient';
import heroBanner from '../assets/hero-banner.png';

const route = useRoute();
const router = useRouter();
const showRegistrationNotice = computed(() => String(route.query.registro || '') === 'inicializado');
const registrationCode = computed(() => {
  const id = Number(route.query.solicitud || 0);
  return id > 0 ? `SGCLI${String(id).padStart(3, '0')}` : '';
});

const dismissRegistrationNotice = () => {
  const query = { ...route.query };
  delete query.registro;
  delete query.solicitud;
  router.replace({ path: '/', query });
};

watch(
  showRegistrationNotice,
  (visible) => {
    if (!visible) return;
    setTimeout(() => {
      if (showRegistrationNotice.value) dismissRegistrationNotice();
    }, 6000);
  },
  { immediate: true },
);

const selectedService = ref(null);

const allSchedules = [
  { dia: 'Lunes',     hora: '06:00–07:00', servicio: 'Fitness',     entrenador: 'Diego Alejandro Castro Flores' },
  { dia: 'Lunes',     hora: '18:00–19:00', servicio: 'Musculación', entrenador: 'Andrea Milagros Torres Paredes' },
  { dia: 'Lunes',     hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
  { dia: 'Martes',    hora: '06:00–07:00', servicio: 'Musculación', entrenador: 'Diego Alejandro Castro Flores' },
  { dia: 'Martes',    hora: '19:00–20:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
  { dia: 'Miércoles', hora: '07:00–08:00', servicio: 'Fitness',     entrenador: 'Andrea Milagros Torres Paredes' },
  { dia: 'Miércoles', hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
  { dia: 'Jueves',    hora: '06:00–07:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
  { dia: 'Jueves',    hora: '19:00–20:00', servicio: 'Musculación', entrenador: 'Andrea Milagros Torres Paredes' },
  { dia: 'Viernes',   hora: '07:00–08:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
  { dia: 'Viernes',   hora: '18:00–19:00', servicio: 'Fitness',     entrenador: 'Carlos Eduardo Ramírez Salazar' },
  { dia: 'Viernes',   hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
  { dia: 'Sábado',    hora: '09:00–10:00', servicio: 'Fitness',     entrenador: 'Diego Alejandro Castro Flores' },
  { dia: 'Sábado',    hora: '10:00–11:00', servicio: 'Musculación', entrenador: 'Carlos Eduardo Ramírez Salazar' },
  { dia: 'Sábado',    hora: '11:00–12:00', servicio: 'Baile',       entrenador: 'Andrea Milagros Torres Paredes' },
  { dia: 'Domingo',   hora: '09:00–10:00', servicio: 'Cardio',      entrenador: 'Diego Alejandro Castro Flores' },
];

// Match card title (e.g. "Musculacion") to schedule servicio (e.g. "Musculación")
/**
 * Normaliza el valor recibido.
 */
const normalizeService = (str) =>
  str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const filteredSchedules = computed(() =>
  selectedService.value
    ? allSchedules.filter(
        (s) => normalizeService(s.servicio) === normalizeService(selectedService.value),
      )
    : [],
);

/**
 * Gestiona esta acción de la vista.
 */
const toggleService = (title) => {
  selectedService.value = selectedService.value === title ? null : title;
};

const landingImages = serviceImages;

/**
 * Gestiona esta acción de la vista.
 */
const handleImageError = (event) => {
  event.currentTarget.style.display = 'none';
};

const gymAddress = 'Jirón Vista Alegre 606, Lima 15056';
const mapEmbedUrl = `https://www.google.com/maps?q=${encodeURIComponent(gymAddress)}&output=embed`;
const backendPlans = ref([]);
const defaultPlans = [
  { id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 dias', precio: 79, descripcion: 'Acceso completo por 30 dias para entrenar con flexibilidad.', activo: true },
  { id_pm: 2, nombre_plan: '3 MESES', duracion: '90 dias', precio: 199, descripcion: 'Plan trimestral para sostener progreso y ahorrar frente al pago mensual.', activo: true },
  { id_pm: 3, nombre_plan: 'ANUAL', duracion: '365 dias', precio: 699, descripcion: 'Membresia anual para clientes constantes con mejor precio acumulado.', activo: true },
];

/**
 * Normaliza el valor recibido.
 */
const normalizePlanName = (value) => String(value || '').trim().toUpperCase();
/**
 * Formatea el valor para mostrarlo.
 */
const formatPlanLabel = (value) =>
  normalizePlanName(value)
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const plans = computed(() =>
  (backendPlans.value.length ? backendPlans.value : defaultPlans)
    .filter((plan) => plan.activo ?? plan.active ?? true)
    .map((plan) => {
      const name = normalizePlanName(plan.nombre_plan || plan.name);
      return {
        id: name,
        label: formatPlanLabel(name),
        price: Number(plan.precio ?? plan.price ?? 0),
        description: plan.duracion || plan.description || 'Plan disponible para registro.',
      };
    })
    .filter((plan) => plan.id),
);

/**
 * Consulta los datos del servidor.
 */
const loadPlans = async () => {
  try {
    const list = await apiGet('/planes-membresia');
    backendPlans.value = Array.isArray(list) ? list : [];
  } catch {
    backendPlans.value = defaultPlans;
  }
};

const stats = [
  { label: 'Horario', value: 'Lun a sab' },
  { label: 'Servicios', value: '4 areas' },
  { label: 'Plataforma', value: 'Digital' },
];

const services = [
  { tag: '01', title: 'Fitness', description: 'Entrenamiento general para mantenerte activo y construir habitos saludables.', image: landingImages.fitness, imageClass: 'object-cover object-center' },
  { tag: '02', title: 'Musculacion', description: 'Trabajo de fuerza con horarios definidos y control de cupos.', image: landingImages.musculacion, imageClass: 'object-cover object-center' },
  { tag: '03', title: 'Cardio', description: 'Bloques de entrenamiento para resistencia, energia y salud.', image: landingImages.cardio, imageClass: 'object-cover object-center' },
  { tag: '04', title: 'Baile', description: 'Clases grupales dinamicas para entrenar con movimiento y motivacion.', image: landingImages.baile, imageClass: 'object-cover object-[40%_center]' },
];

onMounted(loadPlans);
</script>

<style scoped>
.landing-page {
  font-family: 'Manrope', 'Segoe UI', 'Trebuchet MS', sans-serif;
}
.landing-page h1,
.landing-page h2,
.landing-page h3 {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
}

.landing-page .btn-cta {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.toast-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.26, 0.64, 1);
}
.toast-slide-leave-active {
  transition: all 0.25s ease-in;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px) translateX(12px) scale(0.96);
}

.toast-close:hover {
  background-color: #d1fae5;
}

.schedule-panel-enter-active {
  transition: all 0.38s cubic-bezier(0.34, 1.26, 0.64, 1);
}
.schedule-panel-leave-active {
  transition: all 0.22s ease-in;
}
.schedule-panel-enter-from {
  opacity: 0;
  transform: translateY(-12px) scaleY(0.96);
}
.schedule-panel-leave-to {
  opacity: 0;
  transform: translateY(-8px) scaleY(0.97);
}

.service-card {
  cursor: pointer;
  -webkit-user-select: none;
  user-select: none;
}

.sched-row:hover {
  background-color: #b91c1c;
}
.sched-row:hover .sched-hour,
.sched-row:hover .sched-name {
  color: #ffffff !important;
}
.sched-row:hover .sched-icon {
  color: rgba(255, 255, 255, 0.85) !important;
}
</style>
