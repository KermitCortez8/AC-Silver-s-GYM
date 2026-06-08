<template>
  <div class="min-h-screen bg-[#f9f4ec] text-slate-950">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-[#ff7a00] text-white shadow-[0_10px_30px_rgba(0,0,0,0.12)]">
      <div class="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <router-link
          to="/"
          class="inline-flex items-center rounded-sm bg-white px-4 py-1 text-lg font-extrabold italic tracking-tight text-[#d61f4d] shadow-[0_6px_18px_rgba(0,0,0,0.12)]"
        >
          Silver Gym Surco
        </router-link>

        <nav class="hidden items-center gap-2 lg:flex">
          <a
            v-for="item in menuItems"
            :key="item.label"
            :href="item.href"
            class="rounded-sm px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition"
            :class="item.active ? 'bg-[#d94b57] text-white' : 'hover:bg-white/10'"
          >
            {{ item.label }}
          </a>
        </nav>

        <a
          href="#contactar"
          class="inline-flex items-center gap-3 rounded-sm bg-[#d94b57] px-5 py-3 text-sm font-semibold shadow-[0_10px_25px_rgba(0,0,0,0.15)] transition hover:bg-[#c63b47]"
        >
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/15 text-base">☎</span>
          <span class="hidden sm:inline">WTSP: 98888-4206</span>
          <span class="sm:hidden">WhatsApp</span>
        </a>
      </div>
    </header>

    <main>
      <section id="inicio" class="relative overflow-hidden bg-[#ef6a18] text-white">
        <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.07)_0%,rgba(255,255,255,0)_28%,rgba(0,0,0,0.05)_100%)]"></div>
        <div class="mx-auto grid max-w-[1600px] gap-8 px-4 py-8 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8 lg:py-10">
          <div class="relative z-10 flex items-center">
            <div class="max-w-xl">
              <div class="inline-flex rounded-sm bg-[#d94b57] px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] shadow-[0_10px_28px_rgba(0,0,0,0.12)]">
                Silver Gym Surco
              </div>
              <h1 class="mt-8 max-w-md text-5xl font-black uppercase leading-[0.95] sm:text-6xl lg:text-7xl">
                Cuidando tu salud
              </h1>
              <p class="mt-8 max-w-lg text-2xl font-medium uppercase leading-tight text-white/95 sm:text-3xl">
                Un paso de ti para formar tu cuerpo y mente.
              </p>
              <p class="mt-6 max-w-lg text-base leading-7 text-white/90 sm:text-lg">
                Entrena en un espacio cómodo, con máquinas profesionales, seguimiento cercano y una rutina diseñada para que avances con constancia.
              </p>

              <div class="mt-8 flex flex-wrap gap-4">
                <router-link
                  to="/registro"
                  class="rounded-sm bg-white px-6 py-4 text-sm font-bold uppercase tracking-[0.14em] text-[#d94b57] transition hover:translate-y-[-1px]"
                >
                  Registrarme
                </router-link>
                <a
                  href="#servicios"
                  class="rounded-sm border border-white/40 bg-white/10 px-6 py-4 text-sm font-bold uppercase tracking-[0.14em] text-white transition hover:bg-white/15"
                >
                  Ver servicios
                </a>
              </div>

              <div class="mt-10 grid gap-3 sm:grid-cols-3">
                <div v-for="item in heroStats" :key="item.label" class="rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur">
                  <p class="text-xs uppercase tracking-[0.3em] text-white/70">{{ item.label }}</p>
                  <p class="mt-2 text-xl font-black">{{ item.value }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="relative z-10">
            <div class="rounded-[2rem] border border-white/20 bg-white/10 p-4 shadow-[0_35px_80px_rgba(0,0,0,0.18)] backdrop-blur-sm sm:p-6">
              <div class="mb-4 flex items-center justify-between gap-4">
                <div class="rounded-sm bg-[#d94b57] px-4 py-2 text-sm font-semibold uppercase tracking-[0.16em]">
                  Silver Gym Surco
                </div>
                <div class="rounded-full bg-white/15 px-4 py-2 text-sm font-semibold">
                  Rutina del día
                </div>
              </div>

              <div class="relative overflow-hidden rounded-[1.8rem] border border-white/15 bg-[linear-gradient(180deg,#fff7ed_0%,#f3e4d1_34%,#d6d2ca_34%,#c9b8a6_100%)] p-4 text-slate-950 shadow-inner">
                <div class="absolute left-0 right-0 top-0 h-14 bg-[linear-gradient(90deg,rgba(255,255,255,0.35),rgba(255,255,255,0))]"></div>
                <div class="absolute left-6 top-6 flex h-10 w-10 items-center justify-center rounded-full bg-black/75 text-xl text-white">‹</div>
                <div class="absolute right-6 top-6 flex h-10 w-10 items-center justify-center rounded-full bg-black/75 text-xl text-white">›</div>

                <div class="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
                  <div class="relative min-h-[24rem] overflow-hidden rounded-[1.5rem] bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.85),_transparent_35%),linear-gradient(180deg,#7b1316_0%,#e65d25_14%,#f3d7c5_14%,#f6efe7_100%)]">
                    <div class="absolute inset-y-0 left-0 w-20 bg-[linear-gradient(180deg,#f2c3ae_0%,#c96a3e_100%)] opacity-90"></div>
                    <div class="absolute left-0 top-14 h-56 w-12 rounded-r-full bg-[#1f2937]/70"></div>
                    <div class="absolute left-14 top-16 h-56 w-3 rounded-full bg-white/90"></div>
                    <div class="absolute left-20 top-20 h-64 w-3 rounded-full bg-white/90"></div>
                    <div class="absolute inset-x-12 bottom-24 h-4 rounded-full bg-[#3b1b16] opacity-90"></div>
                    <div class="absolute inset-x-20 bottom-32 h-20 rounded-3xl bg-[#d73c3f]/90"></div>
                    <div class="absolute right-14 top-20 h-10 w-24 rounded-full bg-white/85"></div>
                    <div class="absolute right-8 bottom-10 h-16 w-16 rounded-[1.2rem] bg-[#7a3a1c]"></div>
                    <div class="absolute inset-x-8 bottom-2 h-28 rounded-[2rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.12),rgba(255,255,255,0.03))] backdrop-blur-sm"></div>
                    <div class="absolute left-6 top-20 rounded-2xl bg-[#d94b57] px-4 py-3 text-white shadow-lg shadow-black/10">
                      <p class="text-xs uppercase tracking-[0.3em] text-white/80">Silver Gym Surco</p>
                      <p class="mt-2 text-2xl font-black uppercase leading-none">Cuidando tu salud</p>
                    </div>
                  </div>

                  <div class="grid gap-4">
                    <div class="rounded-[1.5rem] bg-white p-4 shadow-sm">
                      <p class="text-xs font-bold uppercase tracking-[0.3em] text-[#d94b57]">Horario</p>
                      <p class="mt-2 text-2xl font-black">Lun a sáb</p>
                      <p class="mt-1 text-sm text-slate-500">05:30 - 22:30</p>
                    </div>
                    <div class="rounded-[1.5rem] bg-[#d94b57] p-4 text-white shadow-sm">
                      <p class="text-xs font-bold uppercase tracking-[0.3em] text-white/80">Promoción</p>
                      <p class="mt-2 text-2xl font-black">Matrícula + asesoría</p>
                      <p class="mt-1 text-sm text-white/85">Consulta planes y disponibilidad.</p>
                    </div>
                    <div class="rounded-[1.5rem] bg-white p-4 shadow-sm">
                      <p class="text-xs font-bold uppercase tracking-[0.3em] text-[#d94b57]">Ubicación</p>
                      <p class="mt-2 text-2xl font-black">Surco</p>
                      <p class="mt-1 text-sm text-slate-500">Cerca al parque libre de contaminación.</p>
                    </div>
                    <div class="rounded-[1.5rem] bg-[#1f2937] p-4 text-white shadow-sm">
                      <p class="text-xs font-bold uppercase tracking-[0.3em] text-white/60">Contacto</p>
                      <p class="mt-2 text-2xl font-black">98888-4206</p>
                      <p class="mt-1 text-sm text-white/75">Escríbenos por WhatsApp para reservar.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-[#c8102e] px-4 py-5 text-center text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1500px] text-sm font-medium uppercase leading-7 tracking-[0.14em] sm:text-base">
          <p>Máquinas profesionales, junto al parque libre de contaminación.</p>
          <p>Nuestro objetivo es contribuir con la salud de la vecindad.</p>
          <p>Puedes lograr el cuerpo que siempre deseaste, sin estar lejos de casa.</p>
        </div>
      </section>

      <section id="servicios" class="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-8 lg:py-20">
        <div class="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div class="space-y-6">
            <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-[#d94b57]">Servicios</p>
            <h2 class="max-w-xl text-4xl font-black leading-tight sm:text-5xl">Entrena con un ambiente directo, limpio y enfocado en resultados.</h2>
            <p class="max-w-2xl text-lg leading-8 text-slate-700">
              Esta landing concentra la primera impresión que se ve en la captura: una propuesta clara, un acceso visible y una mezcla de energía comercial con información práctica.
            </p>

            <div class="grid gap-4 sm:grid-cols-2">
              <article v-for="feature in features" :key="feature.title" class="rounded-[1.8rem] border border-[#e8d7c1] bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
                <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#ffe4c0] text-2xl">{{ feature.icon }}</div>
                <h3 class="mt-4 text-xl font-bold text-slate-950">{{ feature.title }}</h3>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ feature.description }}</p>
              </article>
            </div>
          </div>

          <div class="rounded-[2rem] border border-[#e8d7c1] bg-white p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
            <div class="flex items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-[#d94b57]">Membresías</p>
                <h3 class="mt-2 text-2xl font-black text-slate-950">Planes pensados para adherencia.</h3>
              </div>
              <div class="rounded-full bg-[#fef2f2] px-4 py-2 text-sm font-semibold text-[#d94b57]">Disponible hoy</div>
            </div>

            <div class="mt-6 grid gap-4">
              <router-link v-for="plan in plans" :key="plan.name" :to="{ path: '/registro', query: { plan: plan.id } }" class="rounded-[1.5rem] border border-slate-100 bg-[#faf7f2] p-5 transition hover:border-[#d94b57]/40">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-lg font-bold text-slate-950">{{ plan.name }}</p>
                    <p class="mt-1 text-sm text-slate-600">{{ plan.summary }}</p>
                  </div>
                  <p class="text-right text-2xl font-black text-[#d94b57]">{{ plan.price }}</p>
                </div>
                <div class="mt-4 flex flex-wrap gap-2">
                  <span v-for="tag in plan.tags" :key="tag" class="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{{ tag }}</span>
                </div>
              </router-link>
            </div>

            <div class="mt-6 grid gap-4 sm:grid-cols-3">
              <div class="rounded-[1.5rem] bg-[#fff4ea] p-4 text-center">
                <p class="text-3xl font-black text-[#d94b57]">24/7</p>
                <p class="mt-2 text-sm text-slate-600">Respuesta por WhatsApp</p>
              </div>
              <div class="rounded-[1.5rem] bg-[#fff4ea] p-4 text-center">
                <p class="text-3xl font-black text-[#d94b57]">+30</p>
                <p class="mt-2 text-sm text-slate-600">Máquinas y estaciones</p>
              </div>
              <div class="rounded-[1.5rem] bg-[#fff4ea] p-4 text-center">
                <p class="text-3xl font-black text-[#d94b57]">100%</p>
                <p class="mt-2 text-sm text-slate-600">Enfoque en salud</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="galeria" class="bg-[#f3e4d1] px-4 py-16 sm:px-6 lg:px-8">
        <div class="mx-auto max-w-[1600px]">
          <div class="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-[#d94b57]">Galería</p>
              <h2 class="mt-2 text-3xl font-black sm:text-4xl">Una estética cálida, directa y en movimiento.</h2>
            </div>
            <p class="max-w-xl text-sm leading-7 text-slate-600">
              El bloque visual replica la energía de la referencia: una cabecera intensa, un hero con sensación de carrusel y una banda informativa fuerte.
            </p>
          </div>

          <div class="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div class="rounded-[2rem] bg-[linear-gradient(180deg,#fb7b1a_0%,#e75032_38%,#621216_100%)] p-6 text-white shadow-[0_28px_70px_rgba(15,23,42,0.18)]">
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="rounded-[1.5rem] bg-white/12 p-5 backdrop-blur">
                  <p class="text-xs uppercase tracking-[0.35em] text-white/70">Cobertura</p>
                  <p class="mt-2 text-3xl font-black">Mañana a noche</p>
                  <p class="mt-2 text-sm leading-6 text-white/85">Horarios amplios para adaptarse a la rutina laboral y al descanso.</p>
                </div>
                <div class="rounded-[1.5rem] bg-white/12 p-5 backdrop-blur">
                  <p class="text-xs uppercase tracking-[0.35em] text-white/70">Atención</p>
                  <p class="mt-2 text-3xl font-black">Personal cercana</p>
                  <p class="mt-2 text-sm leading-6 text-white/85">Acompañamiento simple para que la primera visita no se sienta pesada.</p>
                </div>
              </div>
              <div class="mt-4 grid gap-4 sm:grid-cols-[1.1fr_0.9fr]">
                <div class="rounded-[1.5rem] bg-white p-5 text-slate-950">
                  <p class="text-xs font-bold uppercase tracking-[0.35em] text-[#d94b57]">Acceso rápido</p>
                  <p class="mt-2 text-xl font-black">Reserva, paga y entrena.</p>
                  <p class="mt-2 text-sm leading-6 text-slate-600">La experiencia comienza con una llamada clara a la acción.</p>
                </div>
                <div class="rounded-[1.5rem] border border-white/20 bg-black/25 p-5">
                  <p class="text-xs font-bold uppercase tracking-[0.35em] text-white/70">Mapa de la página</p>
                  <div class="mt-4 space-y-3 text-sm">
                    <div class="flex items-center justify-between rounded-full bg-white/10 px-4 py-2"><span>Inicio</span><span>01</span></div>
                    <div class="flex items-center justify-between rounded-full bg-white/10 px-4 py-2"><span>Servicios</span><span>02</span></div>
                    <div class="flex items-center justify-between rounded-full bg-white/10 px-4 py-2"><span>Contacto</span><span>03</span></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid gap-4">
              <div class="rounded-[2rem] bg-white p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
                <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-[#d94b57]">Ubicación</p>
                <h3 class="mt-3 text-2xl font-black">Zona tranquila, cerca al parque.</h3>
                <p class="mt-3 text-sm leading-7 text-slate-600">Un entorno que refuerza la sensación de bienestar que muestra la imagen de referencia.</p>
              </div>
              <div class="rounded-[2rem] bg-[#1f2937] p-6 text-white shadow-[0_24px_60px_rgba(15,23,42,0.16)]">
                <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-white/60">Contacto</p>
                <h3 class="mt-3 text-2xl font-black">98888-4206</h3>
                <p class="mt-3 text-sm leading-7 text-white/80">Escríbenos para reservar tu visita, revisar planes o pedir una rutina inicial.</p>
              </div>
              <div class="rounded-[2rem] border border-dashed border-[#d94b57]/25 bg-white p-6 text-center text-[#d94b57] shadow-[0_24px_60px_rgba(15,23,42,0.05)]">
                <p class="text-sm font-bold uppercase tracking-[0.45em]">Empieza hoy</p>
                <p class="mt-2 text-2xl font-black">Tu mejor versión no espera.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="contactar" class="bg-[#111827] px-4 py-12 text-white sm:px-6 lg:px-8">
        <div class="mx-auto grid max-w-[1600px] gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p class="text-[0.7rem] font-bold uppercase tracking-[0.45em] text-[#ffb36b]">Contacto directo</p>
            <h2 class="mt-3 text-3xl font-black sm:text-4xl">Agenda tu visita y recibe orientación inicial.</h2>
            <p class="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
              El objetivo de esta landing es convertir rápido, con una estructura visual fuerte y un mensaje claro, igual que la captura.
            </p>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <a href="mailto:contacto@silvergymsurco.pe" class="rounded-[1.5rem] bg-white/8 p-5 transition hover:bg-white/12">
              <p class="text-xs uppercase tracking-[0.35em] text-slate-400">Correo</p>
              <p class="mt-2 text-xl font-bold">contacto@silvergymsurco.pe</p>
            </a>
            <a href="tel:+51988884206" class="rounded-[1.5rem] bg-[#d94b57] p-5 transition hover:bg-[#c83d48]">
              <p class="text-xs uppercase tracking-[0.35em] text-white/80">WhatsApp</p>
              <p class="mt-2 text-xl font-bold">98888-4206</p>
            </a>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const menuItems = computed(() => [
  { label: 'Inicio', href: '#inicio', active: true },
  { label: 'Reservar', href: '#contactar', active: false },
  { label: 'Servicios', href: '#servicios', active: false },
  { label: 'Maquinas', href: '#galeria', active: false },
  { label: 'Ubicacion', href: '#contactar', active: false },
]);

const heroStats = [
  { label: 'Horario', value: 'Lun a sáb' },
  { label: 'Respuesta', value: 'WhatsApp' },
  { label: 'Ubicación', value: 'Surco' },
];

const features = [
  {
    icon: '⟡',
    title: 'Máquinas profesionales',
    description: 'Un entorno pensado para entrenar con seguridad, orden visual y una sensación de amplitud.',
  },
  {
    icon: '⌁',
    title: 'Asesoría cercana',
    description: 'Una propuesta clara para quienes recién empiezan y también para quienes ya siguen rutina.',
  },
  {
    icon: '◍',
    title: 'Planes flexibles',
    description: 'La estructura comercial deja el acceso directo a reservas y contacto sin fricción.',
  },
  {
    icon: '↯',
    title: 'Energía de barrio',
    description: 'Diseño cálido, directo y con presencia, como el gimnasio real al que apunta la marca.',
  },
];

const plans = [
  {
    id: 'MENSUAL',
    name: 'Mensual',
    summary: 'Ideal para entrenar de forma constante.',
    price: 'S/ 80',
    tags: ['Acceso completo', 'Sin complicaciones'],
  },
  {
    id: '3 MESES',
    name: '3 meses',
    summary: 'Mejor equilibrio entre compromiso y ahorro.',
    price: 'S/ 220',
    tags: ['Ahorro', 'Seguimiento'],
  },
  {
    id: 'ANUAL',
    name: 'Anual',
    summary: 'Entrena todo el año con el mejor precio.',
    price: 'S/ 780',
    tags: ['Completo', 'Mejor valor'],
  },
];
</script>
