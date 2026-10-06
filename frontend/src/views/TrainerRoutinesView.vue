<template>
  <div class="space-y-6 text-white">
    <!-- Header principal -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-red-500 font-extrabold flex items-center gap-2">
            <i class="fa-solid fa-dumbbell"></i>
            Catálogo de Rutinas
          </p>
          <h1 class="mt-1 text-3xl font-black text-white">Supervisión & Gestión de Rutinas</h1>
          <p class="mt-1 text-sm text-slate-400">Diseña, edita y organiza las rutinas personalizadas del catálogo para los servicios del gimnasio.</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button class="flex items-center gap-2 rounded-2xl bg-red-600 px-5 py-3 text-sm font-extrabold text-white transition hover:bg-red-500 shadow-lg shadow-red-600/20" @click="openCreateModal">
            <i class="fa-solid fa-plus"></i>
            Crear nueva rutina
          </button>
          <button class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800 disabled:opacity-60" :disabled="isLoading" @click="refresh()">
            <i class="fa-solid fa-rotate-right" :class="{ 'fa-spin': isLoading }"></i>
            {{ isLoading ? 'Actualizando...' : 'Actualizar' }}
          </button>
        </div>
      </div>
    </section>

    <p v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">{{ errorMessage }}</p>

    <!-- Tarjetas KPI -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Total Rutinas</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-list-check text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ routines.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Rutinas en el catálogo general</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Con Ejercicios</p>
          <span class="rounded-full bg-emerald-500/10 p-2.5 text-emerald-400 border border-emerald-500/20">
            <i class="fa-solid fa-circle-check text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-emerald-400">{{ routinesWithExercisesCount }}</p>
        <p class="mt-1 text-xs text-slate-400">Listas para ser asignadas a clientes</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Promedio Ejercicios</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-bolt text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-red-400">{{ averageExercisesPerRoutine }}</p>
        <p class="mt-1 text-xs text-slate-400">Ejercicios promedio por rutina</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Servicios Cubiertos</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-layer-group text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ activeServicesCount }} / {{ serviceOptions.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Categorías con rutinas creadas</p>
      </div>
    </section>

    <!-- Sección de Filtros y Tabla -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur space-y-4">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Catálogo Registrado</p>
          <h2 class="text-xl font-black text-white">Lista de Rutinas Registradas</h2>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Selector de cantidad de filas por página (5, 7, 10) -->
          <div class="flex items-center gap-2 text-xs font-bold text-slate-400">
            <span>Ver:</span>
            <div class="flex items-center gap-1 rounded-xl bg-slate-900 p-1 border border-white/10">
              <button
                v-for="size in [5, 7, 10]"
                :key="size"
                type="button"
                class="px-2.5 py-1 rounded-lg font-black text-xs transition"
                :class="itemsPerPage === size ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                @click="setItemsPerPage(size)"
              >
                {{ size }}
              </button>
            </div>
          </div>

          <!-- Orden -->
          <select v-model="sortBy" class="field-input !w-auto text-xs py-2.5" aria-label="Ordenar rutinas">
            <option value="nombre">A-Z</option>
            <option value="ejercicios">Más ejercicios</option>
            <option value="asignados">Más asignadas</option>
          </select>
          <!-- Buscador -->
          <div class="relative w-full sm:w-64">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
            <input v-model="searchQuery" type="text" placeholder="Buscar por nombre, zona o ejercicio..." class="field-input search-input text-xs pr-4 py-2.5" />
          </div>
        </div>
      </div>

      <!-- Filtros por servicio -->
      <div class="flex flex-wrap gap-2 border-b border-white/10 pb-4">
        <button class="rounded-xl px-3.5 py-2 text-xs font-bold transition" :class="selectedServiceFilter === 'todos' ? 'bg-red-600 text-white shadow-md shadow-red-600/20' : 'bg-slate-900 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="setServiceFilter('todos')">
          Todos ({{ routines.length }})
        </button>
        <button v-for="service in serviceOptions" :key="service.value" class="rounded-xl px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5" :class="selectedServiceFilter === service.value ? 'bg-red-600 text-white shadow-md shadow-red-600/20' : 'bg-slate-900 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="setServiceFilter(service.value)">
          <span>{{ service.label }}</span>
          <span class="rounded-full px-2 py-0.5 text-[10px] font-extrabold" :class="selectedServiceFilter === service.value ? 'bg-black/40 text-white' : 'bg-white/10 text-slate-300'">
            {{ routinesForService(service.value).length }}
          </span>
        </button>
      </div>

      <!-- Tabla de Rutinas Registradas -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-300">
          <thead class="bg-black/60 text-xs uppercase text-slate-400 tracking-wider">
            <tr>
              <th class="p-3.5 rounded-l-xl">Servicio</th>
              <th class="p-3.5">Nombre de la Rutina</th>
              <th class="p-3.5">Zonas Musculares</th>
              <th class="p-3.5 text-center">N° Ejercicios</th>
              <th class="p-3.5 text-center">Clientes asignados</th>
              <th class="p-3.5 text-right rounded-r-xl">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr v-for="routine in paginatedRoutines" :key="routine.id_rutina" class="transition hover:bg-white/[0.03]">
              <td class="p-3.5">
                <span class="inline-block rounded-full border border-red-600/30 bg-red-600/10 px-3 py-1 text-xs font-bold text-red-400">
                  {{ serviceLabel(routine.servicio) }}
                </span>
              </td>
              <td class="p-3.5">
                <p class="font-bold text-white text-base">{{ routine.nombre_rutina || 'Sin nombre' }}</p>
                <p v-if="Number(routine.clientes_asignados || 0) > 0" class="mt-0.5 text-xs text-slate-400">
                  {{ routine.clientes_asignados }} {{ Number(routine.clientes_asignados) === 1 ? 'cliente asignado' : 'clientes asignados' }}
                </p>
              </td>
              <td class="p-3.5">
                <span class="text-xs text-slate-300 bg-slate-900 px-2.5 py-1 rounded-lg border border-white/5 inline-block">
                  {{ routine.zonas_musculares || 'General' }}
                </span>
              </td>
              <td class="p-3.5 text-center">
                <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="(routine.ejercicios || []).length ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'">
                  {{ (routine.ejercicios || []).length }} ej.
                </span>
              </td>
              <td class="p-3.5 text-center">{{ routine.clientes_asignados || 0 }}</td>
              <td class="p-3.5 text-right">
                <button class="rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-xs font-extrabold text-white transition hover:bg-red-600 hover:border-red-600 flex items-center gap-1.5 ml-auto" @click="editRoutine(routine)">
                  <i class="fa-solid fa-pen-to-square text-xs text-red-400"></i>
                  <span>Editar rutina</span>
                </button>
              </td>
            </tr>

            <tr v-if="!filteredRoutines.length">
              <td colspan="6" class="py-8 text-center text-slate-400">
                <p v-if="!routines.length" class="text-sm">Aún no hay rutinas registradas.</p>
                <template v-else>
                  <p class="text-sm">Ninguna rutina coincide con los filtros.</p>
                  <button type="button" class="mt-3 text-xs font-bold text-red-400 underline hover:text-red-300" @click="clearFilters">Limpiar filtros</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación Inferior de la Tabla -->
      <div v-if="filteredRoutines.length > 0" class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-white/10 pt-4 text-xs font-bold text-slate-400">
        <p>
          Mostrando <span class="text-white font-black">{{ showingStart }}</span> a <span class="text-white font-black">{{ showingEnd }}</span> de <span class="text-white font-black">{{ filteredRoutines.length }}</span> rutinas
        </p>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <i class="fa-solid fa-chevron-left text-[10px]"></i>
            <span>Anterior</span>
          </button>

          <div class="flex items-center gap-1">
            <button
              v-for="page in totalPages"
              :key="page"
              type="button"
              class="h-7 w-7 rounded-lg text-xs font-black transition flex items-center justify-center"
              :class="currentPage === page ? 'bg-red-600 text-white shadow-sm shadow-red-600/30' : 'bg-slate-900 text-slate-400 border border-white/10 hover:bg-slate-800 hover:text-white'"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
          </div>

          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <span>Siguiente</span>
            <i class="fa-solid fa-chevron-right text-[10px]"></i>
          </button>
        </div>
      </div>
    </section>

    <!-- MODAL DE CREACIÓN / EDICIÓN DE RUTINA (TELEPORTED TO BODY FOR FULLSCREEN OVERLAY) -->
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
            <button class="rounded-full bg-white/10 p-2 text-slate-400 hover:bg-white/20 hover:text-white transition" @click="requestCloseModal">
              <i class="fa-solid fa-xmark text-base"></i>
            </button>
          </div>

          <!-- Aviso de edición -->
          <div v-if="routineForm.id_rutina" class="rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-xs text-amber-50">
            <p class="font-bold">Editando: {{ editingName || 'Rutina' }}</p>
            <p v-if="editingAssignedCount > 0" class="mt-1 text-amber-100/80">
              Esta rutina está asignada a {{ editingAssignedCount }} {{ editingAssignedCount === 1 ? 'cliente' : 'clientes' }}. Los cambios los afectarán.
            </p>
          </div>

          <form class="space-y-5" novalidate @submit.prevent="saveRoutine">
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
                  <span class="font-normal" :class="routineForm.nombre_rutina.length > MAX_NOMBRE ? 'text-rose-300' : 'text-slate-500'">{{ routineForm.nombre_rutina.length }}/{{ MAX_NOMBRE }}</span>
                </span>
                <input v-model="routineForm.nombre_rutina" class="field-input text-sm" :class="{ 'field-error': fieldError('nombre_rutina') }" placeholder="Ej. Hipertrofia Tren Superior" @blur="touched.nombre_rutina = true" />
                <span v-if="fieldError('nombre_rutina')" class="block text-xs text-rose-300">{{ fieldError('nombre_rutina') }}</span>
              </label>
            </div>

            <label class="block space-y-1.5">
              <span class="flex items-center justify-between text-xs font-bold text-slate-300">
                <span>Zonas Musculares Trabajadas</span>
                <span class="font-normal" :class="routineForm.zonas_musculares.length > MAX_ZONAS ? 'text-rose-300' : 'text-slate-500'">{{ routineForm.zonas_musculares.length }}/{{ MAX_ZONAS }}</span>
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
                @click="toggleZone(zone)"
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
                <button type="button" class="flex items-center gap-1.5 rounded-xl bg-red-600/20 border border-red-600/30 px-3.5 py-1.5 text-xs font-bold text-red-400 hover:bg-red-600 hover:text-white transition" @click="addExercise">
                  <i class="fa-solid fa-plus text-xs"></i>
                  <span>Agregar Ejercicio</span>
                </button>
              </div>

              <p v-if="submitted && errors.ejercicios" class="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-xs text-rose-100">{{ errors.ejercicios }}</p>

              <div v-if="routineForm.ejercicios.length" class="space-y-4">
                <div v-for="(ex, index) in routineForm.ejercicios" :key="index" class="rounded-2xl border border-white/10 bg-slate-900/90 p-4 space-y-3 shadow-inner">
                  <div class="flex items-center justify-between border-b border-white/5 pb-2">
                    <span class="text-xs font-black text-red-400">Ejercicio #{{ index + 1 }}</span>
                    <button type="button" class="text-xs font-bold text-red-400 hover:text-red-300 hover:underline flex items-center gap-1" @click="removeExercise(index)">
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
                          @click="setRepMode(ex, 'fijo')"
                        >
                          Número Fijo
                        </button>
                        <button
                          type="button"
                          class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                          :class="ex.rep_modo === 'rango' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                          @click="setRepMode(ex, 'rango')"
                        >
                          Rango (ej. 10-12)
                        </button>
                        <button
                          type="button"
                          class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                          :class="ex.rep_modo === 'fallo' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                          @click="setRepMode(ex, 'fallo')"
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
                          @input="syncRepString(ex)"
                        />
                      </div>

                      <div v-else-if="ex.rep_modo === 'rango'" class="flex items-center gap-2 pt-1">
                        <input
                          v-model="ex.rep_min"
                          type="number"
                          min="1"
                          placeholder="Mín (ej. 10)"
                          class="field-input text-xs"
                          @input="syncRepString(ex)"
                        />
                        <span class="text-xs text-slate-400 font-bold">a</span>
                        <input
                          v-model="ex.rep_max"
                          type="number"
                          min="1"
                          placeholder="Máx (ej. 12)"
                          class="field-input text-xs"
                          @input="syncRepString(ex)"
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
              <button type="button" class="rounded-2xl border border-white/10 bg-slate-900 px-5 py-2.5 text-xs font-bold text-white transition hover:bg-slate-800" :disabled="isSaving" @click="requestCloseModal">
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

    <!-- TOAST DE NOTIFICACIÓN FLOTANTE (TELEPORTED TO BODY) -->
    <Teleport to="body">
      <div v-if="toastMessage" class="fixed bottom-6 right-6 z-50 max-w-sm animate-bounce-short">
        <div class="flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-md" :class="toastType === 'error' ? 'border-red-500/40 bg-slate-950 text-red-200 shadow-red-950/50' : 'border-emerald-500/40 bg-slate-950 text-emerald-200 shadow-emerald-950/50'">
          <span class="rounded-full p-1" :class="toastType === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'">
            <i v-if="toastType === 'error'" class="fa-solid fa-circle-exclamation text-base"></i>
            <i v-else class="fa-solid fa-circle-check text-base"></i>
          </span>
          <p class="text-xs font-bold">{{ toastMessage }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();

const MAX_NOMBRE = 60;
const MAX_ZONAS = 300;
const MAX_EJERCICIO = 80;

const isSaving = ref(false);
const isLoading = ref(false);
const errorMessage = ref('');
const showRoutineModal = ref(false);
const searchQuery = ref('');
const selectedServiceFilter = ref('todos');
const sortBy = ref('nombre');

// Paginación de la Tabla
const itemsPerPage = ref(5);
const currentPage = ref(1);

const setItemsPerPage = (size) => {
  itemsPerPage.value = size;
  currentPage.value = 1;
};

const setServiceFilter = (service) => {
  selectedServiceFilter.value = service;
  currentPage.value = 1;
};

// Toasts flotantes
const toastMessage = ref('');
const toastType = ref('success');
let toastTimer = null;

const showToast = (message, type = 'success') => {
  toastMessage.value = message;
  toastType.value = type;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = '';
  }, 4000);
};

const serviceOptions = [
  { value: 'fitness', label: 'Fitness' },
  { value: 'musculacion', label: 'Musculación' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'baile', label: 'Baile' },
];

const quickZones = ['Pierna', 'Glúteos', 'Core', 'Pecho', 'Espalda', 'Hombro', 'Brazos', 'Cardio'];

const routineForm = reactive({
  id_rutina: null,
  servicio: 'fitness',
  nombre_rutina: '',
  zonas_musculares: '',
  color: 'Azul',
  ejercicios: [],
});

// Estado de validación / edición
const touched = reactive({ nombre_rutina: false, zonas_musculares: false });
const submitted = ref(false);
const baselineSignature = ref(''); // "foto" del formulario al abrir el modal
const editingName = ref(''); // nombre original de la rutina en edición

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

/**
 * Normaliza texto para comparar (minúsculas, sin tildes, sin espacios extra).
 */
const norm = (value) =>
  String(value || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

// Métricas KPI
const routinesWithExercisesCount = computed(() => routines.value.filter((r) => Array.isArray(r.ejercicios) && r.ejercicios.length > 0).length);

const averageExercisesPerRoutine = computed(() => {
  if (!routines.value.length) return 0;
  const totalEx = routines.value.reduce((acc, r) => acc + (Array.isArray(r.ejercicios) ? r.ejercicios.length : 0), 0);
  return (totalEx / routines.value.length).toFixed(1);
});

const activeServicesCount = computed(() => new Set(routines.value.map((r) => norm(r.servicio))).size);

// Filtros, búsqueda y orden
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';

const routinesForService = (service) => routines.value.filter((routine) => norm(routine.servicio) === norm(service));

const exerciseCount = (routine) => (Array.isArray(routine.ejercicios) ? routine.ejercicios.length : 0);

const filteredRoutines = computed(() => {
  const query = norm(searchQuery.value);
  const list = routines.value.filter((r) => {
    const matchesService = selectedServiceFilter.value === 'todos' || norm(r.servicio) === selectedServiceFilter.value;
    const matchesSearch =
      !query ||
      norm(r.nombre_rutina).includes(query) ||
      norm(r.zonas_musculares).includes(query) ||
      (Array.isArray(r.ejercicios) && r.ejercicios.some((ex) => norm(ex.nombre_ejercicio).includes(query)));
    return matchesService && matchesSearch;
  });

  return [...list].sort((a, b) => {
    if (sortBy.value === 'asignados') return Number(b.clientes_asignados || 0) - Number(a.clientes_asignados || 0);
    if (sortBy.value === 'ejercicios') return exerciseCount(b) - exerciseCount(a);
    return String(a.nombre_rutina || '').localeCompare(String(b.nombre_rutina || ''), 'es');
  });
});

const clearFilters = () => {
  searchQuery.value = '';
  setServiceFilter('todos');
};

const totalPages = computed(() => Math.ceil(filteredRoutines.value.length / itemsPerPage.value) || 1);

const paginatedRoutines = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  return filteredRoutines.value.slice(start, start + itemsPerPage.value);
});

