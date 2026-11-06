<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Ventas</p>
          <h1 class="mt-2 text-3xl font-black text-white">Promociones y descuentos</h1>
          <p class="mt-2 text-slate-300">Administra ofertas con cuota de personas, límite de cupos y vista previa en tiempo real.</p>
        </div>
        <button class="flex items-center gap-2 rounded-2xl bg-rose-500 px-5 py-3 font-black text-white transition hover:bg-rose-400 shadow-lg shadow-rose-500/20 cursor-pointer" @click="openNewModal">
          <i class="fa-solid fa-plus"></i> Nueva promoción
        </button>
      </div>
    </section>

    <!-- Modal de Notificación / Alerta -->
    <Teleport to="body">
      <div v-if="feedback" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-all">
        <div class="w-full max-w-md rounded-3xl border bg-slate-900 p-6 shadow-2xl space-y-5" :class="feedbackTone === 'error' ? 'border-rose-500/40' : 'border-blue-500/40'">
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-2xl flex items-center justify-center text-lg shrink-0 shadow-inner" :class="feedbackTone === 'error' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'">
                <i :class="feedbackTone === 'error' ? 'fa-solid fa-triangle-exclamation' : 'fa-solid fa-circle-check'"></i>
              </div>
              <div>
                <h3 class="text-base font-black text-white">
                  {{ feedbackTone === 'error' ? 'Aviso del Sistema' : '¡Promoción Guardada!' }}
                </h3>
                <p class="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Notificación</p>
              </div>
            </div>
            <button type="button" class="h-8 w-8 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-base transition cursor-pointer" @click="feedback = ''" title="Cerrar">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="app-notice p-4 rounded-2xl border" :class="feedbackTone === 'error' ? 'app-notice--error' : 'app-notice--info'">
            <p class="text-sm font-medium text-slate-200 leading-relaxed">
              {{ feedback }}
            </p>
          </div>

          <div class="flex justify-end pt-1">
            <button type="button" @click="feedback = ''" :class="feedbackTone === 'error' ? 'bg-rose-500 hover:bg-rose-400 shadow-rose-500/25' : 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/25'" class="w-full sm:w-auto px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-wider text-white transition-all shadow-lg cursor-pointer">
              Entendido
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal de Confirmación de Eliminación -->
    <Teleport to="body">
      <div v-if="promoToDelete" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-all">
        <div class="w-full max-w-md rounded-3xl border border-rose-500/30 bg-slate-900 p-6 shadow-2xl space-y-6">
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-2xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xl shrink-0 shadow-inner">
                <i class="fa-solid fa-trash-can"></i>
              </div>
              <div>
                <h3 class="text-base font-black text-white">¿Eliminar Promoción?</h3>
                <p class="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Confirmación requerida</p>
              </div>
            </div>
            <button type="button" class="h-8 w-8 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-base transition cursor-pointer" :disabled="deleting" @click="promoToDelete = null" title="Cerrar">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="p-4 rounded-2xl bg-slate-950/70 border border-white/5 space-y-1">
            <p class="text-sm font-medium text-slate-300">
              ¿Estás seguro de que deseas eliminar la promoción <span class="font-black text-white">"{{ promoToDelete.name }}"</span>?
            </p>
            <p class="text-xs text-rose-400/80 font-semibold">Esta acción no se puede deshacer.</p>
          </div>

          <p v-if="deleteError" role="alert" class="app-notice app-notice--error rounded-xl border px-4 py-3 text-sm">{{ deleteError }}</p>
          <div class="flex items-center justify-end gap-3 pt-1">
            <button type="button" class="px-5 py-2.5 rounded-xl border border-white/10 bg-slate-800 text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-700 transition cursor-pointer" :disabled="deleting" @click="promoToDelete = null">
              Cancelar
            </button>
            <button type="button" class="px-6 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-400 text-xs font-black uppercase tracking-wider text-white transition shadow-lg shadow-rose-500/25 flex items-center gap-2 cursor-pointer" :disabled="deleting" @click="confirmDelete">
              <i class="fa-solid fa-trash-can"></i> Sí, Eliminar
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- KPIs Section -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Promociones Activas</p>
          <i class="fa-solid fa-check text-emerald-400 bg-emerald-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-3xl font-black text-white">{{ activePromotionsCount }}</p>
        <p class="mt-2 text-xs text-emerald-400">Reglas comerciales vigentes</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Descuentos Aplicados</p>
          <i class="fa-solid fa-dollar-sign text-orange-500 bg-orange-400/10 p-2 rounded-full text-xs px-3"></i>
        </div>
        <p class="mt-4 text-3xl font-black text-white">S/. {{ totalAhorrado.toFixed(2) }}</p>
        <p class="mt-2 text-xs text-slate-400">Ahorrados a clientes este mes</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Conversión en Caja</p>
          <i class="fa-solid fa-arrow-trend-up text-rose-400 bg-rose-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-3xl font-black text-white">{{ porcentajeVentasConPromo.toFixed(1) }}%</p>
        <p class="mt-2 text-xs text-slate-400">Ventas con cupón o promo</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Ticket Promedio</p>
          <i class="fa-solid fa-lock text-cyan-400 bg-cyan-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-3xl font-black text-white">S/. {{ ticketMedioConDescuento.toFixed(2) }}</p>
        <p class="mt-2 text-xs text-slate-400">Ticket medio con descuento</p>
      </div>
    </section>

    <!-- Chart Section -->
    <section class="rounded-2xl border border-white/10 bg-slate-950/70 p-6">
      <h2 class="text-lg font-bold text-white mb-4">Impacto en Caja Semanal</h2>
      <div class="h-64 w-full">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </section>

    <!-- Promotions Table Section -->
    <section class="rounded-2xl border border-white/10 bg-slate-950/70 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-300">
          <thead class="border-b border-white/10 bg-white/5 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th class="px-6 py-4 font-semibold">ID</th>
              <th class="px-6 py-4 font-semibold">Nombre / Estado</th>
              <th class="px-6 py-4 font-semibold">Etiqueta (Badge)</th>
              <th class="px-6 py-4 font-semibold">Descuento</th>
              <th class="px-6 py-4 font-semibold">Vigencia</th>
              <th class="px-6 py-4 font-semibold">Plan Aplicable</th>
              <th class="px-6 py-4 font-semibold">Cupos / Personas</th>
              <th class="px-6 py-4 font-semibold text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr v-for="promo in promotions" :key="promo.id" class="transition hover:bg-white/5">
              <td class="px-6 py-4">
                <span class="rounded-full bg-rose-400/10 px-2.5 py-1 text-xs font-bold text-rose-400">
                  #{{ promo.id_promocion }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col gap-1">
                  <span class="font-bold text-white">{{ promo.name }}</span>
                  <div class="flex items-center gap-1.5">
                    <span 
                      :class="{
                        'bg-emerald-500/15 text-emerald-400 border-emerald-500/30': getPromoStatus(promo).tone === 'emerald',
                        'bg-slate-700/40 text-slate-400 border-slate-600/30': getPromoStatus(promo).tone === 'slate',
                        'bg-orange-500/15 text-orange-400 border-orange-500/30': getPromoStatus(promo).tone === 'amber',
                        'bg-rose-500/15 text-rose-400 border-rose-500/30': getPromoStatus(promo).tone === 'rose'
                      }"
                      class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black border uppercase tracking-wider"
                    >
                      <i :class="getPromoStatus(promo).icon"></i>
                      {{ getPromoStatus(promo).label }}
                    </span>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-slate-900 border border-slate-700 text-slate-200 tracking-wider shadow-sm">
                  <span>{{ promo.icono_etiqueta || '🏷️' }}</span>
                  <span class="text-rose-400 font-extrabold">{{ promo.discountType === 'fixed' ? `-S/${promo.discountValue}` : `-${promo.discountValue}%` }}</span>
                  <span v-if="promo.palabra_clave" class="uppercase text-slate-300 font-bold ml-0.5">{{ promo.palabra_clave }}</span>
                </span>
              </td>
              <td class="px-6 py-4 font-bold text-emerald-300">
                {{ promo.discountType === 'fixed' ? `S/. ${promo.discountValue}` : `${promo.discountValue}%` }}
              </td>
              <td class="px-6 py-4 text-xs">
                <span v-if="getPromoStatus(promo).label === 'Terminada'" class="inline-flex items-center gap-1 font-extrabold text-orange-400">
                  <i class="fa-solid fa-ban text-[11px]"></i> No aplica (Terminada)
                </span>
                <span v-else class="text-slate-400">
                  {{ promo.startsAt || 'Desde hoy' }} - {{ promo.validUntil || 'Sin fin' }}
                </span>
              </td>
              <td class="px-6 py-4 text-cyan-200 text-xs font-bold uppercase">
                {{ planNames(promo).join(', ') || 'Todos los planes' }}
              </td>
              <td class="px-6 py-4">
                <div v-if="promo.limite_cupos" class="flex flex-col gap-1">
                  <span class="text-xs font-bold text-white">
                    {{ promo.usos_actuales || 0 }} / {{ promo.limite_cupos }} personas
                  </span>
                  <div class="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      class="h-full rounded-full transition-all" 
                      :class="(promo.usos_actuales || 0) >= promo.limite_cupos ? 'bg-orange-400' : 'bg-rose-500'"
                      :style="{ width: Math.min(100, Math.round(((promo.usos_actuales || 0) / promo.limite_cupos) * 100)) + '%' }"
                    ></div>
                  </div>
                </div>
                <span v-else class="text-xs text-slate-400 font-semibold flex items-center gap-1">
                  <i class="fa-solid fa-infinity text-cyan-400"></i> Sin límite
                </span>
              </td>
              <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-3">
                  <button 
                    v-if="getPromoStatus(promo).label !== 'Terminada'" 
                    class="text-slate-400 hover:text-white transition cursor-pointer" 
                    @click="editModal(promo)" 
                    title="Editar"
                  >
                    <i class="fa-solid fa-pen"></i>
                  </button>
                  <span v-else class="text-slate-600 opacity-60 cursor-not-allowed" title="Promoción terminada (solo eliminar)">
                    <i class="fa-solid fa-lock text-xs"></i>
                  </span>
                  <button class="text-rose-400/70 hover:text-rose-400 transition cursor-pointer" @click="requestDelete(promo)" title="Eliminar">
                    <i class="fa-solid fa-trash-can"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="promotions.length === 0">
              <td colspan="8" class="px-6 py-8 text-center text-slate-500">
                No hay reglas comerciales configuradas.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Modal Form con Preview y Plan Único -->
    <PromotionEditorDialog :plans="plans" :form="form" :selected-plan="selectedPlan"
      :preview-calculated-price="previewCalculatedPrice" :preview-savings="previewSavings"
      :is-modal-open="isModalOpen" :saving="saving" :modal-error="modalError" :is-dark-theme="isDarkTheme"
      @close="closeModal" @save="save" @select-plan="selectSinglePlan" />
  </div>
</template>

<script setup>
import PromotionEditorDialog from '../components/promotions/PromotionEditorDialog.vue';
import { Bar } from 'vue-chartjs';
import { usePromotionsWorkspace } from '../composables/promotions/usePromotionsWorkspace.js';

const {
  gymStore, feedback, feedbackTone, plans, promotions,
  form, activePromotionsCount, activeClients, totalAhorrado, porcentajeVentasConPromo,
  ticketMedioConDescuento, selectSinglePlan, selectedPlan, previewCalculatedPrice, previewSavings,
  getPromoStatus, isModalOpen, saving, modalError, deleting,
  deleteError, openNewModal, closeModal, editModal, chartData,
  isDarkTheme, chartOptions, reset, planNames, edit,
  save, promoToDelete, requestDelete, confirmDelete,
} = usePromotionsWorkspace();
</script>

<style scoped src="../styles/promotions.css"></style>
