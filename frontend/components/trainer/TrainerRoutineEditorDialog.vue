<template>
  <Teleport to="body">
    <div v-if="showRoutineModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md overflow-y-auto">
      <div class="relative w-full max-w-3xl rounded-3xl border border-white/15 bg-slate-950 p-6 shadow-2xl space-y-5 my-8 max-h-[90vh] overflow-y-auto">
        <!-- Encabezado Modal -->
        <div class="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <p class="text-xs uppercase tracking-widest text-red-500 font-extrabold">Configuración de Catálogo</p>
            <h2 class="text-2xl font-black text-white">
              {{ routineForm.id_rutina ? 'Editar Rutina Registrada' : 'Crear Nueva Rutina' }}
            </h2>
          </div>
          <button class="rounded-full bg-white/10 p-2 text-slate-400 hover:bg-white/20 hover:text-white transition" @click="$emit('close')">
            <i class="fa-solid fa-xmark text-base"></i>
          </button>
        </div>

        <!-- Aviso de edición -->
        <div v-if="routineForm.id_rutina" class="rounded-2xl border border-orange-400/30 bg-orange-400/10 px-4 py-3 text-xs text-orange-50">
          <p class="font-bold">Editando: {{ editingName || 'Rutina' }}</p>
          <p v-if="editingAssignedCount > 0" class="mt-1 text-orange-100/80">
            Esta rutina está asignada a {{ editingAssignedCount }} {{ editingAssignedCount === 1 ? 'cliente' : 'clientes' }}. Los cambios los afectarán.
          </p>
        </div>

        <form class="space-y-5" novalidate @submit.prevent="$emit('save')">
          <div class="grid gap-4 sm:grid-cols-2">
            <label class="space-y-1.5">
              <span class="text-xs font-bold text-slate-300">Servicio Asociado</span>
              <select v-model="routineForm.servicio" class="field-input text-sm" :class="{ 'field-error': fieldError('servicio') }">
                <option v-for="service in serviceOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
              </select>
              <span v-if="fieldError('servicio')" class="block text-xs text-rose-300">{{ fieldError('servicio') }}</span>
            </label>
            <label class="space-y-1.5">
              <span class="flex items-center justify-between text-xs font-bold text-slate-300">
                <span>Nombre de la Rutina</span>
                <span class="font-normal" :class="routineForm.nombre_rutina.length > maxNombre ? 'text-rose-300' : 'text-slate-500'">{{ routineForm.nombre_rutina.length }}/{{ maxNombre }}</span>
              </span>
              <input v-model="routineForm.nombre_rutina" class="field-input text-sm" :class="{ 'field-error': fieldError('nombre_rutina') }" placeholder="Ej. Hipertrofia Tren Superior" @blur="touched.nombre_rutina = true" />
              <span v-if="fieldError('nombre_rutina')" class="block text-xs text-rose-300">{{ fieldError('nombre_rutina') }}</span>
            </label>
          </div>

          <label class="block space-y-1.5">
            <span class="flex items-center justify-between text-xs font-bold text-slate-300">
              <span>Zonas Musculares Trabajadas</span>
              <span class="font-normal" :class="routineForm.zonas_musculares.length > maxZonas ? 'text-rose-300' : 'text-slate-500'">{{ routineForm.zonas_musculares.length }}/{{ maxZonas }}</span>
            </span>
            <input v-model="routineForm.zonas_musculares" class="field-input text-sm" :class="{ 'field-error': fieldError('zonas_musculares') }" placeholder="Ej. Pecho, Espalda, Hombros, Tríceps" @blur="touched.zonas_musculares = true" />
            <span v-if="fieldError('zonas_musculares')" class="block text-xs text-rose-300">{{ fieldError('zonas_musculares') }}</span>
          </label>

          <!-- Atajos para zonas comunes -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="zone in quickZones"
              :key="zone"
              type="button"
              class="rounded-full border px-3 py-1 text-[11px] font-bold transition"
              :class="zoneActive(zone) ? 'border-red-600 bg-red-600 text-white' : 'border-white/10 text-slate-300 hover:bg-red-600/20'"
              @click="$emit('toggle-zone', zone)"
            >
              {{ zone }}
            </button>
          </div>

          <!-- CONSTRUCTOR DE EJERCICIOS CON SELECTOR CLARO DE MODO DE REPETICIÓN -->
          <div class="rounded-2xl border border-white/10 bg-black p-4 space-y-4">
            <div class="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 class="font-bold text-white text-sm flex items-center gap-2">
                  <i class="fa-solid fa-dumbbell text-red-500"></i>
                  Lista de Ejercicios
                </h3>
                <p class="text-xs text-slate-400">Agrega los ejercicios detallando series, tipo de repeticiones, descanso y peso sugerido.</p>
              </div>
              <button type="button" class="flex items-center gap-1.5 rounded-xl bg-red-600/20 border border-red-600/30 px-3.5 py-1.5 text-xs font-bold text-red-400 hover:bg-red-600 hover:text-white transition" @click="$emit('add-exercise')">
                <i class="fa-solid fa-plus text-xs"></i>
                <span>Agregar Ejercicio</span>
              </button>
            </div>

            <p v-if="submitted && errors.ejercicios" class="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-xs text-rose-100">{{ errors.ejercicios }}</p>

            <div v-if="routineForm.ejercicios.length" class="space-y-4">
              <div v-for="(ex, index) in routineForm.ejercicios" :key="index" class="rounded-2xl border border-white/10 bg-slate-900/90 p-4 space-y-3 shadow-inner">
                <div class="flex items-center justify-between border-b border-white/5 pb-2">
                  <span class="text-xs font-black text-red-400">Ejercicio #{{ index + 1 }}</span>
                  <button type="button" class="text-xs font-bold text-red-400 hover:text-red-300 hover:underline flex items-center gap-1" @click="$emit('remove-exercise', index)">
                    <i class="fa-solid fa-trash text-xs"></i>
                    <span>Eliminar</span>
                  </button>
                </div>

                <!-- Campos principales: Nombre y Músculo Objetivo -->
                <div class="grid gap-3 sm:grid-cols-2">
                  <label class="space-y-1">
                    <span class="text-[11px] font-bold text-slate-300">Nombre del Ejercicio</span>
                    <input v-model="ex.nombre_ejercicio" class="field-input text-xs" :class="{ 'field-error': exError(index, 'nombre') }" placeholder="Ej. Press de Banca Plano" />
                    <span v-if="exError(index, 'nombre')" class="block text-[11px] text-rose-300">{{ exError(index, 'nombre') }}</span>
                  </label>
                  <label class="space-y-1">
                    <span class="text-[11px] font-bold text-slate-300">Músculo Objetivo (opcional)</span>
                    <input v-model="ex.grupo_muscular" class="field-input text-xs" placeholder="Ej. Pectoral mayor / Tríceps" />
                  </label>
                </div>

                <!-- Configuración de Series, Tipo de Repeticiones y Descanso -->
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-4 items-start pt-1">
                  <!-- Series -->
                  <label class="space-y-1">
                    <span class="text-[11px] font-bold text-slate-300">Series</span>
                    <input v-model.number="ex.series" type="number" min="1" max="20" class="field-input text-xs" :class="{ 'field-error': exError(index, 'series') }" />
                    <span v-if="exError(index, 'series')" class="block text-[11px] text-rose-300">{{ exError(index, 'series') }}</span>
                  </label>

                  <!-- Selector de Modo de Repetición (Fijo / Rango / Al fallo) -->
                  <div class="space-y-1 sm:col-span-2">
                    <span class="text-[11px] font-bold text-slate-300">Repeticiones</span>

                    <!-- Pestañas de modo -->
                    <div class="flex items-center gap-1 rounded-xl bg-slate-950/80 p-1 border border-white/10">
                      <button
                        type="button"
                        class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                        :class="ex.rep_modo === 'fijo' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                        @click="$emit('rep-mode', ex, 'fijo')"
                      >
                        Número Fijo
                      </button>
                      <button
                        type="button"
                        class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                        :class="ex.rep_modo === 'rango' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                        @click="$emit('rep-mode', ex, 'rango')"
                      >
                        Rango (ej. 10-12)
                      </button>
                      <button
                        type="button"
                        class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                        :class="ex.rep_modo === 'fallo' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                        @click="$emit('rep-mode', ex, 'fallo')"
                      >
                        Al Fallo
                      </button>
                    </div>

                    <!-- Input dinámico según modo -->
                    <div v-if="ex.rep_modo === 'fijo'" class="pt-1">
                      <input
                        v-model="ex.rep_fijo"
                        type="number"
                        min="1"
                        placeholder="Ej. 10 o 12"
                        class="field-input text-xs"
                        @input="$emit('sync-reps', ex)"
                      />
                    </div>

                    <div v-else-if="ex.rep_modo === 'rango'" class="flex items-center gap-2 pt-1">
                      <input
                        v-model="ex.rep_min"
                        type="number"
                        min="1"
                        placeholder="Mín (ej. 10)"
                        class="field-input text-xs"
                        @input="$emit('sync-reps', ex)"
                      />
                      <span class="text-xs text-slate-400 font-bold">a</span>
                      <input
                        v-model="ex.rep_max"
                        type="number"
                        min="1"
                        placeholder="Máx (ej. 12)"
                        class="field-input text-xs"
                        @input="$emit('sync-reps', ex)"
                      />
                    </div>

                    <div v-else-if="ex.rep_modo === 'fallo'" class="pt-1">
                      <div class="rounded-xl border border-red-500/40 bg-red-950/40 px-3 py-2 text-center text-xs font-bold text-red-300 flex items-center justify-center gap-2">
                        <i class="fa-solid fa-fire text-red-500"></i>
                        <span>Repeticiones hasta el fallo (AMRAP)</span>
                      </div>
                    </div>
                    <span v-if="exError(index, 'reps')" class="block text-[11px] text-rose-300">{{ exError(index, 'reps') }}</span>
                  </div>

                  <!-- Descanso -->
                  <label class="space-y-1">
                    <span class="text-[11px] font-bold text-slate-300">Descanso</span>
                    <select v-model.number="ex.descanso_segundos" class="field-input text-xs">
                      <option :value="30">30 seg</option>
                      <option :value="45">45 seg</option>
                      <option :value="60">60 seg (1 min)</option>
                      <option :value="90">90 seg (1.5 min)</option>
                      <option :value="120">120 seg (2 min)</option>
                      <option :value="180">180 seg (3 min)</option>
                    </select>
                  </label>
                </div>

                <!-- Peso sugerido (kg) -->
                <div class="pt-2 border-t border-white/5 flex flex-col gap-1">
                  <label class="flex items-center gap-3 w-full sm:w-1/2">
                    <span class="text-[11px] font-bold text-slate-300 whitespace-nowrap">Peso sug. (kg):</span>
                    <input v-model.number="ex.peso_sugerido_kg" type="number" step="0.5" min="0" class="field-input text-xs" :class="{ 'field-error': exError(index, 'peso') }" placeholder="Opcional (ej. 60)" />
                  </label>
                  <span v-if="exError(index, 'peso')" class="block text-[11px] text-rose-300">{{ exError(index, 'peso') }}</span>
                </div>
              </div>
            </div>

            <p v-else class="text-center text-xs text-slate-400 py-4 border border-dashed border-white/10 rounded-xl">
              No has agregado ejercicios a esta rutina aún. Haz clic en "+ Agregar Ejercicio".
            </p>
          </div>

          <!-- Botones de Acción Modal -->
          <div class="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <p v-if="routineForm.id_rutina && !hasChanges" class="mr-auto text-xs text-slate-500">No hay cambios por guardar.</p>
            <button type="button" class="rounded-2xl border border-white/10 bg-slate-900 px-5 py-2.5 text-xs font-bold text-white transition hover:bg-slate-800" :disabled="isSaving" @click="$emit('close')">
              Cancelar
            </button>
            <button class="flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-2.5 text-xs font-extrabold text-white transition hover:bg-red-500 shadow-lg shadow-red-600/20 disabled:cursor-not-allowed disabled:opacity-60" :disabled="isSaving || (routineForm.id_rutina !== null && !hasChanges)">
              <i class="fa-solid fa-floppy-disk"></i>
              <span>{{ isSaving ? 'Guardando...' : (routineForm.id_rutina ? 'Actualizar Rutina' : 'Guardar Rutina') }}</span>
            </button>
          </div>
          <p v-if="routineForm.id_rutina !== null && !hasChanges" class="text-xs text-slate-400">No hay cambios por guardar.</p>
        </form>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
defineProps({
 maxNombre: Number, maxZonas: Number, isSaving: Boolean, showRoutineModal: Boolean,
 serviceOptions: Array, quickZones: Array, routineForm: { type: Object, required: true },
 touched: Object, submitted: Boolean, editingName: String, hasChanges: Boolean,
 editingAssignedCount: Number, errors: Object, fieldError: Function, exError: Function, zoneActive: Function,
});
defineEmits(['close', 'save', 'toggle-zone', 'add-exercise', 'remove-exercise', 'rep-mode', 'sync-reps']);
</script>
<style scoped src="../../styles/trainer-routines.css"></style>
