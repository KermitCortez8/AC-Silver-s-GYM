<template>
  <div v-if="total" class="inv-pager text-slate-400">
    <div class="flex flex-wrap items-center gap-4">
      <p>
        Mostrando {{ start + 1 }} a {{ end }} de
        <span class="font-bold text-white">{{ total }}</span> {{ itemLabel }}
      </p>
      <label class="inv-pager-size">
        <span class="whitespace-nowrap">Filas por pagina</span>
        <select :value="pageSize" class="inv-input" @change="changeSize($event.target.value)">
          <option v-for="size in PAGE_SIZES" :key="size" :value="size">{{ size }}</option>
        </select>
      </label>
    </div>
    <nav v-if="totalPages > 1" class="flex items-center gap-1.5" aria-label="Paginacion">
      <button type="button" class="inv-btn-ghost" :disabled="page === 1" @click="emit('update:page', page - 1)">Anterior</button>
      <template v-for="item in pages" :key="item.key">
        <span v-if="item.gap" class="px-1" aria-hidden="true">…</span>
        <button
          v-else
          type="button"
          class="inv-btn-ghost min-w-9"
          :class="{ 'is-active': item.value === page }"
          :aria-current="item.value === page ? 'page' : undefined"
          @click="emit('update:page', item.value)"
        >{{ item.value }}</button>
      </template>
      <button type="button" class="inv-btn-ghost" :disabled="page === totalPages" @click="emit('update:page', page + 1)">Siguiente</button>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { PAGE_SIZES } from '../../../domain/utils/inputRules.js';

const props = defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  total: { type: Number, required: true },
  itemLabel: { type: String, default: 'registros' },
});
const emit = defineEmits(['update:page', 'update:pageSize']);

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const start = computed(() => (props.page - 1) * props.pageSize);
const end = computed(() => Math.min(start.value + props.pageSize, props.total));

// Primera, ultima y las vecinas de la actual; el resto se resume con "…".
const pages = computed(() => {
  const result = [];
  let previous = 0;
  for (let value = 1; value <= totalPages.value; value += 1) {
    if (value === 1 || value === totalPages.value || Math.abs(value - props.page) <= 1) {
      if (value - previous > 1) result.push({ key: `gap-${value}`, gap: true });
      result.push({ key: value, value });
      previous = value;
    }
  }
  return result;
});

const changeSize = (value) => {
  emit('update:pageSize', Number(value));
  emit('update:page', 1);
};
</script>