const showingStart = computed(() => {
  if (!filteredRoutines.value.length) return 0;
  return (currentPage.value - 1) * itemsPerPage.value + 1;
});

const showingEnd = computed(() => Math.min(currentPage.value * itemsPerPage.value, filteredRoutines.value.length));

// Al cambiar búsqueda u orden vuelve a la página 1; si la página actual ya no existe (p. ej. tras guardar), se ajusta
watch([searchQuery, sortBy], () => {
  currentPage.value = 1;
});
watch(totalPages, (pages) => {
  if (currentPage.value > pages) currentPage.value = pages;
});

// Ayudantes de parsing y sincronización de modos de repetición
const parseRepeticiones = (repStr) => {
  const str = String(repStr || '').trim();
  if (str.toLowerCase().includes('fallo')) {
    return { rep_modo: 'fallo', rep_fijo: '', rep_min: '', rep_max: '', repeticiones: 'Al fallo' };
  }
  if (str.includes('-')) {
    const parts = str.split('-');
    return {
      rep_modo: 'rango',
      rep_fijo: '',
      rep_min: (parts[0] || '10').trim(),
      rep_max: (parts[1] || '12').trim(),
      repeticiones: str,
    };
  }
  return {
    rep_modo: 'fijo',
    rep_fijo: str || '10',
    rep_min: '',
    rep_max: '',
    repeticiones: str || '10',
  };
};

