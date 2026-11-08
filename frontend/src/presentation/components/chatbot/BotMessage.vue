<template>
  <article class="space-y-1 w-full text-left" data-purpose="bot-message">
    <div class="text-[14.5px] leading-relaxed text-gray-800 whitespace-pre-line font-normal pr-2">
      {{ text }}
    </div>
  </article>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    required: true,
  },
});
</script>
