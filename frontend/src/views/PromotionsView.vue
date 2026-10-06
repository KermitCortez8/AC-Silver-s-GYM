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
        <div class="w-full max-w-md rounded-3xl border bg-slate-900 p-6 shadow-2xl space-y-5" :class="feedbackTone === 'error' ? 'border-rose-500/40' : 'border-emerald-500/40'">
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-2xl flex items-center justify-center text-lg shrink-0 shadow-inner" :class="feedbackTone === 'error' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'">
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

          <div class="p-4 rounded-2xl bg-slate-950/70 border border-white/5">
            <p class="text-sm font-medium text-slate-200 leading-relaxed">
              {{ feedback }}
            </p>
          </div>

          <div class="flex justify-end pt-1">
            <button type="button" @click="feedback = ''" :class="feedbackTone === 'error' ? 'bg-rose-500 hover:bg-rose-400 shadow-rose-500/25' : 'bg-emerald-500 hover:bg-emerald-400 shadow-emerald-500/25'" class="w-full sm:w-auto px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-wider text-white transition-all shadow-lg cursor-pointer">
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
            <button type="button" class="h-8 w-8 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-base transition cursor-pointer" @click="promoToDelete = null" title="Cerrar">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="p-4 rounded-2xl bg-slate-950/70 border border-white/5 space-y-1">
            <p class="text-sm font-medium text-slate-300">
              ¿Estás seguro de que deseas eliminar la promoción <span class="font-black text-white">"{{ promoToDelete.name }}"</span>?
            </p>
            <p class="text-xs text-rose-400/80 font-semibold">Esta acción no se puede deshacer.</p>
          </div>

          <div class="flex items-center justify-end gap-3 pt-1">
            <button type="button" class="px-5 py-2.5 rounded-xl border border-white/10 bg-slate-800 text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-700 transition cursor-pointer" @click="promoToDelete = null">
              Cancelar
            </button>
            <button type="button" class="px-6 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-400 text-xs font-black uppercase tracking-wider text-white transition shadow-lg shadow-rose-500/25 flex items-center gap-2 cursor-pointer" @click="confirmDelete">
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
          <i class="fa-solid fa-dollar-sign text-amber-500 bg-amber-400/10 p-2 rounded-full text-xs px-3"></i>
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
                        'bg-amber-500/15 text-amber-400 border-amber-500/30': getPromoStatus(promo).tone === 'amber',
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
                <span v-if="getPromoStatus(promo).label === 'Terminada'" class="inline-flex items-center gap-1 font-extrabold text-amber-400">
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
                      :class="(promo.usos_actuales || 0) >= promo.limite_cupos ? 'bg-amber-400' : 'bg-rose-500'" 
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
    <Teleport to="body">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
        <form class="w-full max-w-6xl rounded-3xl border border-white/10 bg-slate-950 p-0 shadow-2xl overflow-y-auto max-h-[92vh]" @submit.prevent="save">
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
              <button type="button" class="text-slate-400 hover:text-white text-xl transition cursor-pointer" @click="closeModal">
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
                    <span class="text-[10px] text-amber-400 font-bold bg-amber-400/10 px-2.5 py-0.5 rounded-full border border-amber-400/20">
                      1 solo plan
                    </span>
                  </div>
                  <p class="text-[11px] text-slate-400">Elige exactamente un plan de la lista para asociarle esta oferta promocional:</p>
                  
                  <div class="grid grid-cols-1 gap-2.5">
                    <div 
                      v-for="plan in plans" 
                      :key="plan.id"
                      @click="selectSinglePlan(plan.id)"
                      :class="form.appliesTo.includes(plan.id) ? 'border-rose-500 bg-rose-500/10 ring-1 ring-rose-500/50' : 'border-white/5 hover:border-slate-700 bg-slate-950/60'"
                      class="relative flex cursor-pointer items-center justify-between rounded-2xl border p-3.5 transition-all"
                    >
                      <div class="flex items-center gap-3">
                        <div :class="form.appliesTo.includes(plan.id) ? 'bg-rose-500 border-rose-400 text-white' : 'bg-slate-900 border-slate-700 text-transparent'" class="h-5 w-5 rounded-full border flex items-center justify-center text-xs transition">
                          <i class="fa-solid fa-check text-[10px]"></i>
                        </div>
                        <div>
                          <p class="text-sm font-black text-white uppercase leading-none">{{ plan.name }}</p>
                          <p class="text-[11px] text-slate-400 mt-1">{{ plan.duration || '30 dias' }}</p>
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
                        <span class="text-slate-300">{{ selectedPlan?.duration || '30 dias' }}</span>
                      </div>
                      <div>
                        <span v-if="form.limite_cupos && form.limite_cupos > 0" :class="form.usos_actuales >= form.limite_cupos ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' : 'text-amber-400 bg-amber-400/10 border-amber-400/30'" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-bold">
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
            
            <!-- Actions -->
            <div class="mt-10 flex justify-end items-center gap-6">
              <button type="button" class="text-sm font-bold text-slate-300 hover:text-white transition cursor-pointer" @click="closeModal">Cancelar</button>
              <button type="submit" class="flex items-center gap-2 rounded-xl bg-rose-500 px-6 py-3 text-sm font-black text-white hover:bg-rose-400 transition shadow-lg shadow-rose-500/20 cursor-pointer">
                <i class="fa-solid fa-check"></i> Guardar y Activar Regla
              </button>
            </div>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';
