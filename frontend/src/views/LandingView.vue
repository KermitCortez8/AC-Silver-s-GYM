<template>
  <div class="min-h-screen bg-[#f5f5f5] text-slate-950">
    <header class="sticky top-0 z-40 border-b border-orange-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic tracking-tight text-orange-600">
          Silver Gym Surco
        </router-link>

        <nav class="hidden items-center gap-6 text-sm font-bold uppercase tracking-[0.12em] text-slate-700 lg:flex">
          <a href="#servicios" class="transition hover:text-orange-600">Servicios</a>
          <a href="#membresias" class="transition hover:text-orange-600">Membresias</a>
          <a href="#ubicacion" class="transition hover:text-orange-600">Ubicacion</a>
          <a href="#contacto" class="transition hover:text-orange-600">Contacto</a>
        </nav>

        <div class="flex items-center gap-2">
          <router-link to="/registro" class="rounded-full bg-orange-500 px-4 py-2 text-sm font-black text-white shadow-lg shadow-orange-500/20 transition hover:bg-orange-600">
            Registrarse
          </router-link>
          <router-link to="/login" class="hidden rounded-full border border-orange-300 bg-white px-4 py-2 text-sm font-black text-orange-700 transition hover:bg-orange-50 sm:inline-flex">
            Acceso a plataforma digital
          </router-link>
        </div>
      </div>
    </header>

    <main>
      <section class="relative overflow-hidden bg-white">
        <div class="absolute inset-0">
          <img
            :src="landingImages.fitness"
            alt=""
            class="h-full w-full object-cover"
            @error="handleImageError"
          />
          <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.96)_0%,rgba(255,255,255,0.86)_42%,rgba(255,255,255,0.28)_100%)]"></div>
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.24),_transparent_34%)]"></div>
        </div>
        <div class="relative mx-auto grid max-w-[1600px] gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8 lg:py-20">
          <div class="flex items-center">
            <div class="max-w-2xl">
              <p class="inline-flex rounded-full bg-white px-4 py-2 text-xs font-black uppercase tracking-[0.24em] text-orange-600 shadow-sm">
                Gimnasio, salud y disciplina
              </p>
              <h1 class="mt-6 text-5xl font-black leading-[0.95] text-slate-950 sm:text-6xl lg:text-7xl">
                Entrena fuerte, cerca de casa.
              </h1>
              <p class="mt-6 max-w-xl text-lg leading-8 text-slate-700">
                En Silver Gym Surco ofrecemos entrenamiento funcional, musculacion, cardio y clases grupales con horarios pensados para tu rutina diaria.
              </p>

              <div class="mt-8 flex flex-col gap-3 sm:flex-row">
                <router-link to="/registro" class="rounded-2xl bg-orange-500 px-6 py-4 text-center text-sm font-black uppercase tracking-[0.14em] text-white shadow-xl shadow-orange-500/25 transition hover:-translate-y-0.5 hover:bg-orange-600">
                  Registrarse
                </router-link>
                <router-link to="/login" class="rounded-2xl border border-orange-300 bg-white px-6 py-4 text-center text-sm font-black uppercase tracking-[0.14em] text-orange-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-orange-50">
                  Acceso a plataforma digital
                </router-link>
              </div>

              <div class="mt-8 grid gap-3 sm:grid-cols-3">
                <div v-for="stat in stats" :key="stat.label" class="rounded-2xl border border-orange-100 bg-white/80 p-4 shadow-sm">
                  <p class="text-xs font-bold uppercase tracking-[0.18em] text-orange-500">{{ stat.label }}</p>
                  <p class="mt-2 text-xl font-black text-slate-950">{{ stat.value }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="grid min-h-[34rem] gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div class="relative overflow-hidden rounded-[1.5rem] bg-orange-950 text-white shadow-2xl shadow-orange-900/20">
                <img
                  :src="landingImages.musculacion"
                  alt=""
                  class="h-full min-h-[34rem] w-full object-cover"
                  @error="handleImageError"
                />
                <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.08)_0%,rgba(0,0,0,0.72)_100%)]"></div>
                <div class="absolute inset-x-6 bottom-6 rounded-3xl bg-black/35 p-5 backdrop-blur">
                  <p class="text-xs font-bold uppercase tracking-[0.22em] text-white/70">Rutina del dia</p>
                  <h2 class="mt-2 text-3xl font-black">Fuerza + cardio</h2>
                  <p class="mt-2 text-sm leading-6 text-white/85">Sesiones guiadas para avanzar con orden, constancia y energia.</p>
                </div>
              </div>

              <div class="grid gap-4">
                <article v-for="service in featuredServices" :key="service.title" class="relative min-h-[10rem] overflow-hidden rounded-[1.5rem] bg-slate-950 text-white shadow-xl shadow-slate-900/10">
                  <img
                    :src="service.image"
                    alt=""
                    class="absolute inset-0 h-full w-full object-cover"
                    @error="handleImageError"
                  />
                  <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(0,0,0,0.74)_0%,rgba(0,0,0,0.26)_100%)]"></div>
                  <div class="relative flex h-full min-h-[10rem] flex-col justify-end p-5">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-orange-200">{{ service.tag }}</p>
                    <h3 class="mt-2 text-2xl font-black">{{ service.title }}</h3>
                    <p class="mt-2 text-sm leading-6 text-white/82">{{ service.description }}</p>
                  </div>
                </article>
              </div>
            </div>
        </div>
      </section>

      <section id="servicios" class="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-xs font-black uppercase tracking-[0.28em] text-orange-500">Servicios</p>
            <h2 class="mt-3 max-w-2xl text-4xl font-black leading-tight sm:text-5xl">Todo lo que necesitas para entrenar mejor.</h2>
          </div>
          <p class="max-w-2xl text-base leading-7 text-slate-600">
            Nuestro objetivo es que cada cliente tenga una ruta clara: elegir membresia, matricular horarios y registrar asistencia desde la plataforma digital.
          </p>
        </div>

        <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article v-for="service in services" :key="service.title" class="overflow-hidden rounded-2xl border border-orange-100 bg-white shadow-[0_18px_40px_rgba(127,29,29,0.10)]">
            <div class="h-44 overflow-hidden bg-orange-50 sm:h-52 xl:h-48 2xl:h-56">
              <img
                :src="service.image"
                alt=""
                :class="['h-full w-full', service.imageClass]"
                loading="lazy"
                @error="handleImageError"
              />
            </div>
            <div class="p-6">
              <p class="text-sm font-black uppercase tracking-[0.22em] text-orange-500">{{ service.tag }}</p>
              <h3 class="mt-4 text-2xl font-black text-slate-950">{{ service.title }}</h3>
              <p class="mt-3 text-sm leading-6 text-slate-600">{{ service.description }}</p>
            </div>
          </article>
        </div>
      </section>

      <section id="membresias" class="bg-white px-4 py-16 sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1600px]">
          <div class="rounded-[2rem] bg-[linear-gradient(135deg,#fee2e2_0%,#f5f5f5_50%,#ffffff_100%)] p-6 shadow-xl shadow-orange-900/10 lg:p-8">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p class="text-xs font-black uppercase tracking-[0.28em] text-orange-600">Membresias</p>
                <h2 class="mt-3 text-4xl font-black text-slate-950">Elige el plan que acompane tu ritmo.</h2>
              </div>
              <router-link to="/registro" class="rounded-2xl bg-orange-500 px-5 py-3 text-center text-sm font-black uppercase tracking-[0.14em] text-white transition hover:bg-orange-600">
                Registrarse
              </router-link>
            </div>

            <div class="mt-8 grid gap-4 lg:grid-cols-3">
              <router-link v-for="plan in plans" :key="plan.id" :to="{ path: '/registro', query: { plan: plan.id } }" class="rounded-2xl border border-orange-100 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:border-orange-300">
                <p class="text-sm font-black uppercase tracking-[0.18em] text-orange-500">{{ plan.label }}</p>
                <p class="mt-3 text-4xl font-black text-slate-950">S/ {{ plan.price }}</p>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ plan.description }}</p>
              </router-link>
            </div>
            <p v-if="!plans.length" class="mt-8 rounded-2xl border border-orange-100 bg-white p-5 text-sm font-bold text-slate-600">
              Planes pendientes de configuracion.
            </p>
          </div>
        </div>
      </section>

      <section id="ubicacion" class="bg-[#c90024] px-4 py-14 text-white sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1440px]">
          <h2 class="text-center text-3xl font-black uppercase tracking-[0.04em] sm:text-4xl">
            Ubicacion del Gym
          </h2>
          <p class="mx-auto mt-8 max-w-[1180px] bg-white/20 px-4 py-3 text-center text-base font-bold leading-7 text-white shadow-lg shadow-red-950/10 sm:text-xl">
            {{ gymAddress }}
          </p>
          <div class="mx-auto mt-0 max-w-[1124px] overflow-hidden bg-white shadow-2xl shadow-red-950/30">
            <iframe
              :src="mapEmbedUrl"
              title="Mapa de ubicacion de Silver Gym Surco"
              class="h-[22rem] w-full border-0 sm:h-[32rem] lg:h-[44rem]"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              allowfullscreen
            ></iframe>
          </div>
        </div>
      </section>

      <section id="contacto" class="bg-[#080808] px-4 py-14 text-white sm:px-6 lg:px-8">
        <div class="mx-auto grid max-w-[1600px] gap-6 lg:grid-cols-[1fr_0.8fr] lg:items-center">
          <div>
            <p class="text-xs font-black uppercase tracking-[0.28em] text-amber-300">Contacto</p>
            <h2 class="mt-3 text-4xl font-black">Agenda tu visita o entra a la plataforma.</h2>
            <p class="mt-4 max-w-2xl text-sm leading-7 text-orange-100/80">
              Puedes iniciar tu registro en linea, revisar horarios disponibles y completar el proceso con el administrador.
            </p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <router-link to="/registro" class="rounded-2xl bg-amber-300 px-5 py-4 text-center text-sm font-black uppercase tracking-[0.14em] text-orange-950">
              Registrarse
            </router-link>
            <router-link to="/login" class="rounded-2xl border border-orange-200/30 bg-white/10 px-5 py-4 text-center text-sm font-black uppercase tracking-[0.14em] text-white">
              Acceso a plataforma digital
            </router-link>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { landingImageUrl } from '../config/publicStorage';