/**
 * Construye el texto de repeticiones según el modo (sin modificar el ejercicio).
 */
const buildRepString = (ex) => {
  if (ex.rep_modo === 'fijo') return String(ex.rep_fijo || '10');
  if (ex.rep_modo === 'rango') return `${ex.rep_min || '10'}-${ex.rep_max || '12'}`;
  return 'Al fallo';
};

const syncRepString = (ex) => {
  ex.repeticiones = buildRepString(ex);
};

const setRepMode = (ex, mode) => {
  ex.rep_modo = mode;
  if (mode === 'fijo' && !ex.rep_fijo) ex.rep_fijo = '10';
  if (mode === 'rango') {
    if (!ex.rep_min) ex.rep_min = '10';
    if (!ex.rep_max) ex.rep_max = '12';
  }
  syncRepString(ex);
};

/**
 * Convierte un ejercicio del formulario al formato que se envía / compara.
 */
const buildExercise = (ex) => ({
  id_ejercicio: ex.id_ejercicio ?? null,
  nombre_ejercicio: String(ex.nombre_ejercicio || '').trim(),
  grupo_muscular: String(ex.grupo_muscular || '').trim(),
  series: Number(ex.series || 3),
  repeticiones: buildRepString(ex),
  descanso_segundos: Number(ex.descanso_segundos || 60),
  peso_sugerido_kg: ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== undefined && ex.peso_sugerido_kg !== '' ? Number(ex.peso_sugerido_kg) : null,
  notas: ex.notas || '',
});

