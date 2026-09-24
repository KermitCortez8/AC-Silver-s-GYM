<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-16 text-center">
    <div class="w-full max-w-5xl">
      <h1 class="text-5xl font-black uppercase leading-tight tracking-tight text-orange-500 sm:text-7xl">
        DE PARTE DE TP REMIX
      </h1>
      <div class="mx-auto mt-10 grid max-w-3xl gap-6 sm:grid-cols-2">
        <img
          :src="rickrollImage"
          alt="Rick Astley bailando en el meme Never Gonna Give You Up"
          width="300"
          height="224"
          class="aspect-[4/3] w-full rounded-2xl border border-orange-500/30 bg-black object-contain shadow-xl"
        />
        <img
          :src="tenorMeme"
          alt="GIF del easter egg TP REMIX"
          width="220"
          height="197"
          class="aspect-[4/3] w-full rounded-2xl border border-orange-500/30 bg-black object-contain shadow-xl"
        />
      </div>
      <router-link
        to="/"
        class="mt-10 inline-flex rounded-full border border-white/30 px-6 py-3 text-sm font-bold text-white transition hover:border-orange-500 hover:text-orange-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-orange-500"
      >
        Volver al inicio
      </router-link>
    </div>
  </main>
</template>

<script setup>
// Fuentes: https://tenor.com/view/never-gonna-give-you-up-rick-astley-rick-roll-gif-11533288
// https://media.tenor.com/B3JcquMOrjYAAAAM/%E5%8F%A4%E5%8A%A0.gif
import rickrollImage from '../assets/tp-remix/rickroll.gif';
import tenorMeme from '../assets/tp-remix/tenor-meme.gif';
</script>
