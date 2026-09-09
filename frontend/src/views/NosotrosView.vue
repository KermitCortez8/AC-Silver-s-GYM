<template>
  <div class="nosotros-page min-h-screen bg-[#faf7f5] text-slate-950">
    <header class="sticky top-0 z-40 border-b border-orange-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic tracking-tight text-orange-600">
          Silver Gym Surco
        </router-link>

        <nav class="hidden items-center gap-6 text-sm font-bold uppercase tracking-[0.04em] text-slate-700 lg:flex">
          <router-link :to="{ path: '/', hash: '#servicios' }" class="transition hover:text-orange-600">Servicios</router-link>
          <router-link to="/nosotros" class="text-orange-600">Nosotros</router-link>
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
      <!-- Intro -->
      <section class="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-8">
        <div class="grid gap-10 lg:grid-cols-[1fr_0.95fr] lg:items-center">
          <div>
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-500">
              <span class="h-[2px] w-[18px] bg-orange-500"></span>
              Nosotros
            </span>
            <h1 class="mt-5 text-4xl font-black leading-[1.05] text-slate-950 sm:text-5xl">
              Mas que un gimnasio,<br /><span class="text-orange-500">tu segundo lugar de entrenamiento.</span>
            </h1>
            <p class="mt-6 max-w-[52ch] text-lg leading-8 text-slate-600">
              En Silver Gym Surco creemos que entrenar es mas facil cuando tienes un espacio cercano, ordenado y un equipo que conoce tu progreso. Por eso construimos una rutina completa: musculacion, cardio, clases grupales y una plataforma digital para llevar todo en un solo lugar.
            </p>
            <p class="mt-4 max-w-[52ch] text-lg leading-8 text-slate-600">
              Nuestro objetivo no es solo que vengas a entrenar, sino que encuentres un lugar donde te sientas comodo para volver cada semana.
            </p>
          </div>
          <div class="relative overflow-hidden rounded-[1.75rem] shadow-2xl shadow-red-950/10 lg:min-h-[24rem]">
            <img :src="heroBanner" alt="" class="absolute inset-0 h-full w-full object-cover" />
            <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,12,11,0.05)_0%,rgba(15,12,11,0.55)_100%)]"></div>
          </div>
        </div>
      </section>

      <!-- Historia -->
      <section class="bg-[#141110] px-4 py-16 text-white sm:px-6 lg:px-8">
        <div class="mx-auto grid max-w-[1600px] gap-10 lg:grid-cols-[0.95fr_1fr] lg:items-center">
          <div class="relative overflow-hidden rounded-[1.75rem] shadow-2xl shadow-red-950/20 lg:min-h-[22rem]">
            <img :src="historiaImage" alt="" class="absolute inset-0 h-full w-full object-cover" />
            <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,12,11,0.05)_0%,rgba(15,12,11,0.55)_100%)]"></div>
          </div>
          <div>
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300">
              <span class="h-[2px] w-[18px] bg-orange-300"></span>
              Historia
            </span>
            <h2 class="mt-3 text-3xl font-black leading-tight sm:text-4xl">Sed do eiusmod tempor incididunt.</h2>
            <p class="mt-4 text-sm leading-7 text-white/65">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </p>
            <p class="mt-4 text-sm leading-7 text-white/65">
              Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
            </p>
          </div>
        </div>
      </section>

      <!-- Mision y Vision -->
      <section class="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-8">
        <div class="grid gap-6 lg:grid-cols-2">
          <div class="rounded-2xl border border-orange-100 bg-white p-8 shadow-[0_18px_40px_rgba(127,29,29,0.08)]">
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-500">
              <span class="h-[2px] w-[18px] bg-orange-500"></span>
              Mision
            </span>
            <h2 class="mt-3 text-2xl font-black leading-tight text-slate-950 sm:text-3xl">Lorem ipsum dolor sit amet.</h2>
            <p class="mt-4 text-sm leading-7 text-slate-600">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </p>
          </div>
          <div class="rounded-2xl border border-orange-100 bg-white p-8 shadow-[0_18px_40px_rgba(127,29,29,0.08)]">
            <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-500">
              <span class="h-[2px] w-[18px] bg-orange-500"></span>
              Vision
            </span>
            <h2 class="mt-3 text-2xl font-black leading-tight text-slate-950 sm:text-3xl">Consectetur adipiscing elit.</h2>
            <p class="mt-4 text-sm leading-7 text-slate-600">
              Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
            </p>
          </div>
        </div>
      </section>

      <!-- Valores -->
      <section class="bg-[#141110] px-4 py-16 text-white sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1600px]">
          <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300">
            <span class="h-[2px] w-[18px] bg-orange-300"></span>
            Por que entrenar aqui
          </span>
          <h2 class="mt-3 max-w-2xl text-3xl font-black leading-tight sm:text-4xl">Lo que nos hace diferentes.</h2>

          <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div
              v-for="value in values"
              :key="value.title"
              class="rounded-2xl border border-white/15 p-6 transition hover:-translate-y-1 hover:border-white/30"
            >
              <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-orange-300">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  v-html="value.icon"
                ></svg>
              </div>
              <h3 class="mt-4 text-lg font-black text-white">{{ value.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-white/60">{{ value.description }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Resenas -->
      <section class="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-8">
        <span class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-500">
          <span class="h-[2px] w-[18px] bg-orange-500"></span>
          Resenas
        </span>
        <h2 class="mt-3 max-w-2xl text-3xl font-black leading-tight sm:text-4xl">Ut enim ad minim veniam.</h2>

        <div class="mt-8 grid gap-5 md:grid-cols-3">
          <div
            v-for="review in reviews"
            :key="review.name"
            class="rounded-2xl border border-orange-100 bg-white p-6 shadow-[0_18px_40px_rgba(127,29,29,0.08)]"
          >
            <div class="flex items-center gap-1 text-orange-400">
              <svg v-for="n in 5" :key="n" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 1.5l2.6 5.6 6.1.6-4.6 4.1 1.3 6-5.4-3.1-5.4 3.1 1.3-6-4.6-4.1 6.1-.6z" />
              </svg>
            </div>
            <p class="mt-4 text-sm leading-7 text-slate-600">"{{ review.quote }}"</p>
            <div class="mt-5 flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-full bg-orange-100 text-sm font-black text-orange-600">{{ review.initial }}</div>
              <div>
                <p class="text-sm font-black text-slate-950">{{ review.name }}</p>
                <p class="text-xs text-slate-500">{{ review.role }}</p>
              </div>
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
import { serviceImages } from '../config/serviceImages';
import heroBanner from '../assets/hero-banner.png';

const gymAddress = 'Jirón Vista Alegre 606, Lima 15056';

const historiaImage = serviceImages.musculacion;

const values = [
  {
    title: 'Entrenamiento guiado',
    description: 'Rutinas y clases pensadas para cada nivel, desde el primer dia.',
    icon: '<path d="M9 12l2 2 4-4M7 4h10a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6a2 2 0 012-2z" />',
  },
  {
    title: 'Ambiente cercano',
    description: 'Un equipo que conoce tu progreso y te acompana en cada sesion.',
    icon: '<path d="M20.8 8.6c0 4.6-8.8 10-8.8 10s-8.8-5.4-8.8-10a4.6 4.6 0 018.8-1.8 4.6 4.6 0 018.8 1.8z" />',
  },
  {
    title: 'Equipamiento completo',
    description: 'Zona de musculacion, cardio y espacio para clases grupales.',
    icon: '<path d="M3 12h3M18 12h3M8 8v8M16 8v8M8 12h8" />',
  },
  {
    title: 'Horarios flexibles',
    description: 'Bloques de lunes a sabado para que entrenes segun tu rutina.',
    icon: '<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />',
  },
];

const reviews = [
  {
    name: 'Lorem Ipsum',
    initial: 'L',
    role: 'Socio desde 2024',
    quote: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore.',
  },
  {
    name: 'Dolor Sit',
    initial: 'D',
    role: 'Socia desde 2023',
    quote: 'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo.',
  },
  {
    name: 'Amet Consectetur',
    initial: 'A',
    role: 'Socio desde 2025',
    quote: 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
  },
];
</script>

<style scoped>
.nosotros-page {
  font-family: 'Manrope', 'Segoe UI', 'Trebuchet MS', sans-serif;
}
.nosotros-page h1,
.nosotros-page h2,
.nosotros-page h3 {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
}
.nosotros-page .btn-cta {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
</style>
