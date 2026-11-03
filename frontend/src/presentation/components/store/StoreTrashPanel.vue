<template>
  <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
    <div>
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Eliminados</p>
      <h2 class="mt-2 text-2xl font-black text-white">Papelera</h2>
      <p class="mt-1.5 text-sm text-slate-400">
        Productos eliminados de la Tienda junto con su articulo de Inventario. Restaura para volver a venderlos
        o elimina para sacarlos para siempre.
      </p>
    </div>

    <div class="mt-4">
      <TableSearch
        v-model="busqueda"
        label="Buscar en la papelera por N° o nombre"
        placeholder="Buscar por N° de producto o nombre"
        @update:model-value="pagina = 1"
      />
    </div>

    <p v-if="feedback" role="status" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass(feedbackTone)">
      {{ feedback }}
    </p>

    <div v-if="filtrados.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm store-admin-table">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th class="px-5 py-4 font-bold">N° producto</th>
              <th class="px-4 py-4 font-bold">Nombre</th>
              <th class="px-4 py-4 font-bold">Imagen</th>
              <th class="px-4 py-4 font-bold">Categoría</th>
              <th class="px-4 py-4 font-bold">Precio</th>
              <th class="px-4 py-4 font-bold">Stock</th>
              <th class="px-5 py-4 text-right font-bold">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="producto in paginados" :key="producto.id_producto" class="transition hover:bg-white/[0.04]">
              <td data-label="N° producto" class="whitespace-nowrap px-5 py-4 align-top">
                <span class="rounded-lg bg-slate-400/10 px-2.5 py-1 text-xs font-bold text-slate-300">
                  {{ productCode(producto.id_producto) }}
                </span>
              </td>
              <td data-label="Nombre" class="max-w-xs px-4 py-4 align-top">
                <p class="font-bold text-white">{{ producto.nombre }}</p>
                <p class="mt-1 line-clamp-1 text-xs leading-5 text-slate-400">{{ producto.descripcion || 'Sin descripción' }}</p>
              </td>
              <td data-label="Imagen" class="px-4 py-4 align-top">
                <img
                  v-if="producto.imagen_url"
                  :src="producto.imagen_url"
                  :alt="producto.nombre"
                  class="h-14 w-14 rounded-xl border border-white/10 bg-slate-950/60 object-contain p-1 opacity-70"
                />
                <span v-else class="text-xs text-slate-500">Sin imagen</span>
              </td>
              <td data-label="Categoría" class="px-4 py-4 align-top text-slate-200">{{ producto.categoria || 'General' }}</td>
              <td data-label="Precio" class="whitespace-nowrap px-4 py-4 align-top font-bold text-slate-200">
                S/. {{ Number(producto.precio || 0).toFixed(2) }}
              </td>
              <td data-label="Stock" class="px-4 py-4 align-top text-slate-200">
                {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
              </td>
              <td data-label="Acciones" class="px-5 py-4 align-top">
                <div class="flex justify-end gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-sm font-bold text-emerald-200 transition hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="busyId === producto.id_producto"
                    @click="restaurar(producto)"
                  >
                    <RotateCcw :size="15" aria-hidden="true" /> Restaurar
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-300 transition hover:bg-rose-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="busyId === producto.id_producto"
                    @click="eliminar(producto)"
                  >
                    <Trash2 :size="15" aria-hidden="true" /> Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <TablePager v-model:page="pagina" v-model:pageSize="porPagina" :total="filtrados.length" item-label="productos" />

    <div v-if="!filtrados.length" class="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
      <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-slate-900">
        <Trash2 :size="24" class="text-slate-500" aria-hidden="true" />
      </div>
      <p class="text-sm font-semibold text-slate-300">{{ busqueda ? 'Sin resultados' : 'La papelera esta vacia' }}</p>
      <p class="mt-1 text-xs text-slate-500">
        {{ busqueda ? 'Prueba con otro N° o nombre.' : 'Los productos que elimines en la pestaña Productos apareceran aqui.' }}
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { RotateCcw, Trash2 } from 'lucide-vue-next';
import TablePager from '../common/TablePager.vue';
import TableSearch from '../common/TableSearch.vue';
import { feedbackClass } from '../../utils/feedback.js';
import { DEFAULT_PAGE_SIZE, matchesSearch } from '../../../domain/utils/inputRules.js';
import { useGymStore } from '../../../application/stores/gymStore';

const props = defineProps({ productCode: { type: Function, required: true } });
const gymStore = useGymStore();

const busqueda = ref('');
const pagina = ref(1);
const porPagina = ref(DEFAULT_PAGE_SIZE);
const feedback = ref('');
const feedbackTone = ref('info');
const busyId = ref(null);

const filtrados = computed(() => gymStore.papelera_tienda
  .filter((p) => matchesSearch(busqueda.value, [props.productCode(p.id_producto), p.nombre])));
const paginados = computed(() => filtrados.value.slice((pagina.value - 1) * porPagina.value, pagina.value * porPagina.value));

const ejecutar = async (producto, accion, mensaje) => {
  busyId.value = producto.id_producto;
  try {
    const result = await accion(producto.id_producto);
    feedbackTone.value = 'success';
    feedback.value = mensaje(result);
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo completar la accion.';
  } finally {
    busyId.value = null;
  }
};

const restaurar = (producto) => ejecutar(producto, gymStore.restoreProductoTienda,
  () => `${producto.nombre} se restauro en la Tienda y su articulo volvio a Inventario.`);

const eliminar = (producto) => {
  if (!window.confirm(`Eliminar "${producto.nombre}" para siempre?\n\nYa no se podra restaurar. Si tiene ventas o movimientos, ese historial se conserva.`)) return;
  return ejecutar(producto, gymStore.purgeProductoTienda, (result) => (result?.producto === 'oculto'
    ? `${producto.nombre} se elimino. Tenia ventas registradas: su historial se conserva.`
    : `${producto.nombre} se elimino definitivamente.`));
};
</script>

<style scoped src="../../styles/store-view.css"></style>
