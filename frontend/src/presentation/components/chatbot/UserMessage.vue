<template>
  <article class="flex justify-end pt-1 w-full" data-purpose="user-message">
    <div class="max-w-[85%] bg-[#DC2626] text-white px-4 py-2.5 rounded-2xl rounded-tr-sm shadow-sm">
      <p class="text-[14px] leading-snug break-words">
        {{ text }}
      </p>
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
