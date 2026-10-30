<template>
  <Teleport to="body">
    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
      <form class="w-full max-w-6xl rounded-3xl border border-white/10 bg-slate-950 p-0 shadow-2xl overflow-y-auto max-h-[92vh]" novalidate @submit.prevent="$emit('save')">
        <!-- Top gradient border -->
        <div class="h-1 w-full bg-gradient-to-r from-rose-500 via-purple-500 to-indigo-500 rounded-t-3xl"></div>
        
        <div class="p-8">
          <div class="flex justify-between items-center mb-8">
            <div class="flex items-center gap-4">
              <div class="h-12 w-12 rounded-2xl bg-rose-500/10 flex items-center justify-center text-rose-400">
                <i class="fa-solid fa-tag"></i>
              </div>
              <div>
                <p class="text-xs uppercase tracking-widest text-slate-400 font-bold">{{ form.id_promocion ? 'EDITAR' : 'CREAR' }}</p>
                <h2 class="mt-1 text-2xl font-black text-white">Regla comercial</h2>
              </div>
            </div>
            <button type="button" class="text-slate-400 hover:text-white text-xl transition cursor-pointer" @click="$emit('close')">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Left Column: Datos generales + Etiqueta + Limite -->
            <div class="space-y-6">
              <div>
                <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                  <i class="fa-solid fa-wand-magic-sparkles text-rose-400"></i> NOMBRE DE LA PROMOCIÓN
                </label>
                <input v-model="form.name" class="field-input focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" placeholder="Ej. Promo Verano" required />
              </div>
              
              <div>
                <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                  <i class="fa-regular fa-file-lines text-slate-400"></i> DESCRIPCIÓN INTERNA <span class="text-slate-500 lowercase normal-case">(opcional)</span>
                </label>
                <textarea v-model="form.description" rows="2" class="field-input focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" placeholder="Detalle o notas internas del descuento..."></textarea>
              </div>
              
              <div class="grid gap-4 sm:grid-cols-2">
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                    <i class="fa-solid fa-chart-pie text-slate-400"></i> TIPO
                  </label>
                  <select v-model="form.discountType" class="field-input focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition">
                    <option value="percent">Porcentaje (%)</option>
                    <option value="fixed">Monto fijo (S/.)</option>
                  </select>
                </div>
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-rose-400 uppercase tracking-widest mb-2">
                    <i class="fa-regular fa-square-check"></i> VALOR
                  </label>
                  <div class="relative">
                    <input v-model.number="form.discountValue" type="number" min="0" step="0.01" class="field-input pr-10 focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" placeholder="0.00" required />
                    <span class="absolute right-4 top-3.5 text-slate-400 font-bold text-sm">{{ form.discountType === 'percent' ? '%' : 'S/.' }}</span>
                  </div>
                </div>
              </div>

              <!-- Límite de Cupos por Persona -->
              <div>
                <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                  <i class="fa-solid fa-users text-indigo-400"></i> LÍMITE DE PERSONAS / CUPOS <span class="text-slate-500 lowercase normal-case">(opcional)</span>
                </label>
                <div class="relative">
                  <input v-model.number="form.limite_cupos" type="number" min="1" class="field-input pr-24 focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" placeholder="Ej. 10 (Dejar vacío = ilimitado)" />
                  <span class="absolute right-4 top-3.5 text-slate-400 font-bold text-xs uppercase">Personas</span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1">Al alcanzar este número de ventas, la promoción pasará automáticamente a estado AGOTADA / CUMPLIDA.</p>
              </div>
              
              <div class="grid gap-4 sm:grid-cols-2">
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                    <i class="fa-regular fa-calendar text-slate-400"></i> INICIO <span class="text-slate-500 lowercase normal-case">(opcional)</span>
                  </label>
                  <input v-model="form.startsAt" type="date" class="field-input focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" />
                </div>
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
                    <i class="fa-regular fa-calendar text-slate-400"></i> FIN <span class="text-slate-500 lowercase normal-case">(opcional)</span>
                  </label>
                  <input v-model="form.validUntil" type="date" class="field-input focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" />
                </div>
              </div>

              <!-- Personalización de Etiqueta (Badge) -->
              <div class="rounded-3xl border border-rose-500/20 bg-slate-900/60 p-5 space-y-4">
                <div class="flex items-center justify-between">
                  <label class="flex items-center gap-2 text-xs font-black text-rose-400 uppercase tracking-widest">
                    <i class="fa-solid fa-tag"></i> PERSONALIZACIÓN DE ETIQUETA (BADGE)
                  </label>
                  <span class="text-[10px] text-slate-400 font-medium">Visible en planes</span>
                </div>

                <!-- Palabra Clave -->
                <div>
                  <label class="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">Palabra Clave / Tag</label>
                  <input 
                    v-model="form.palabra_clave" 
                    @input="form.palabra_clave = form.palabra_clave.toUpperCase()"
                    class="field-input text-xs uppercase font-bold tracking-wider focus:border-rose-400 focus:ring-1 focus:ring-rose-400 transition" 
                    placeholder="Ej. NAVIDAD, VERANO, FLASH" 
                    maxlength="20"
                  />
                </div>

                <!-- Vista Previa de la Etiqueta -->
                <div class="pt-2 border-t border-white/5 flex items-center justify-between">
                  <span class="text-[11px] text-slate-400 font-semibold">Badge generado:</span>
                  <span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-black bg-slate-950 border border-slate-700 text-slate-200 tracking-wider shadow-inner">
                    <span>🏷️</span>
                    <span class="text-rose-400 font-extrabold">{{ form.discountType === 'fixed' ? `-S/${form.discountValue || 0}` : `-${form.discountValue || 0}%` }}</span>
                    <span v-if="form.palabra_clave" class="uppercase text-slate-200 font-bold ml-0.5">{{ form.palabra_clave }}</span>
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Right Column: Selección de 1 solo plan + LIVE PREVIEW EN MODO OSCURO -->
            <div class="space-y-6">
              <!-- Selector de Plan Único -->
              <div class="rounded-3xl border border-white/10 bg-slate-900/45 p-5 space-y-3">
                <div class="flex items-center justify-between">
                  <label class="flex items-center gap-2 text-xs font-bold text-rose-400 uppercase tracking-widest">
                    <i class="fa-regular fa-credit-card"></i> SELECCIONA EL PLAN APLICABLE
                  </label>
                  <span class="text-[10px] text-orange-400 font-bold bg-orange-400/10 px-2.5 py-0.5 rounded-full border border-orange-400/20">
                    1 solo plan
                  </span>
                </div>
                <p class="text-[11px] text-slate-400">Elige exactamente un plan de la lista para asociarle esta oferta promocional:</p>
                
                <div class="grid grid-cols-1 gap-2.5">
                  <div 
                    v-for="plan in plans" 
                    :key="plan.id"
                    @click="$emit('select-plan', plan.id)"
                    :class="form.appliesTo.includes(plan.id) ? 'border-rose-500 bg-rose-500/10 ring-1 ring-rose-500/50' : 'border-white/5 hover:border-slate-700 bg-slate-950/60'"
                    class="relative flex cursor-pointer items-center justify-between rounded-2xl border p-3.5 transition-all"
                  >
                    <div class="flex items-center gap-3">
                      <div :class="form.appliesTo.includes(plan.id) ? 'bg-rose-500 border-rose-400 text-white' : 'bg-slate-900 border-slate-700 text-transparent'" class="h-5 w-5 rounded-full border flex items-center justify-center text-xs transition">
                        <i class="fa-solid fa-check text-[10px]"></i>
                      </div>
                      <div>
                        <p class="text-sm font-black text-white uppercase leading-none">{{ plan.name }}</p>
                        <p class="text-[11px] text-slate-400 mt-1">{{ plan.duration || '30 días' }}</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-sm font-black text-white">S/. {{ Number(plan.price || 0).toFixed(2) }}</p>
                      <p class="text-[10px] text-slate-400">Precio regular</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- LIVE PREVIEW CARD (CLIENTE FINAL) -->
              <div class="rounded-3xl border border-rose-500/30 bg-slate-950 p-6 shadow-2xl space-y-4 relative overflow-hidden card-preview">
                <div class="absolute -top-12 -right-12 h-32 w-32 bg-rose-500/10 rounded-full blur-2xl pointer-events-none"></div>

                <div class="flex items-center justify-between pb-3 border-b border-white/10">
                  <div class="flex items-center gap-2">
                    <i class="fa-solid fa-eye text-rose-400 text-xs"></i>
                    <span class="text-xs font-black uppercase tracking-widest text-slate-300">
                      VISTA PREVIA DE TARJETA ({{ isDarkTheme ? 'MODO OSCURO' : 'MODO CLARO' }})
                    </span>
                  </div>
                  <span class="text-[10px] uppercase tracking-wider text-emerald-400 font-bold bg-emerald-400/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    Vista Cliente
                  </span>
                </div>

                <!-- Live Card Content -->
                <div class="rounded-2xl border border-white/10 bg-slate-900/90 p-5 space-y-4">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">PLAN SELECCIONADO</span>
                      <h3 class="text-xl font-black text-white uppercase tracking-tight">
                        {{ selectedPlan ? selectedPlan.name : 'SELECCIONA UN PLAN' }}
                      </h3>
                    </div>
                    <!-- Badge Promocional -->
                    <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black bg-slate-950 border border-slate-700 text-slate-200 tracking-wider shadow-md">
                      <span>{{ form.icono_etiqueta || '🏷️' }}</span>
                      <span class="text-rose-400 font-extrabold">{{ form.discountType === 'fixed' ? `-S/${form.discountValue || 0}` : `-${form.discountValue || 0}%` }}</span>
                      <span v-if="form.palabra_clave" class="uppercase text-slate-200 font-bold ml-0.5">{{ form.palabra_clave }}</span>
                    </span>
                  </div>

                  <!-- Pricing Display -->
                  <div class="pt-2 flex items-baseline justify-between border-t border-white/5">
                    <div>
                      <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Precio Final Promocional</p>
                      <div class="flex items-baseline gap-2 mt-0.5">
                        <span class="text-2xl font-black text-emerald-400">S/. {{ previewCalculatedPrice.toFixed(2) }}</span>
                        <span v-if="previewSavings > 0" class="text-xs text-slate-500 line-through">S/. {{ Number(selectedPlan?.price || 0).toFixed(2) }}</span>
                      </div>
                    </div>
                    <div v-if="previewSavings > 0" class="text-right">
                      <span class="inline-block rounded-xl bg-emerald-500/15 border border-emerald-500/30 px-3 py-1 text-xs font-extrabold text-emerald-300">
                        Ahorras S/. {{ previewSavings.toFixed(2) }}
                      </span>
                    </div>
                  </div>

                  <!-- Cupos Availability Badge -->
                  <div class="pt-3 border-t border-white/5 flex items-center justify-between text-xs font-semibold">
                    <div class="flex items-center gap-2">
                      <i class="fa-solid fa-clock text-slate-400"></i>
                      <span class="text-slate-300">{{ selectedPlan?.duration || '30 días' }}</span>
                    </div>
                    <div>
                      <span v-if="form.limite_cupos && form.limite_cupos > 0" :class="form.usos_actuales >= form.limite_cupos ? 'text-orange-400 bg-orange-500/10 border-orange-500/30' : 'text-orange-400 bg-orange-400/10 border-orange-400/30'" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-bold">
                        <i :class="form.usos_actuales >= form.limite_cupos ? 'fa-solid fa-flag-checkered' : 'fa-solid fa-fire'"></i>
                        {{ form.usos_actuales >= form.limite_cupos ? 'Terminada' : `Quedan ${Math.max(0, form.limite_cupos - (form.usos_actuales || 0))} de ${form.limite_cupos} cupos` }}
                      </span>
                      <span v-else class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[11px] font-bold">
                        <i class="fa-solid fa-bolt"></i> Cupos ilimitados
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Activo Toggle -->
              <label class="flex items-center justify-between rounded-3xl border border-white/10 bg-slate-900/45 p-5 cursor-pointer hover:bg-white/10 transition-colors">
                <div class="flex items-center gap-4">
                  <div class="h-2 w-2 rounded-full" :class="form.active ? 'bg-emerald-400' : 'bg-slate-500'"></div>
                  <div>
                    <p class="text-sm font-bold text-white">Promoción activa</p>
                    <p class="text-xs text-slate-400 mt-0.5">Estará disponible de inmediato tras guardar</p>
                  </div>
                </div>
                <div class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors" :class="form.active ? 'bg-rose-500' : 'bg-slate-600'">
                  <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="form.active ? 'translate-x-6' : 'translate-x-1'"></span>
                  <input v-model="form.active" type="checkbox" class="sr-only" />
                </div>
              </label>
            </div>
          </div>
          
          <p v-if="modalError" role="alert" class="app-notice app-notice--error rounded-xl border px-4 py-3 text-sm">{{ modalError }}</p>
          <!-- Actions -->
          <div class="mt-10 flex justify-end items-center gap-6">
            <button type="button" class="text-sm font-bold text-slate-300 hover:text-white transition cursor-pointer" @click="$emit('close')">Cancelar</button>
            <button type="submit" :disabled="saving" class="flex items-center gap-2 rounded-xl bg-rose-500 px-6 py-3 text-sm font-black text-white hover:bg-rose-400 transition shadow-lg shadow-rose-500/20 cursor-pointer">
              <i class="fa-solid fa-check"></i> {{ saving ? 'Guardando…' : 'Guardar y Activar Regla' }}
            </button>
          </div>
        </div>
      </form>
    </div>
  </Teleport>
</template>
<script setup>
defineProps({
  plans: Array, form: { type: Object, required: true }, selectedPlan: Object,
  previewCalculatedPrice: Number, previewSavings: Number, isModalOpen: Boolean,
  saving: Boolean, modalError: String, isDarkTheme: Boolean,
});
defineEmits(['close', 'save', 'select-plan']);
</script>
<style scoped src="../../styles/promotions.css"></style>