import { apiGet } from '../services/apiClient';

const landingImages = {
  fitness: landingImageUrl('fitness.jpg'),
  musculacion: landingImageUrl('musculacion.jpg'),
  cardio: landingImageUrl('cardio.png'),
  baile: landingImageUrl('baile.jpg'),
};

const handleImageError = (event) => {
  event.currentTarget.style.display = 'none';
};

const gymAddress = 'Jirón Vista Alegre 606, Lima 15056';
const mapEmbedUrl = `https://www.google.com/maps?q=${encodeURIComponent(gymAddress)}&output=embed`;
const backendPlans = ref([]);

const normalizePlanName = (value) => String(value || '').trim().toUpperCase();
const formatPlanLabel = (value) =>
  normalizePlanName(value)
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const plans = computed(() =>
  backendPlans.value
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

const loadPlans = async () => {
  try {
    const list = await apiGet('/planes-membresia');
    backendPlans.value = Array.isArray(list) ? list : [];
  } catch {
    backendPlans.value = [];
  }
};

const stats = [
  { label: 'Horario', value: 'Lun a sab' },
  { label: 'Servicios', value: '4 areas' },
  { label: 'Plataforma', value: 'Digital' },
];

const featuredServices = [
  { tag: 'Fitness', title: 'Entrena con energia', description: 'Rutinas para mejorar resistencia, movilidad y condicion fisica.', image: landingImages.fitness },
  { tag: 'Musculacion', title: 'Fuerza progresiva', description: 'Espacios y horarios para trabajar tren superior, inferior y core.', image: landingImages.musculacion },
  { tag: 'Cardio', title: 'Activa tu ritmo', description: 'Sesiones para quemar calorias y mejorar capacidad cardiovascular.', image: landingImages.cardio },
];

const services = [
  { tag: '01', title: 'Fitness', description: 'Entrenamiento general para mantenerte activo y construir habitos saludables.', image: landingImages.fitness, imageClass: 'object-cover object-center' },
  { tag: '02', title: 'Musculacion', description: 'Trabajo de fuerza con horarios definidos y control de cupos.', image: landingImages.musculacion, imageClass: 'object-contain object-center p-2' },
  { tag: '03', title: 'Cardio', description: 'Bloques de entrenamiento para resistencia, energia y salud.', image: landingImages.cardio, imageClass: 'object-contain object-center p-2' },
  { tag: '04', title: 'Baile', description: 'Clases grupales dinamicas para entrenar con movimiento y motivacion.', image: landingImages.baile, imageClass: 'object-cover object-center' },
];

onMounted(loadPlans);
</script>
