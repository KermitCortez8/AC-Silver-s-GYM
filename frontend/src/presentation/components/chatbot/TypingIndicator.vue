<template>
  <div
    aria-label="El asistente está redactando una respuesta"
    class="flex items-center space-x-1.5 bg-white border border-gray-200 rounded-full px-4 py-2.5 w-fit shadow-xs my-1"
    data-purpose="typing-indicator"
  >
    <span class="w-2 h-2 rounded-full bg-[#DC2626] animate-bounce" style="animation-delay: 0ms;" />
    <span class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 150ms;" />
    <span class="w-2 h-2 rounded-full bg-[#DC2626] animate-bounce" style="animation-delay: 300ms;" />
    <span class="text-xs text-gray-500 font-medium ml-1.5">Pensando respuesta...</span>
  </div>
</template>

<script setup>
</script>