import { useTheme } from '../composables/useTheme';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const plans = computed(() => gymStore.planCatalog);
const promotions = computed(() => {
  return gymStore.promotions.map((promo) => {
    const usesInStore = gymStore.members.filter((m) => {
      if (!m || m.status === 'INACTIVO') return false;
      const mPromoId = Number(
        m.id_promocion || (m.promocion && String(m.promocion).startsWith('promo-') ? String(m.promocion).replace('promo-', '') : 0)
      );
      return mPromoId === Number(promo.id_promocion);
    }).length;

    const usosActuales = Number(promo.usos_actuales ?? usesInStore);
    return {
      ...promo,
      usos_actuales: usosActuales,
    };
  });
});

const form = reactive({
  id_promocion: null,
  name: '',
  description: '',
  discountType: 'percent',
  discountValue: 10,
  startsAt: '',
  validUntil: '',
  icono_etiqueta: '🏷️',
  palabra_clave: '',
  appliesTo: [],
  limite_cupos: null,
  usos_actuales: 0,
  active: true,
});

const activePromotionsCount = computed(() => promotions.value.filter(p => p.active).length);

const activeClients = computed(() => gymStore.members.filter(m => m.status === 'ACTIVO' && m.membershipPrice > 0));

const totalAhorrado = computed(() => {
  return activeClients.value.reduce((acc, client) => {
    const plan = plans.value.find(p => p.name === client.plan);
    if (plan && client.membershipPrice < plan.price) {
      return acc + (plan.price - client.membershipPrice);
    }
    return acc;
  }, 0);
});

const porcentajeVentasConPromo = computed(() => {
  if (activeClients.value.length === 0) return 0;
  const withPromo = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    return plan && client.membershipPrice < plan.price;
  });
  return (withPromo.length / activeClients.value.length) * 100;
});

const ticketMedioConDescuento = computed(() => {
  const withPromo = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    return plan && client.membershipPrice < plan.price;
  });
  if (withPromo.length === 0) return 0;
  const totalPagado = withPromo.reduce((acc, client) => acc + client.membershipPrice, 0);
  return totalPagado / withPromo.length;
});

// Selección de Plan Único
const selectSinglePlan = (planId) => {
  form.appliesTo = [planId];
};

const selectedPlan = computed(() => {
  if (!form.appliesTo.length) return plans.value[0] || null;
  return plans.value.find(p => p.id === form.appliesTo[0]) || plans.value[0] || null;
});

const previewCalculatedPrice = computed(() => {
  if (!selectedPlan.value) return 0;
  const basePrice = Number(selectedPlan.value.price || 0);
  const val = Number(form.discountValue || 0);
  if (form.discountType === 'fixed') {
    return Math.max(0, basePrice - val);
  } else {
    return Math.max(0, basePrice - (basePrice * val / 100));
  }
});

const previewSavings = computed(() => {
  if (!selectedPlan.value) return 0;
  const basePrice = Number(selectedPlan.value.price || 0);
  return Math.max(0, basePrice - previewCalculatedPrice.value);
});

const getPromoStatus = (promo) => {
  if (!promo.active) return { label: 'Pausada', tone: 'slate', icon: 'fa-solid fa-pause' };
  const today = new Date().toISOString().split('T')[0];
  const isCupoCumplido = promo.limite_cupos && promo.usos_actuales >= promo.limite_cupos;
  const isExpirada = promo.validUntil && promo.validUntil < today;
  if (isCupoCumplido || isExpirada) {
    return { label: 'Terminada', tone: 'amber', icon: 'fa-solid fa-flag-checkered' };
  }
  return { label: 'Activa', tone: 'emerald', icon: 'fa-solid fa-circle-check' };
};

const isModalOpen = ref(false);
const openNewModal = () => {
  reset();
  isModalOpen.value = true;
};
const closeModal = () => {
  isModalOpen.value = false;
};
const editModal = (promo) => {
  if (getPromoStatus(promo).label === 'Terminada') {
    feedbackTone.value = 'error';
    feedback.value = 'Las promociones terminadas no se pueden editar, únicamente eliminar.';
    return;
  }
  edit(promo);
  isModalOpen.value = true;
};

