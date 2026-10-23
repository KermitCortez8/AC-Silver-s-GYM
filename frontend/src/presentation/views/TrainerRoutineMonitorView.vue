<template>
  <div class="space-y-6 relative text-white">
    <!-- TOAST NOTIFICATION CONTAINER (FLOTANTE EN ESQUINA INFERIOR DERECHA) -->
    <Teleport to="body">
      <div v-if="toast.show" class="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border px-5 py-4 shadow-2xl backdrop-blur-xl transition-all animate-bounce-short" :class="toast.type === 'error' ? 'border-red-500/40 bg-slate-950 text-red-200 shadow-red-950/50' : 'border-emerald-500/40 bg-slate-950 text-emerald-200 shadow-emerald-950/50'">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-bold" :class="toast.type === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'">
          <i v-if="toast.type === 'error'" class="fa-solid fa-circle-exclamation text-base"></i>
          <i v-else class="fa-solid fa-circle-check text-base"></i>
        </div>
        <div>
          <p class="text-[11px] uppercase tracking-wider font-bold opacity-70">{{ toast.type === 'error' ? 'Error u Operación Fallida' : 'Notificación del Sistema' }}</p>
          <p class="text-xs font-semibold text-white mt-0.5">{{ toast.message }}</p>
        </div>
        <button class="ml-4 text-slate-400 hover:text-white font-bold text-sm" @click="toast.show = false">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </Teleport>

    <!-- Header & Búsqueda (ROJO Y NEGRO) -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-red-500 font-extrabold flex items-center gap-2">
            <i class="fa-solid fa-dumbbell"></i>
            Módulo Entrenador
          </p>
          <h1 class="mt-1 text-3xl font-black text-white">Supervisión y Seguimiento de Rutinas</h1>
          <p class="mt-1 text-sm text-slate-400">Consulta alumnos matriculados, asigna nuevas rutinas personalizadas y registra el progreso de ejercicios.</p>
        </div>
        <!-- Búsqueda con autocompletado: integra ambos cambios del conflicto. -->
        <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="searchClient">
          <div class="relative min-w-64 sm:w-80">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
            <input
              v-model="dni"
              class="field-input search-input text-xs"
              type="text"
              inputmode="numeric"
              maxlength="8"
              autocomplete="off"
              placeholder="Ingresa DNI del cliente"
              aria-label="DNI del cliente"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="dni-suggestions"
              :aria-expanded="showSuggestions"
              :aria-activedescendant="activeIndex >= 0 && showSuggestions ? `dni-option-${activeIndex}` : undefined"
              @input="onDniInput"
              @focus="openSuggestions"
              @blur="open = false"
              @keydown.down.prevent="moveActive(1)"
              @keydown.up.prevent="moveActive(-1)"
              @keydown.enter="onEnter"
              @keydown.esc="open = false"
            />
            <ul
              v-if="showSuggestions"
              id="dni-suggestions"
              role="listbox"
              class="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-white/10 bg-slate-950 p-1 shadow-xl"
              @mousedown.prevent
            >
              <li
                v-for="(client, index) in suggestions"
                :id="`dni-option-${index}`"
                :key="client.dni"
                role="option"
                :aria-selected="index === activeIndex"
                class="cursor-pointer rounded-xl px-3 py-2 text-sm"
                :class="index === activeIndex ? 'bg-red-600/25 text-white' : 'text-slate-200 hover:bg-white/10'"
                @mousedown.prevent="pickClient(client.dni)"
                @mouseenter="activeIndex = index"
              >
                <span class="font-bold text-red-400">{{ client.dni.slice(0, dni.length) }}</span>{{ client.dni.slice(dni.length) }}
                <span class="ml-2 text-slate-400">· {{ client.nombre }}</span>
              </li>
              <li v-if="!suggestions.length" class="px-3 py-2 text-sm text-slate-400" role="option" aria-disabled="true" aria-selected="false">
                Ningún cliente con matrícula activa empieza con {{ dni }}. Puedes buscar ese DNI directamente.
              </li>
            </ul>
          </div>
          <button
            type="submit"
            class="flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="searching"
          >
            <i class="fa-solid fa-magnifying-glass"></i>
            <span>{{ searching ? 'Buscando…' : 'Buscar Cliente' }}</span>
          </button>
        </form>
      </div>
    </section>

    <p
      v-if="feedback"
      role="status"
      class="rounded-2xl border px-4 py-3 text-sm"
      :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'"
    >
      {{ feedback }}
    </p>

    <!-- Visual Rest Timer (Flotante en Vista Principal - ROJO Y NEGRO) -->
    <section v-if="timerActive || timerSeconds > 0 || timerFinished" class="rounded-2xl border border-red-500/40 bg-black/90 p-4 shadow-xl transition-all">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-red-500/20 text-red-400 font-black">
            <i class="fa-solid fa-stopwatch text-lg"></i>
          </div>
          <div>
            <p class="text-[11px] uppercase tracking-wider text-slate-400 font-bold">Temporizador de Descanso entre Series</p>
            <p class="text-2xl font-black text-white" :class="{ 'text-emerald-400 animate-pulse': timerSeconds === 0 }">
              {{ formatTimer(timerSeconds) }}
              <span v-if="timerSeconds === 0" class="text-xs font-bold text-emerald-400 ml-2">¡Tiempo de descanso finalizado!</span>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="!timerActive" class="rounded-xl bg-red-600 px-4 py-2 font-black text-white text-xs hover:bg-red-500 transition flex items-center gap-1.5" @click="timerSeconds > 0 ? startTimer() : setRestTimer(timerInitialSeconds)">
            <i class="fa-solid fa-play text-xs"></i>
            <span>{{ timerSeconds > 0 ? 'Reanudar' : 'Iniciar' }}</span>
          </button>
          <button v-else class="rounded-xl bg-amber-500 px-4 py-2 font-black text-slate-950 text-xs hover:bg-amber-400 transition flex items-center gap-1.5" @click="pauseTimer">
            <i class="fa-solid fa-pause text-xs"></i>
            <span>Pausar</span>
          </button>
          <button class="rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-800 transition flex items-center gap-1.5" @click="resetTimer">
            <i class="fa-solid fa-rotate-right text-xs"></i>
            <span>Reiniciar</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Estado 1: ANIMACIÓN DE CARGA GIRATORIA CUANDO ESTÁ BUSCANDO -->
    <section v-if="isSearching" class="rounded-2xl border border-white/10 bg-slate-950 p-12 text-center backdrop-blur shadow-2xl space-y-4">
      <div class="flex flex-col items-center justify-center gap-4">
        <div class="relative flex h-16 w-16 items-center justify-center">
          <div class="absolute h-16 w-16 animate-spin rounded-full border-4 border-red-600 border-t-transparent shadow-lg shadow-red-600/40"></div>
          <i class="fa-solid fa-magnifying-glass text-xl text-red-500 animate-pulse"></i>
        </div>
        <div class="space-y-1">
          <p class="text-base font-black text-white">Consultando información del cliente...</p>
          <p class="text-xs text-slate-400">Buscando DNI <span class="font-mono font-bold text-red-400">{{ dni }}</span> y cargando rutinas asignadas</p>
        </div>
      </div>
    </section>

    <!-- Estado 2: Panel de información del Cliente (ROJO Y NEGRO) -->
    <section v-else-if="clientData?.cliente" class="space-y-6">
      <!-- BARRA SUPERIOR DE DATOS DEL CLIENTE -->
      <div class="rounded-2xl border border-white/10 bg-slate-950 p-4 backdrop-blur shadow-lg">
        <div class="flex flex-wrap items-center justify-between gap-4 text-xs font-semibold text-slate-200">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-user text-red-500"></i>
            <span class="text-slate-400">Cliente:</span>
            <span class="font-black text-white text-sm">{{ clientData.cliente.nombre }}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-id-card text-red-400"></i>
            <span class="text-slate-400">DNI:</span>
            <span class="font-mono text-red-400 font-bold">{{ clientData.cliente.dni }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Membresía:</span>
            <span class="rounded-full px-3 py-0.5 text-xs font-bold" :class="hasActiveMembership ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'">
              {{ membershipLabel }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Código ID:</span>
            <span class="text-slate-300 font-mono">{{ clientData.cliente.id_usuario }}</span>
          </div>

          <!-- BOTÓN INTEGRADO DE ACCIÓN: + ASIGNAR RUTINA PERSONALIZADA (ROJO SÓLIDO) -->
          <button
            type="button"
            class="flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!hasActiveMembership"
            @click="openAssignModal"
          >
            <i class="fa-solid fa-plus text-xs"></i>
            <span>Asignar rutina personalizada</span>
          </button>
        </div>
      </div>

      <p
        v-if="!hasActiveMembership"
        class="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100"
        role="alert"
      >
        {{ clientData.cliente.nombre }} no tiene una matrícula activa. Para asignar una rutina, primero debe matricularse en un horario.
      </p>

      <!-- LISTADO DE RUTINAS ASIGNADAS -->
      <div class="space-y-4">
        <article v-for="item in clientData.matriculas" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-xl space-y-4">
          <!-- Cabecera de la rutina y Botones de Acción -->
          <div class="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-4">
            <div>
              <div class="flex items-center gap-3">
                <h3 class="text-xl font-black text-white flex items-center gap-2">
                  <i class="fa-solid fa-dumbbell text-red-500 text-lg"></i>
                  {{ item.rutina_nombre || ('Servicio de ' + serviceLabel(item.servicio)) }}
                </h3>
                <span class="rounded-full bg-red-600/20 px-3 py-1 text-xs font-bold text-red-300 border border-red-600/30">
                  {{ serviceLabel(item.servicio) }}
                </span>
              </div>
              <div class="mt-2 grid gap-1 text-xs text-slate-300 sm:grid-cols-2">
                <p><strong class="text-slate-400">Día:</strong> {{ dayLabel(item.dia) }}</p>
                <p><strong class="text-slate-400">Hora:</strong> {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
                <p class="sm:col-span-2"><strong class="text-slate-400">Zonas musculares:</strong> {{ item.zonas_musculares || 'General / Fuerza' }}</p>
                <p class="sm:col-span-2"><strong class="text-slate-400">Estado:</strong>
                  <span class="font-bold ml-1" :class="item.id_rutina ? 'text-emerald-400' : 'text-amber-400'">
                    {{ item.id_rutina ? 'En progreso' : 'Pendiente asignación' }}
                  </span>
                </p>
              </div>
            </div>

            <!-- Botones Editar / Eliminar -->
            <div class="flex items-center gap-2">
              <button
                v-if="item.id_rutina"
                class="rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 transition flex items-center gap-1.5"
                @click="openExercisesModal(item)"
              >
                <i class="fa-solid fa-pen-to-square text-xs text-red-400"></i>
                <span>Editar / Ejercicios</span>
              </button>
              <button
                v-if="item.id_rutina"
                class="rounded-xl border border-red-500/30 bg-red-600/20 px-4 py-2 text-xs font-bold text-red-300 hover:bg-red-600 hover:text-white transition flex items-center gap-1.5"
                @click="confirmUnassign(item)"
              >
                <i class="fa-solid fa-trash text-xs"></i>
                <span>Eliminar</span>
              </button>
            </div>
          </div>

          <!-- Indicadores conservados de la rama de asignación. -->
          <div class="flex flex-wrap gap-2">
            <span
              class="rounded-full px-3 py-1 text-xs font-bold"
              :class="isEnrollmentActive(item) ? 'bg-emerald-400/15 text-emerald-200' : 'bg-amber-400/15 text-amber-200'"
            >
              {{ isEnrollmentActive(item) ? 'Matrícula activa' : 'Matrícula no activa' }}
            </span>
            <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200">
              {{ item.rutina_origen === 'cliente' ? 'Rutina del cliente' : 'Rutina del servicio' }}
            </span>
          </div>

          <!-- Asignación directa por matrícula, además del modal personalizado. -->
          <div class="grid gap-3 sm:grid-cols-[1fr_auto]">
            <select
              class="field-input text-sm"
              :value="selectedRoutine(item)"
              :disabled="!canAssign(item) || assigningId === item.id_matricula"
              :aria-label="`Rutina para ${serviceLabel(item.servicio)}`"
              @change="selection[item.id_matricula] = Number($event.target.value)"
            >
              <option :value="0" disabled>Selecciona una rutina de {{ serviceLabel(item.servicio) }}</option>
              <option v-for="routine in routinesForService(item.servicio)" :key="routine.id_rutina" :value="routine.id_rutina">
                {{ routine.nombre_rutina }}
              </option>
            </select>
            <button
              type="button"
              class="rounded-2xl bg-red-600 px-4 py-3 text-xs font-black text-white disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              :disabled="!canAssign(item) || !hasChange(item) || Boolean(assigningId)"
              @click="assignRoutine(item)"
            >
              {{ assigningId === item.id_matricula ? 'Asignando…' : 'Asignar' }}
            </button>
          </div>
          <button
            type="button"
            class="w-full rounded-2xl bg-emerald-500 px-4 py-3 text-xs font-black text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            :disabled="!item.id_rutina || !isEnrollmentActive(item) || markingId === item.id_matricula"
            @click="markDone(item)"
          >
            {{ markingId === item.id_matricula ? 'Registrando…' : 'Check realizado' }}
          </button>
          <p
            v-if="isEnrollmentActive(item) && !hasCompatibleRoutines(item)"
            class="rounded-xl border border-amber-400/20 bg-amber-400/10 px-3 py-2 text-sm text-amber-100"
            role="status"
          >
            No hay rutinas compatibles con el servicio {{ serviceLabel(item.servicio) }}. Crea una en la sección Rutinas para poder asignarla.
          </p>

          <!-- Historial de avance reciente -->
          <div>
            <p class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-clock-rotate-left text-xs text-red-500"></i>
              Avance reciente registrado
            </p>
            <div v-if="sortedProgress(item.progreso).length" class="mt-3 space-y-3 max-h-72 overflow-y-auto pr-1">
              <div v-for="progress in sortedProgress(item.progreso)" :key="progress.id_progreso" class="rounded-xl bg-black/80 p-4 text-xs space-y-2 border border-white/10">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="flex items-center gap-1.5 font-bold text-red-400">
                    <i class="fa-regular fa-calendar text-[11px]"></i>
                    {{ formatProgressDate(progress.fecha) }}
                  </span>
                  <span v-if="isCompleted(progress.estado)" class="rounded-full bg-emerald-500/20 px-3 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">
                    <i class="fa-solid fa-check mr-1 text-[9px]"></i>Rutina completada
                  </span>
                  <span v-else class="rounded-full bg-amber-500/20 px-3 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/30">
                    Pendiente
                  </span>
                </div>
                <p class="text-slate-300">
                  <strong class="text-slate-400">Observación:</strong>
                  {{ progress.observacion || 'Sin observación registrada' }}
                </p>
                <div v-if="(progress.ejercicios_detalle || []).length" class="mt-1 space-y-1 border-t border-white/5 pt-2">
                  <div v-for="(exDet, detIdx) in progress.ejercicios_detalle" :key="detIdx" class="text-[11px] text-slate-300 flex justify-between">
                    <span>
                      <i v-if="exDet.completado" class="fa-solid fa-check text-emerald-400 mr-1 text-[10px]"></i>
                      {{ exDet.nombre_ejercicio }}
                    </span>
                    <span class="text-slate-400">{{ exDet.series_completadas }} series <template v-if="exDet.peso_utilizado_kg">· {{ exDet.peso_utilizado_kg }} kg</template></span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="mt-3 rounded-xl border border-dashed border-white/10 p-4 text-center text-xs text-slate-500">
              Aún no hay progreso registrado
            </div>
          </div>
        </article>
      </div>

    </section>

    <!-- Estado 3: ESTADO VACÍO PREVIO A LA BÚSQUEDA -->
    <section v-else class="empty-state-card rounded-2xl border border-dashed border-white/10 bg-slate-900/60 p-12 text-center shadow-lg">
      <div class="mx-auto max-w-sm space-y-3">
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-600/10 text-red-500 font-bold text-2xl border border-red-600/30 shadow-inner">
          <i class="fa-solid fa-magnifying-glass"></i>
        </div>
        <h3 class="text-lg font-black text-white">Consulta y Asignación de Alumnos</h3>
        <p class="text-xs text-slate-400 leading-relaxed">Ingresa el número de DNI del alumno arriba y haz clic en "Buscar Cliente" para consultar sus rutinas y registrar progresos.</p>
      </div>
    </section>

    <!-- MODAL: Asignar Nueva Rutina Personalizada -->
    <Teleport to="body">
      <div v-if="showAssignModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md">
        <div class="w-full max-w-xl rounded-3xl border border-white/15 bg-slate-950 p-6 shadow-2xl space-y-5 text-white">
          <div class="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 class="text-xl font-black text-white flex items-center gap-2">
              <i class="fa-solid fa-plus text-red-500 text-sm"></i>
              <span>Asignar rutina personalizada</span>
            </h3>
            <button class="rounded-full bg-white/10 p-2 text-slate-400 hover:text-white transition" @click="showAssignModal = false">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="space-y-4">
            <label class="block space-y-2">
              <span class="text-xs uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5">
                <i class="fa-solid fa-dumbbell text-red-500/80"></i>
                <span>Seleccionar servicio matriculado del cliente</span>
              </span>
              <select v-model="assignForm.id_matricula" class="field-input text-sm cursor-pointer font-medium" @change="assignForm.id_rutina = 0">
                <option v-for="mat in (clientData?.matriculas || []).filter(isEnrollmentActive)" :key="mat.id_matricula" :value="mat.id_matricula">
                  {{ serviceLabel(mat.servicio) }} ({{ dayLabel(mat.dia) }} {{ mat.hora_inicio }} - {{ mat.hora_fin }})
                </option>
              </select>
            </label>

            <label class="block space-y-2">
              <span class="text-xs uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5">
                <i class="fa-solid fa-list-check text-red-500/80"></i>
                <span>Rutina del catálogo a vincular</span>
              </span>
              <select v-model="assignForm.id_rutina" class="field-input text-sm cursor-pointer font-medium">
                <option :value="0" disabled>Selecciona una rutina del catálogo</option>
                <option v-for="routine in availableRoutinesForSelectedMatricula" :key="routine.id_rutina" :value="routine.id_rutina">
                  {{ routine.nombre_rutina }} ({{ (routine.ejercicios || []).length }} ejercicios)
                </option>
              </select>
              <p v-if="!availableRoutinesForSelectedMatricula.length" class="text-xs text-amber-300">
                No hay rutinas compatibles con el servicio seleccionado.
              </p>
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button class="rounded-xl bg-slate-900 border border-white/10 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition" @click="showAssignModal = false">
              Cancelar
            </button>
            <button
              class="flex items-center gap-2 rounded-xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30 disabled:bg-slate-800 disabled:text-slate-500 disabled:border disabled:border-white/10 disabled:shadow-none disabled:cursor-not-allowed"
              :disabled="!canSubmitAssign || Boolean(assigningId)"
              @click="submitAssignRoutine"
            >
              <i class="fa-solid fa-check"></i>
                <span>{{ assigningId ? 'Guardando…' : 'Guardar rutina' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- MODAL ANCHO Y COMPACTO DE EJERCICIOS Y SEGUIMIENTO (TEMA ROJO Y NEGRO - ANCHO MAX 6XL SIN SCROLL VERTICAL) -->
    <Teleport to="body">
      <div v-if="showExercisesModal && selectedMatriculaItem" class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-3 sm:p-6 backdrop-blur-md overflow-y-auto">
        <div class="relative w-full max-w-6xl rounded-3xl border border-white/15 bg-slate-950 p-5 sm:p-6 shadow-2xl space-y-3 text-white my-auto max-h-[95vh] overflow-y-auto">

          <!-- Header del Modal -->
          <div class="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <div class="flex flex-wrap items-center gap-2.5">
                <h3 class="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                  <i class="fa-solid fa-square-check text-red-500"></i>
                  {{ selectedMatriculaItem.rutina_nombre }}
                </h3>
                <span class="rounded-full bg-red-600/20 px-3 py-0.5 text-xs font-extrabold text-red-400 border border-red-600/30">
                  {{ serviceLabel(selectedMatriculaItem.servicio) }}
                </span>
                <span class="rounded-full bg-emerald-500/20 px-3 py-0.5 text-xs font-black text-emerald-300 border border-emerald-500/30">
                  EN PROGRESO
                </span>
              </div>
              <p class="text-xs text-slate-400 mt-0.5">
                Zonas musculares: <span class="text-slate-200 font-semibold">{{ selectedMatriculaItem.zonas_musculares || 'General' }}</span>
              </p>
            </div>
            <button class="rounded-full bg-white/10 p-2 text-slate-400 hover:bg-white/20 hover:text-white transition" @click="showExercisesModal = false">
              <i class="fa-solid fa-xmark text-lg"></i>
            </button>
          </div>

          <!-- WIDGET CRONÓMETRO DE DESCANSO EN TIEMPO REAL (Fondo Negro Oscuro + Rojo, Sin Gradientes) -->
          <div v-if="timerActive || timerSeconds > 0 || timerFinished" class="rounded-2xl border border-red-500/40 bg-black p-3 shadow-xl space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-red-600/20 text-red-400 font-black border border-red-600/30">
                  <i class="fa-solid fa-stopwatch text-base"></i>
                </span>
                <div>
                  <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Cronómetro de Descanso En Vivo</p>
                  <p class="text-lg font-black text-white" :class="{ 'text-emerald-400 animate-pulse': timerSeconds === 0 }">
                    {{ formatTimer(timerSeconds) }}
                    <span v-if="timerSeconds === 0" class="text-xs font-extrabold text-emerald-400 ml-2">¡Tiempo completado!</span>
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button v-if="!timerActive" class="rounded-xl bg-red-600 px-3.5 py-1.5 font-black text-white text-xs hover:bg-red-500 transition flex items-center gap-1.5" @click="timerSeconds > 0 ? startTimer() : setRestTimer(timerInitialSeconds)">
                  <i class="fa-solid fa-play text-[10px]"></i>
                  <span>{{ timerSeconds > 0 ? 'Reanudar' : 'Iniciar' }}</span>
                </button>
                <button v-else class="rounded-xl bg-amber-500 px-3.5 py-1.5 font-black text-slate-950 text-xs hover:bg-amber-400 transition flex items-center gap-1.5" @click="pauseTimer">
                  <i class="fa-solid fa-pause text-[10px]"></i>
                  <span>Pausar</span>
                </button>
                <button class="rounded-xl border border-white/10 bg-slate-900 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-800 transition flex items-center gap-1.5" @click="resetTimer">
                  <i class="fa-solid fa-rotate-right text-[10px]"></i>
                  <span>Reiniciar</span>
                </button>
              </div>
            </div>

            <!-- Barra de progreso de tiempo en rojo sólido -->
            <div class="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-white/5">
              <div class="bg-red-600 h-1.5 transition-all duration-1000" :style="{ width: timerInitialSeconds > 0 ? `${(timerSeconds / timerInitialSeconds) * 100}%` : '0%' }"></div>
            </div>
          </div>

          <!-- LISTA DE EJERCICIOS (ANCHO MAX 6XL COMPACTO HORIZONTAL SIN OVERFLOW) -->
          <div class="space-y-3">
            <div
              v-for="(ex, exIdx) in getTracker(selectedMatriculaItem.id_matricula, selectedMatriculaItem.id_rutina)"
              :key="exIdx"
              class="routine-ex-card rounded-2xl border transition p-3.5 space-y-2.5"
              :class="ex.completado ? 'border-emerald-500/40 bg-emerald-950/20' : 'border-white/10 bg-slate-900/60'"
            >
              <!-- Fila Superior: Botón de estado del ejercicio y Botón de descanso -->
              <div class="flex items-center justify-between gap-2 border-b border-white/5 pb-2">
                <div class="flex items-center gap-3">
                  <!-- Botón interactivo de check/completado (Sin checkbox plano) -->
                  <button
                    type="button"
                    class="flex h-7 w-7 items-center justify-center rounded-lg transition active:scale-95"
                    :class="ex.completado ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30' : 'bg-slate-800 text-slate-400 border border-white/10 hover:border-emerald-500/50 hover:text-emerald-400'"
                    @click="ex.completado = !ex.completado; onToggleExerciseCompleted(ex)"
                    :title="ex.completado ? 'Ejercicio completado' : 'Marcar ejercicio como completado'"
                  >
                    <i :class="ex.completado ? 'fa-solid fa-check text-sm font-black' : 'fa-regular fa-circle text-xs'"></i>
                  </button>

                  <div class="flex items-center gap-2">
                    <i class="fa-solid fa-dumbbell text-red-500 text-sm"></i>
                    <span class="font-extrabold text-white text-base tracking-tight" :class="{ 'text-emerald-400': ex.completado }">
                      {{ ex.nombre_ejercicio }}
                    </span>
                    <span v-if="ex.completado" class="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-black text-emerald-400 border border-emerald-500/30">
                      <i class="fa-solid fa-check text-[9px] mr-1"></i> Completado
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  class="rest-badge-btn flex items-center gap-1.5 rounded-xl bg-red-600/10 border border-red-600/30 px-3 py-1 text-xs font-bold text-red-400 hover:bg-red-600 hover:text-white transition"
                  @click="setRestTimer(ex.descanso_segundos || 60)"
                >
                  <i class="fa-solid fa-stopwatch text-xs"></i>
                  <span>{{ ex.descanso_segundos || 60 }}s descanso</span>
                </button>
              </div>

              <p v-if="ex.notas" class="text-xs text-slate-400 italic flex items-center gap-1.5">
                <i class="fa-solid fa-circle-info text-red-500/70 text-[11px]"></i>
                <span>Notas: {{ ex.notas }}</span>
              </p>

              <!-- CONTROLES HORIZONTALES COMPACTOS (3 COLUMNAS SIN ROLLO ROJO Y NEGRO) -->
              <div class="grid gap-3 md:grid-cols-3">

                <!-- Control 1: Series Completadas -->
                <div class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <i class="fa-solid fa-layer-group text-red-500/80"></i>
                    <span>Series Completadas</span>
                  </span>
                  <div class="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      class="flex h-7 w-8 items-center justify-center rounded-lg bg-slate-900 text-white font-black hover:bg-slate-800 active:scale-95 transition border border-white/10"
                      @click="adjustSeries(ex, -1)"
                    >
                      <i class="fa-solid fa-minus text-xs"></i>
                    </button>
                    <span class="text-sm font-black text-red-400">
                      {{ ex.series_completadas || 0 }} <span class="text-xs text-slate-500 font-bold">/ {{ ex.series_meta }}</span>
                    </span>
                    <button
                      type="button"
                      class="flex h-7 w-8 items-center justify-center rounded-lg bg-red-600 text-white font-black hover:bg-red-500 active:scale-95 transition"
                      @click="adjustSeries(ex, 1)"
                    >
                      <i class="fa-solid fa-plus text-xs"></i>
                    </button>
                  </div>
                  <!-- Pills rápidos de series -->
                  <div class="flex flex-wrap gap-1 pt-1">
                    <button
                      v-for="s in Number(ex.series_meta || 3)"
                      :key="s"
                      type="button"
                      class="rounded px-2.5 py-0.5 text-[10px] font-bold transition"
                      :class="ex.series_completadas === s ? 'bg-red-600 text-white font-black' : 'bg-slate-900 text-slate-400 border border-white/5 hover:bg-slate-800'"
                      @click="ex.series_completadas = s; onSeriesChanged(ex)"
                    >
                      {{ s }}
                    </button>
                  </div>
                </div>

                <!-- Control 2: Peso Real Utilizado (kg) -->
                <div class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <i class="fa-solid fa-weight-hanging text-red-500/80"></i>
                      <span>Peso Real (kg)</span>
                    </span>
                    <span class="text-sm font-black text-red-400">{{ ex.peso_utilizado_kg || 0 }} kg</span>
                  </div>
                  <div class="flex flex-wrap gap-1 pt-1">
                    <button
                      type="button"
                      class="flex-1 rounded bg-slate-900 py-1 text-[10px] font-bold text-slate-300 border border-white/10 hover:bg-slate-800 transition"
                      @click="adjustWeight(ex, -2.5)"
                    >
                      -2.5
                    </button>
                    <button
                      v-if="ex.peso_sugerido_kg"
                      type="button"
                      class="sug-weight-btn flex-1 rounded bg-red-950/60 py-1 text-[10px] font-bold text-red-400 border border-red-600/40 hover:bg-red-600 hover:text-white transition flex items-center justify-center gap-1"
                      @click="setWeightToSuggested(ex)"
                    >
                      <i class="fa-solid fa-wand-magic-sparkles text-[9px]"></i>
                      <span>Sug: {{ ex.peso_sugerido_kg }}</span>
                    </button>
                    <button
                      type="button"
                      class="flex-1 rounded bg-slate-900 py-1 text-[10px] font-bold text-slate-300 border border-white/10 hover:bg-slate-800 transition"
                      @click="adjustWeight(ex, 2.5)"
                    >
                      +2.5
                    </button>
                    <button
                      type="button"
                      class="flex-1 rounded bg-red-600 py-1 text-[10px] font-bold text-white hover:bg-red-500 transition"
                      @click="adjustWeight(ex, 5)"
                    >
                      +5
                    </button>
                  </div>
                </div>

                <!-- Control 3: Repeticiones Logradas -->
                <div class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <i class="fa-solid fa-bullseye text-red-500/80"></i>
                    <span>Reps Logradas</span>
                  </span>
                  <input v-model="ex.repeticiones_logradas" class="field-input text-xs py-1 px-2 text-white bg-black border-white/10" placeholder="Ej. 10-12" />
                  <div class="flex flex-wrap gap-1 pt-0.5">
                    <button
                      type="button"
                      class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
                      @click="ex.repeticiones_logradas = '8'"
                    >
                      8
                    </button>
                    <button
                      type="button"
                      class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
                      @click="ex.repeticiones_logradas = '10'"
                    >
                      10
                    </button>
                    <button
                      type="button"
                      class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
                      @click="ex.repeticiones_logradas = '12'"
                    >
                      12
                    </button>
                    <button
                      type="button"
                      class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
                      @click="ex.repeticiones_logradas = 'Al fallo'"
                    >
                      Al fallo
                    </button>
                  </div>
                </div>

              </div>
            </div>
          </div>

          <!-- Observaciones y Botones de Acción (SIN GRADIENTES, ROJO Y NEGRO) -->
          <div class="space-y-2 pt-2 border-t border-white/10">
            <label class="block space-y-1">
              <span class="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <i class="fa-solid fa-clipboard-list text-red-500/80"></i>
                <span>Observaciones Generales de la Sesión</span>
              </span>
              <input v-model="observationsMap[selectedMatriculaItem.id_matricula]" class="field-input text-xs py-2 bg-black border-white/10" placeholder="Ej. El cliente logró subir peso manteniendo buena técnica." />
            </label>
            <div class="flex items-center justify-end gap-3 pt-1">
              <button class="flex items-center gap-1.5 rounded-2xl border border-white/10 bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition" @click="showExercisesModal = false">
                <i class="fa-solid fa-xmark text-xs"></i>
                <span>Cerrar</span>
              </button>
              <button class="flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30 disabled:opacity-50" :disabled="isSavingProgress" @click="submitSaveProgress">
                <i class="fa-solid fa-floppy-disk"></i>
                <span>{{ isSavingProgress ? 'Guardando…' : 'Guardar Progreso de Sesión' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- MODAL: Confirmar Desvinculación de Rutina -->
    <Teleport to="body">
      <div v-if="showConfirmModal && selectedMatriculaItem" class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md">
        <div class="w-full max-w-md rounded-3xl border border-white/15 bg-slate-950 p-6 shadow-2xl space-y-4 text-white">
          <h3 class="text-xl font-black text-white">¿Desvincular rutina?</h3>
          <p class="text-xs text-slate-300">
            Se quitará la rutina asignada para el servicio <strong>{{ serviceLabel(selectedMatriculaItem.servicio) }}</strong>.
          </p>
          <div class="flex justify-end gap-3 pt-3">
            <button class="rounded-xl bg-slate-900 border border-white/10 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800" @click="showConfirmModal = false">
              Cancelar
            </button>
            <button class="rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition disabled:opacity-50" :disabled="isUnassigning" @click="submitUnassign">
              {{ isUnassigning ? 'Desvinculando…' : 'Desvincular' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue';
import { useGymStore } from '../../application/stores/gymStore';

const gymStore = useGymStore();
const dni = ref('');
const clientData = ref(null);
const searching = ref(false);
const isSearching = computed(() => searching.value);
const feedback = ref('');
const feedbackTone = ref('success');
const assigningId = ref(0);
const markingId = ref(0);
const isSavingProgress = ref(false);
const isUnassigning = ref(false);

// Sugerencias de clientes y selección directa de rutinas.
const open = ref(false);
const activeIndex = ref(-1);
const selection = reactive({});

// Notificaciones emergentes.
const toast = reactive({ show: false, message: '', type: 'success' });
let toastTimeout = null;
const showToast = (message, type = 'success') => {
  toast.message = message;
  toast.type = type;
  toast.show = true;
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { toast.show = false; toastTimeout = null; }, 4000);
};
const setFeedback = (message, type = 'success') => {
  feedbackTone.value = type;
  feedback.value = message;
};

// Ventanas de asignación, edición de ejercicios y desvinculación.
const showAssignModal = ref(false);
const showExercisesModal = ref(false);
const showConfirmModal = ref(false);
const selectedMatriculaItem = ref(null);
const assignForm = reactive({ id_matricula: null, id_rutina: 0 });

// Datos temporales de la sesión de entrenamiento.
const trackerMap = reactive({});
const observationsMap = reactive({});

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);
const serviceLabel = (service) => ({
  fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile',
})[service] || service || 'Servicio';
const dayLabel = (day) => ({
  lunes: 'Lunes, Miércoles, Viernes', martes: 'Martes, Jueves',
  miercoles: 'Miércoles', jueves: 'Jueves', viernes: 'Viernes',
  sabado: 'Sábado', domingo: 'Domingo',
})[day] || day || 'Día';

const sortedProgress = (list) => [...(Array.isArray(list) ? list : [])].sort((a, b) => {
  const diff = new Date(b.fecha) - new Date(a.fecha);
  if (!Number.isNaN(diff) && diff !== 0) return diff;
  return Number(b.id_progreso || 0) - Number(a.id_progreso || 0);
});
const formatProgressDate = (value) => {
  if (!value) return 'Fecha no registrada';
  const text = String(value);
  const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(text) ? `${text}T00:00:00` : text);
  return Number.isNaN(date.getTime())
    ? text
    : date.toLocaleDateString('es-PE', { day: '2-digit', month: 'long', year: 'numeric' });
};
const isCompleted = (estado) => String(estado || '').toUpperCase() === 'REALIZADO';

// El servicio de clientes del entrenador normalmente ya entrega matrículas activas.
// Si el backend envía 'estado', se respeta para bloquear las inactivas.
const isEnrollmentActive = (item) => {
  const estado = String(item?.estado || '').trim().toUpperCase();
  return !estado || ['ACTIVA', 'ACTIVO', 'VIGENTE'].includes(estado);
};
const hasActiveMembership = computed(() =>
  (clientData.value?.matriculas || []).some(isEnrollmentActive));
const membershipLabel = computed(() =>
  hasActiveMembership.value ? 'Vigente' : 'Sin matrícula activa');

const routinesForService = (service) => routines.value.filter((routine) =>
  String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());
const hasCompatibleRoutines = (item) => routinesForService(item.servicio).length > 0;
const canAssign = (item) => isEnrollmentActive(item) && hasCompatibleRoutines(item);
const selectedRoutine = (item) => selection[item.id_matricula] ?? (item.id_rutina || 0);
const hasChange = (item) => {
  const chosen = Number(selection[item.id_matricula] || 0);
  return chosen > 0 && chosen !== Number(item.id_rutina || 0);
};

// Clientes con matrícula activa para mostrar sugerencias mientras escriben el DNI.
const activeClients = computed(() => {
  const seen = new Map();
  for (const row of overview.value.schedule_monitor || []) {
    const clientDni = String(row.cliente_dni || '').trim();
    if (clientDni && !seen.has(clientDni)) {
      seen.set(clientDni, { dni: clientDni, nombre: row.cliente_nombre || 'Cliente' });
    }
  }
  return [...seen.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
});
const suggestions = computed(() => {
  const prefix = dni.value.trim();
  return activeClients.value.filter((client) => client.dni.startsWith(prefix)).slice(0, 50);
});
const showSuggestions = computed(() =>
  open.value && (suggestions.value.length > 0 || dni.value.length > 0));

const onDniInput = () => {
  dni.value = dni.value.replace(/\D/g, '').slice(0, 8);
  feedback.value = '';
  open.value = true;
  activeIndex.value = -1;
};
const openSuggestions = () => { open.value = true; activeIndex.value = -1; };
const moveActive = (step) => {
  open.value = true;
  const total = suggestions.value.length;
  if (!total) return;
  activeIndex.value = activeIndex.value < 0
    ? (step > 0 ? 0 : total - 1)
    : (activeIndex.value + step + total) % total;
  nextTick(() => document.getElementById(`dni-option-${activeIndex.value}`)?.scrollIntoView({ block: 'nearest' }));
};
const onEnter = (event) => {
  if (showSuggestions.value && activeIndex.value >= 0 && suggestions.value[activeIndex.value]) {
    event.preventDefault();
    pickClient(suggestions.value[activeIndex.value].dni);
  }
};
const pickClient = (value) => { dni.value = value; open.value = false; searchClient(); };

const selectedAssignMatricula = computed(() =>
  (clientData.value?.matriculas || []).find((m) =>
    Number(m.id_matricula) === Number(assignForm.id_matricula)));
const availableRoutinesForSelectedMatricula = computed(() =>
  selectedAssignMatricula.value
    ? routinesForService(selectedAssignMatricula.value.servicio)
    : []);
const canSubmitAssign = computed(() => {
  const mat = selectedAssignMatricula.value;
  return Boolean(mat && isEnrollmentActive(mat)
    && availableRoutinesForSelectedMatricula.value.some((r) =>
      Number(r.id_rutina) === Number(assignForm.id_rutina)));
});

const getRoutineExercises = (idRutina) => {
  const routine = routines.value.find((r) => Number(r.id_rutina) === Number(idRutina));
  return Array.isArray(routine?.ejercicios) ? routine.ejercicios : [];
};
const getTracker = (idMatricula, idRutina) => {
  const key = `${idMatricula}_${idRutina}`;
  if (!trackerMap[key]) {
    trackerMap[key] = getRoutineExercises(idRutina).map((ex, i) => ({
      id_ejercicio: ex.id_ejercicio || i + 1,
      nombre_ejercicio: ex.nombre_ejercicio || `Ejercicio #${i + 1}`,
      series_meta: Number(ex.series || 3),
      series_completadas: 0,
      repeticiones_logradas: ex.repeticiones || '10-12',
      peso_sugerido_kg: ex.peso_sugerido_kg ?? null,
      peso_utilizado_kg: ex.peso_sugerido_kg ?? null,
      descanso_segundos: Number(ex.descanso_segundos || 60),
      notas: ex.notas || '',
      completado: false,
      observaciones: '',
    }));
  }
  return trackerMap[key];
};
const onSeriesChanged = (ex) => {
  ex.completado = Number(ex.series_completadas || 0) >= Number(ex.series_meta || 3);
};
const adjustSeries = (ex, delta) => {
  const meta = Number(ex.series_meta || 3);
  ex.series_completadas = Math.max(0, Math.min(meta, Number(ex.series_completadas || 0) + delta));
  onSeriesChanged(ex);
};
const adjustWeight = (ex, delta) => {
  const current = Number(ex.peso_utilizado_kg ?? ex.peso_sugerido_kg ?? 0);
  ex.peso_utilizado_kg = Math.max(0, current + delta);
};
const setWeightToSuggested = (ex) => {
  if (ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== undefined) {
    ex.peso_utilizado_kg = Number(ex.peso_sugerido_kg);
  }
};
const onToggleExerciseCompleted = (ex) => {
  ex.series_completadas = ex.completado ? Number(ex.series_meta || 3) : 0;
};

// Temporizador de descansos; continúa visible al llegar a cero.
const timerSeconds = ref(0);
const timerInitialSeconds = ref(60);
const timerActive = ref(false);
const timerFinished = ref(false);
let timerInterval = null;
const pauseTimer = () => {
  timerActive.value = false;
  if (timerInterval !== null) { clearInterval(timerInterval); timerInterval = null; }
};
const resetTimer = () => {
  pauseTimer();
  timerSeconds.value = 0;
  timerFinished.value = false;
};
const startTimer = () => {
  if (timerSeconds.value <= 0) return;
  pauseTimer();
  timerFinished.value = false;
  timerActive.value = true;
  timerInterval = setInterval(() => {
    if (timerSeconds.value > 0) timerSeconds.value -= 1;
    if (timerSeconds.value <= 0) {
      pauseTimer();
      timerFinished.value = true;
    }
  }, 1000);
};
const setRestTimer = (seconds) => {
  const duration = Math.max(1, Math.floor(Number(seconds) || 60));
  resetTimer();
  timerInitialSeconds.value = duration;
  timerSeconds.value = duration;
  startTimer();
};
const formatTimer = (totalSec) => {
  const value = Math.max(0, Number(totalSec) || 0);
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
};

const searchClient = async () => {
  if (searching.value) return;
  open.value = false;
  const query = dni.value.trim();
  if (!/^\d{8}$/.test(query)) {
    setFeedback('Ingresa un DNI válido de 8 dígitos o selecciona una sugerencia.', 'error');
    return;
  }
  searching.value = true;
  feedback.value = '';
  clientData.value = null;
  showAssignModal.value = false;
  showExercisesModal.value = false;
  showConfirmModal.value = false;
  try {
    const [, client] = await Promise.all([
      gymStore.fetchTrainerOverview(),
      gymStore.fetchTrainerClientRoutines(query),
    ]);
    if (!client?.cliente) throw new Error('No se encontró información del cliente.');
    clientData.value = client;
    Object.keys(selection).forEach((key) => { delete selection[key]; });
    showToast(`Cliente ${client.cliente.nombre} cargado exitosamente.`);
  } catch (error) {
    clientData.value = null;
    const message = error instanceof Error ? error.message : 'No se pudo buscar el cliente.';
    setFeedback(message, 'error');
    showToast(message, 'error');
  } finally {
    searching.value = false;
  }
};

const reloadClient = async () => {
  if (!dni.value.trim()) return;
  clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value.trim());
};

// Asignación directa (rama karinaTp3_AsignacionRutina).
const assignRoutine = async (item) => {
  const idRutina = Number(selection[item.id_matricula] || 0);
  if (!idRutina || assigningId.value) return;
  if (!isEnrollmentActive(item)) {
    setFeedback('Solo se puede asignar una rutina a una matrícula activa.', 'error');
    return;
  }
  const routine = routinesForService(item.servicio).find((r) => Number(r.id_rutina) === idRutina);
  if (!routine) {
    setFeedback(`Esa rutina no corresponde al servicio ${serviceLabel(item.servicio)}.`, 'error');
    return;
  }
  assigningId.value = item.id_matricula;
  try {
    feedback.value = '';
    await gymStore.assignTrainerRoutine(item.id_matricula, idRutina);
    delete selection[item.id_matricula];
    await reloadClient();
    const message = `Rutina «${routine.nombre_rutina}» asignada a ${serviceLabel(item.servicio)} (${dayLabel(item.dia)} ${item.hora_inicio} - ${item.hora_fin}).`;
    setFeedback(message);
    showToast('Rutina asignada exitosamente.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo asignar la rutina.';
    setFeedback(message, 'error');
    showToast(message, 'error');
    await reloadClient().catch(() => {});
  } finally {
    assigningId.value = 0;
  }
};

// Registro rápido de rutina realizada: opción de la rama de asignación.
const markDone = async (item) => {
  if (!item.id_rutina || !isEnrollmentActive(item) || markingId.value) return;
  markingId.value = item.id_matricula;
  try {
    await gymStore.markTrainerRoutineProgress(item.id_matricula, {
      estado: 'REALIZADO',
      observacion: 'Rutina marcada como realizada por el entrenador.',
      ejercicios_detalle: [],
    });
    await reloadClient();
    setFeedback('Rutina marcada como realizada.');
    showToast('Rutina completada correctamente.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo registrar la rutina como realizada.';
    setFeedback(message, 'error');
    showToast(message, 'error');
  } finally {
    markingId.value = 0;
  }
};

// Asignación mediante modal (rama develop), con validación de compatibilidad.
const openAssignModal = () => {
  const first = (clientData.value?.matriculas || []).find(isEnrollmentActive);
  if (!first) {
    setFeedback('El cliente debe tener una matrícula activa para asignar rutinas.', 'error');
    return;
  }
  assignForm.id_matricula = first.id_matricula;
  assignForm.id_rutina = 0;
  showAssignModal.value = true;
};
const submitAssignRoutine = async () => {
  if (!canSubmitAssign.value || assigningId.value) return;
  assigningId.value = assignForm.id_matricula;
  try {
    await gymStore.assignTrainerRoutine(assignForm.id_matricula, Number(assignForm.id_rutina));
    delete selection[assignForm.id_matricula];
    await reloadClient();
    showAssignModal.value = false;
    setFeedback('Rutina personalizada asignada exitosamente.');
    showToast('Rutina personalizada asignada exitosamente.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo asignar la rutina.';
    setFeedback(message, 'error');
    showToast(message, 'error');
    await reloadClient().catch(() => {});
  } finally {
    assigningId.value = 0;
  }
};

const openExercisesModal = (item) => {
  selectedMatriculaItem.value = item;
  getTracker(item.id_matricula, item.id_rutina);
  showExercisesModal.value = true;
};
const submitSaveProgress = async () => {
  const item = selectedMatriculaItem.value;
  if (!item || isSavingProgress.value) return;
  isSavingProgress.value = true;
  try {
    const trackerExs = getTracker(item.id_matricula, item.id_rutina);
    const ejercicios_detalle = trackerExs.map((ex) => ({
      id_ejercicio: ex.id_ejercicio,
      nombre_ejercicio: ex.nombre_ejercicio,
      completado: Boolean(ex.completado),
      series_completadas: Number(ex.series_completadas || 0),
      repeticiones_logradas: String(ex.repeticiones_logradas || ''),
      peso_utilizado_kg: ex.peso_utilizado_kg !== null && ex.peso_utilizado_kg !== ''
        ? Number(ex.peso_utilizado_kg) : null,
      observaciones: String(ex.observaciones || ''),
    }));
    const observacion = observationsMap[item.id_matricula] || 'Sesión de entrenamiento realizada';
    await gymStore.markTrainerRoutineProgress(item.id_matricula, {
      estado: 'REALIZADO',
      observacion,
      ejercicios_detalle,
    });
    await reloadClient();
    delete trackerMap[`${item.id_matricula}_${item.id_rutina}`];
    delete observationsMap[item.id_matricula];
    showExercisesModal.value = false;
    setFeedback('Progreso de rutina registrado en el sistema.');
    showToast('Progreso de rutina registrado en el sistema.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo registrar el progreso.';
    setFeedback(message, 'error');
    showToast(message, 'error');
  } finally {
    isSavingProgress.value = false;
  }
};

const confirmUnassign = (item) => {
  selectedMatriculaItem.value = item;
  showConfirmModal.value = true;
};
const submitUnassign = async () => {
  const item = selectedMatriculaItem.value;
  if (!item || isUnassigning.value) return;
  isUnassigning.value = true;
  try {
    // Mantiene la interfaz que ya usa el proyecto para quitar la asignación.
    await gymStore.assignTrainerRoutine(item.id_matricula, 0);
    delete selection[item.id_matricula];
    await reloadClient();
    showConfirmModal.value = false;
    setFeedback('Rutina desvinculada del servicio.');
    showToast('Rutina desvinculada del servicio.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo desvincular la rutina.';
    setFeedback(message, 'error');
    showToast(message, 'error');
  } finally {
    isUnassigning.value = false;
  }
};

onMounted(() => { gymStore.fetchTrainerOverview().catch(() => {}); });
onUnmounted(() => {
  pauseTimer();
  if (toastTimeout) clearTimeout(toastTimeout);
});
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid var(--app-border, rgba(255, 255, 255, 0.1));
  border-radius: 1rem;
  background: var(--app-input, rgba(2, 6, 23, 0.9));
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