/**
 * Datos del formulario ya limpios (los que se guardan).
 */
const buildPayload = () => ({
  ...routineForm,
  nombre_rutina: routineForm.nombre_rutina.trim(),
  zonas_musculares: routineForm.zonas_musculares.trim(),
  ejercicios: routineForm.ejercicios.map(buildExercise),
});

const buildSignature = () => {
  const { servicio, nombre_rutina, zonas_musculares, ejercicios } = buildPayload();
  return JSON.stringify({ servicio, nombre_rutina, zonas_musculares, ejercicios });
};

// ---------- Cambios sin guardar ----------
const hasChanges = computed(() => buildSignature() !== baselineSignature.value);

const editingAssignedCount = computed(() => {
  const current = routines.value.find((r) => r.id_rutina === routineForm.id_rutina);
  return Number(current?.clientes_asignados || 0);
});

// ---------- Validaciones (en vivo) ----------
const exerciseErrors = computed(() =>
  routineForm.ejercicios.map((ex) => {
    const result = {};
    const nombre = String(ex.nombre_ejercicio || '').trim();
    const series = Number(ex.series);

    if (!nombre) result.nombre = 'El nombre es obligatorio.';
    else if (nombre.length > MAX_EJERCICIO) result.nombre = `Máximo ${MAX_EJERCICIO} caracteres.`;

    if (!Number.isInteger(series) || series < 1 || series > 20) result.series = 'Entre 1 y 20.';

    if (ex.rep_modo === 'fijo') {
      const fijo = Number(ex.rep_fijo);
      if (!Number.isInteger(fijo) || fijo < 1) result.reps = 'Indica un número de repeticiones válido.';
    } else if (ex.rep_modo === 'rango') {
      const min = Number(ex.rep_min);
      const max = Number(ex.rep_max);
      if (!Number.isInteger(min) || !Number.isInteger(max) || min < 1) result.reps = 'Indica un mínimo y un máximo válidos.';
      else if (max <= min) result.reps = 'El máximo debe ser mayor que el mínimo.';
    }

    const peso = ex.peso_sugerido_kg;
    if (peso !== null && peso !== undefined && peso !== '' && (!Number.isFinite(Number(peso)) || Number(peso) < 0)) {
      result.peso = 'El peso no puede ser negativo.';
    }
    return result;
  }),
);