const chartData = computed(() => {
  const currentMonth = new Date().getMonth();
  const currentYear = new Date().getFullYear();

  const withPromoThisMonth = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    const hasPromo = plan && client.membershipPrice < plan.price;
    if (!hasPromo) return false;
    
    const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
    return startDate.getMonth() === currentMonth && startDate.getFullYear() === currentYear;
  });
  
  const baseValuesNeto = [0, 0, 0, 0];
  const baseValuesDesc = [0, 0, 0, 0];

  withPromoThisMonth.forEach((client) => {
    const plan = plans.value.find(p => p.name === client.plan);
    const neto = client.membershipPrice;
    const desc = plan.price - client.membershipPrice;
    
    const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
    const day = startDate.getDate();
    
    let weekIndex = 0;
    if (day <= 7) weekIndex = 0;
    else if (day <= 14) weekIndex = 1;
    else if (day <= 21) weekIndex = 2;
    else weekIndex = 3;

    baseValuesNeto[weekIndex] += neto;
    baseValuesDesc[weekIndex] += desc;
  });
  
  return {
    labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
    datasets: [
      {
        label: 'Descuento Otorgado (S/.)',
        backgroundColor: '#a855f7',
        data: baseValuesDesc,
        borderRadius: 4,
      },
      {
        label: 'Ingreso Neto Caja (S/.)',
        backgroundColor: '#f43f5e',
        data: baseValuesNeto,
        borderRadius: 4,
      }
    ]
  };
});

const { isDarkTheme } = useTheme();

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: isDarkTheme.value ? '#cbd5e1' : '#525252' } }
  },
  scales: {
    x: { ticks: { color: isDarkTheme.value ? '#94a3b8' : '#737373' }, grid: { color: isDarkTheme.value ? 'rgba(255,255,255,0.1)' : 'rgba(23,23,23,0.1)' } },
    y: { ticks: { color: isDarkTheme.value ? '#94a3b8' : '#737373' }, grid: { color: isDarkTheme.value ? 'rgba(255,255,255,0.1)' : 'rgba(23,23,23,0.1)' } }
  }
}));

const reset = () => {
  const defaultPlanId = plans.value[0]?.id || null;
  Object.assign(form, {
    id_promocion: null,
    name: '',
    description: '',
    discountType: 'percent',
    discountValue: 10,
    startsAt: '',
    validUntil: '',
    icono_etiqueta: '🏷️',
    palabra_clave: '',
    appliesTo: defaultPlanId ? [defaultPlanId] : [],
    limite_cupos: null,
    usos_actuales: 0,
    active: true,
  });
};

const planNames = (promo) => promo.appliesTo.map((id) => plans.value.find((plan) => plan.id === id)?.name).filter(Boolean);

const edit = (promo) => {
  const plansList = Array.isArray(promo.appliesTo) ? promo.appliesTo : [];
  Object.assign(form, {
    id_promocion: promo.id_promocion,
    name: promo.name,
    description: promo.description,
    discountType: promo.discountType,
    discountValue: promo.discountValue,
    startsAt: promo.startsAt,
    validUntil: promo.validUntil,
    icono_etiqueta: promo.icono_etiqueta || '🏷️',
    palabra_clave: promo.palabra_clave || '',
    appliesTo: plansList.slice(0, 1),
    limite_cupos: promo.limite_cupos !== undefined && promo.limite_cupos !== null ? promo.limite_cupos : null,
    usos_actuales: promo.usos_actuales || 0,
    active: promo.active,
  });
};

const save = async () => {
  if (!form.appliesTo || !form.appliesTo.length) {
    feedbackTone.value = 'error';
    feedback.value = 'Debes seleccionar exactamente un plan para la promoción.';
    return;
  }
  try {
    await gymStore.upsertPromotion({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Promoción guardada exitosamente.';
    closeModal();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la promoción.';
  }
};

const promoToDelete = ref(null);

const requestDelete = (promo) => {
  promoToDelete.value = promo;
};

const confirmDelete = async () => {
  if (!promoToDelete.value) return;
  const target = promoToDelete.value;
  promoToDelete.value = null;
  try {
    await gymStore.deletePromotion(target.id_promocion);
    feedbackTone.value = 'success';
    feedback.value = 'Promoción eliminada exitosamente.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar la promoción.';
  }
};

onMounted(() => gymStore.fetchFromBackend?.({ section: 'promotions' }).catch(() => {}));
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid var(--app-border, rgba(255,255,255,.1));
  border-radius: 1rem;
  background: var(--app-input, rgba(2,6,23,.72));
  padding: .75rem 1rem;
  color: var(--app-text, white);
  outline: none;
}
.field-input::placeholder {
  color: var(--app-text-faint, #64748b);
}
</style>
