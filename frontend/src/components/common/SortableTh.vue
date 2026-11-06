<template>
  <th :aria-sort="ariaSort">
    <button type="button" class="inv-sort" :class="{ 'is-active': isActive }" :title="title" @click="emit('sort', column)">
      {{ label }}
      <component :is="icon" :size="14" aria-hidden="true" />
    </button>
  </th>
</template>

<script setup>
import { computed } from 'vue';
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-vue-next';

const props = defineProps({
  label: { type: String, required: true },
  column: { type: String, required: true },
  sortKey: { type: String, default: '' },
  sortDir: { type: String, default: 'asc' },
  numeric: Boolean,
});
const emit = defineEmits(['sort']);

const isActive = computed(() => props.sortKey === props.column);
const icon = computed(() => {
  if (!isActive.value) return ArrowUpDown;
  return props.sortDir === 'asc' ? ArrowUp : ArrowDown;
});
const ariaSort = computed(() => {
  if (!isActive.value) return 'none';
  return props.sortDir === 'asc' ? 'ascending' : 'descending';
});
const title = computed(() => {
  const [asc, desc] = props.numeric ? ['menor a mayor', 'mayor a menor'] : ['A-Z', 'Z-A'];
  if (!isActive.value) return `Ordenar ${asc}`;
  return props.sortDir === 'asc' ? `Ordenado ${asc}. Clic para ${desc}` : `Ordenado ${desc}. Clic para ${asc}`;
});
</script>