const errors = computed(() => {
  const result = {};
  const nombre = routineForm.nombre_rutina.trim();
  const zonas = routineForm.zonas_musculares.trim();

  if (!serviceOptions.some((service) => service.value === routineForm.servicio)) {
    result.servicio = 'Selecciona un servicio válido.';
  }

  if (!nombre) {
    result.nombre_rutina = 'El nombre es obligatorio.';
  } else if (nombre.length < 3) {
    result.nombre_rutina = 'Usa al menos 3 caracteres.';
  } else if (nombre.length > MAX_NOMBRE) {
    result.nombre_rutina = `Máximo ${MAX_NOMBRE} caracteres.`;
  } else if (
    routines.value.some(
      (r) => r.id_rutina !== routineForm.id_rutina && norm(r.servicio) === routineForm.servicio && norm(r.nombre_rutina) === norm(nombre),
    )
  ) {
    result.nombre_rutina = 'Ya existe una rutina con ese nombre en este servicio.';
  }

  if (!zonas) {
    result.zonas_musculares = 'Indica al menos una zona muscular.';
  } else if (zonas.length < 3) {
    result.zonas_musculares = 'Describe las zonas con más detalle.';
  } else if (zonas.length > MAX_ZONAS) {
    result.zonas_musculares = `Máximo ${MAX_ZONAS} caracteres.`;
  }

  const badExercises = exerciseErrors.value.filter((e) => Object.keys(e).length).length;
  if (badExercises) {
    result.ejercicios = `Revisa ${badExercises} ${badExercises === 1 ? 'ejercicio' : 'ejercicios'} con datos incompletos o inválidos.`;
  }

  return result;
});

