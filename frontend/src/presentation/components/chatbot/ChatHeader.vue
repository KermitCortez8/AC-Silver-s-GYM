<template>
  <header
    class="flex-none bg-white border-b border-gray-100 px-4 py-3 pt-safe flex items-center justify-between z-20 shadow-xs relative"
    data-purpose="chat-header"
  >
    <!-- Barra superior de acento deportiva -->
    <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-red-500 to-orange-500"></div>

    <!-- Identidad e Información de Silver -->
    <div class="flex items-center space-x-3 mt-0.5">
      <!-- Avatar con indicador de estado online -->
      <div class="relative">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-red-600 to-red-700 text-white flex items-center justify-center font-black shadow-md shadow-red-600/20">
          <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
          </svg>
        </div>
        <!-- Punto verde pulsante (Online) -->
        <span class="absolute bottom-0 right-0 flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-white"></span>
        </span>
      </div>

      <!-- Textos informativos -->
      <div class="flex flex-col">
        <div class="flex items-center space-x-1.5">
          <span class="font-oswald text-xl font-black italic tracking-wide uppercase text-gray-900 leading-none">
            Silver
          </span>
          <span class="text-[9px] font-extrabold uppercase tracking-wider bg-red-50 text-red-600 border border-red-100 rounded-md px-1.5 py-0.5">
            IA Oficial
          </span>
        </div>
        <p class="text-[11px] font-medium text-gray-500 mt-0.5 flex items-center gap-1">
          <span>Silver Gym Surco</span>
          <span>·</span>
          <span class="text-emerald-600 font-semibold">En línea</span>
        </p>
      </div>
    </div>

    <!-- Botón Cerrar (Target accesible 44x44px con micro-rotación) -->
    <button
      type="button"
      @click="$emit('close')"
      aria-label="Cerrar ventana de chat"
      class="w-10 h-10 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-all focus:outline-none focus:ring-2 focus:ring-[#DC2626] group"
    >
      <svg
        class="w-5 h-5 stroke-current stroke-[2.2] transition-transform duration-200 group-hover:rotate-90"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </header>
</template>

<script setup>
defineEmits(['close']);
</script>
