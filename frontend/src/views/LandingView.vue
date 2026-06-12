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
      <section class="relative overflow-hidden">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(220,38,38,0.20),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(127,29,29,0.14),_transparent_36%)]"></div>
        <div class="relative mx-auto grid max-w-[1600px] gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8 lg:py-20">
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

          <div class="rounded-[2rem] border border-orange-100 bg-white p-5 shadow-2xl shadow-orange-900/10">
            <div class="grid min-h-[34rem] gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div class="relative overflow-hidden rounded-[1.5rem] bg-[linear-gradient(160deg,#ef4444_0%,#dc2626_42%,#450a0a_100%)] p-6 text-white">
                <div class="absolute inset-x-6 bottom-6 rounded-3xl bg-white/15 p-5 backdrop-blur">
                  <p class="text-xs font-bold uppercase tracking-[0.22em] text-white/70">Rutina del dia</p>
                  <h2 class="mt-2 text-3xl font-black">Fuerza + cardio</h2>
                  <p class="mt-2 text-sm leading-6 text-white/85">Sesiones guiadas para avanzar con orden, constancia y energia.</p>
                </div>
              </div>

              <div class="grid gap-4">
                <article v-for="service in featuredServices" :key="service.title" class="rounded-[1.5rem] border border-orange-100 bg-[#f5f5f5] p-5">
                  <p class="text-xs font-black uppercase tracking-[0.2em] text-orange-500">{{ service.tag }}</p>
                  <h3 class="mt-2 text-2xl font-black text-slate-950">{{ service.title }}</h3>
                  <p class="mt-2 text-sm leading-6 text-slate-600">{{ service.description }}</p>
                </article>
              </div>
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
          <article v-for="service in services" :key="service.title" class="rounded-2xl border border-orange-100 bg-white p-6 shadow-[0_18px_40px_rgba(127,29,29,0.10)]">
            <p class="text-sm font-black uppercase tracking-[0.22em] text-orange-500">{{ service.tag }}</p>
            <h3 class="mt-4 text-2xl font-black text-slate-950">{{ service.title }}</h3>
            <p class="mt-3 text-sm leading-6 text-slate-600">{{ service.description }}</p>
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
const stats = [
  { label: 'Horario', value: 'Lun a sab' },
  { label: 'Servicios', value: '4 areas' },
  { label: 'Plataforma', value: 'Digital' },
];

const featuredServices = [
  { tag: 'Fitness', title: 'Entrena con energia', description: 'Rutinas para mejorar resistencia, movilidad y condicion fisica.' },
  { tag: 'Musculacion', title: 'Fuerza progresiva', description: 'Espacios y horarios para trabajar tren superior, inferior y core.' },
  { tag: 'Cardio', title: 'Activa tu ritmo', description: 'Sesiones para quemar calorias y mejorar capacidad cardiovascular.' },
];

const services = [
  { tag: '01', title: 'Fitness', description: 'Entrenamiento general para mantenerte activo y construir habitos saludables.' },
  { tag: '02', title: 'Musculacion', description: 'Trabajo de fuerza con horarios definidos y control de cupos.' },
  { tag: '03', title: 'Cardio', description: 'Bloques de entrenamiento para resistencia, energia y salud.' },
  { tag: '04', title: 'Baile', description: 'Clases grupales dinamicas para entrenar con movimiento y motivacion.' },
];

const plans = [
  { id: 'MENSUAL', label: 'Mensual', price: 80, description: 'Ideal para empezar y probar tu rutina semanal.' },
  { id: '3 MESES', label: '3 meses', price: 220, description: 'Mejor equilibrio entre constancia y ahorro.' },
  { id: 'ANUAL', label: 'Anual', price: 780, description: 'Plan completo para entrenar todo el ano.' },
];
</script>