/**
 * Muestra el error solo si el campo fue tocado o ya se intentó guardar.
 */
const fieldError = (field) => (submitted.value || touched[field] ? errors.value[field] : '');

/**
 * Error de un campo de un ejercicio (solo después de intentar guardar).
 */
const exError = (index, field) => (submitted.value ? exerciseErrors.value[index]?.[field] : '');

// ---------- Zonas rápidas ----------
const zoneActive = (zone) => routineForm.zonas_musculares.split(',').some((part) => norm(part) === norm(zone));

const toggleZone = (zone) => {
  const parts = routineForm.zonas_musculares.split(',').map((part) => part.trim()).filter(Boolean);
  const index = parts.findIndex((part) => norm(part) === norm(zone));
  if (index >= 0) parts.splice(index, 1);
  else parts.push(zone);
  routineForm.zonas_musculares = parts.join(', ');
  touched.zonas_musculares = true;
};

// ---------- Modal & ejercicios ----------
const addExercise = () => {
  routineForm.ejercicios.push({
    nombre_ejercicio: '',
    series: 3,
    rep_modo: 'rango',
    rep_fijo: '10',
    rep_min: '10',
    rep_max: '12',
    repeticiones: '10-12',
    descanso_segundos: 60,
    peso_sugerido_kg: null,
    grupo_muscular: '',
    notas: '',
  });
};

const removeExercise = (index) => {
  routineForm.ejercicios.splice(index, 1);
};

const resetRoutineForm = () => {
  routineForm.id_rutina = null;
  routineForm.servicio = 'fitness';
  routineForm.nombre_rutina = '';
  routineForm.zonas_musculares = '';
  routineForm.color = 'Azul';
  routineForm.ejercicios = [];
  submitted.value = false;
  touched.nombre_rutina = false;
  touched.zonas_musculares = false;
  editingName.value = '';
  baselineSignature.value = buildSignature();
};

/**
 * Abre el modal y guarda la "foto" inicial para detectar cambios.
 */
const openModal = () => {
  baselineSignature.value = buildSignature();
  showRoutineModal.value = true;
};

const openCreateModal = () => {
  resetRoutineForm();
  // Si hay un servicio filtrado, la rutina nueva se crea en ese servicio
  if (selectedServiceFilter.value !== 'todos') routineForm.servicio = selectedServiceFilter.value;
  openModal();
};

const editRoutine = (routine) => {
  resetRoutineForm();
  routineForm.id_rutina = routine.id_rutina;
  routineForm.servicio = routine.servicio || 'fitness';
  routineForm.nombre_rutina = routine.nombre_rutina || '';
  routineForm.zonas_musculares = routine.zonas_musculares || '';
  routineForm.color = routine.color || 'Azul';
  routineForm.ejercicios = Array.isArray(routine.ejercicios)
    ? routine.ejercicios.map((ex) => ({
        ...ex,
        ...parseRepeticiones(ex.repeticiones),
      }))
    : [];
  editingName.value = routineForm.nombre_rutina;
  openModal();
};

/**
 * Cierra el modal sin preguntar (después de guardar).
 */
const closeRoutineModal = () => {
  showRoutineModal.value = false;
  resetRoutineForm();
};

/**
 * Cierra el modal pidiendo confirmación solo si hay cambios sin guardar.
 */
const requestCloseModal = () => {
  if (hasChanges.value && !window.confirm('Tienes cambios sin guardar. ¿Descartarlos?')) return;
  closeRoutineModal();
};

const saveRoutine = async () => {
  submitted.value = true;
  if (Object.keys(errors.value).length) {
    showToast('Revisa los campos marcados antes de guardar.', 'error');
    return;
  }

  if (isSaving.value) return;
  const wasEditing = routineForm.id_rutina !== null;
  try {
    isSaving.value = true;
    await gymStore.upsertTrainerRoutine(buildPayload());
    showToast(wasEditing ? 'Rutina actualizada exitosamente.' : 'Nueva rutina creada exitosamente.', 'success');
    closeRoutineModal();
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo guardar la rutina.', 'error');
  } finally {
    isSaving.value = false;
  }
};

const refresh = async (notify = true) => {
  if (isLoading.value) return;
  try {
    isLoading.value = true;
    errorMessage.value = '';
    await gymStore.fetchTrainerOverview();
    if (notify) showToast('Datos del catálogo actualizados.', 'success');
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar rutinas.';
    showToast(errorMessage.value, 'error');
  } finally {
    isLoading.value = false;
  }
};

// Carga inicial silenciosa (sin toast de "actualizados")
onMounted(() => refresh(false));
onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});
</script>

<style scoped>
.field-error { border-color: rgb(251, 113, 133) !important; }
.field-input {
  width: 100%;
  border: 1px solid var(--app-border, rgba(255, 255, 255, 0.1));
  border-radius: 1rem;
  background: var(--app-input, rgba(2, 6, 23, 0.72));
  padding: 0.75rem 1rem;
  color: var(--app-text, white);
  outline: none;
}

[data-theme="light"] .field-input,
[data-theme="light"] select.field-input {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border-color: #cbd5e1 !important;
}

[data-theme="light"] select.field-input option {
  background-color: #ffffff !important;
  color: #0f172a !important;
}

.field-input::placeholder {
  color: var(--app-text-faint, #64748b);
}

.field-error {
  border-color: rgba(251, 113, 133, 0.7) !important;
}

.search-input {
  padding-left: 2.75rem !important;
}

@keyframes bounceShort {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-bounce-short {
  animation: bounceShort 0.3s ease-in-out;
}
</style>