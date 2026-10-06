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
        <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="searchClient">
          <div class="relative min-w-64">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
            <input v-model="dni" class="field-input search-input text-xs" placeholder="Ingresa DNI del cliente" required />
          </div>
          <button class="flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20">
            <i class="fa-solid fa-magnifying-glass"></i>
            <span>Buscar Cliente</span>
          </button>
        </form>
      </div>
    </section>

    <!-- Visual Rest Timer (Flotante en Vista Principal - ROJO Y NEGRO) -->
    <section v-if="timerActive || timerSeconds > 0" class="rounded-2xl border border-red-500/40 bg-black/90 p-4 shadow-xl transition-all">
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
          <button v-if="!timerActive" class="rounded-xl bg-red-600 px-4 py-2 font-black text-white text-xs hover:bg-red-500 transition flex items-center gap-1.5" @click="startTimer">
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
            class="flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20"
            @click="openAssignModal"
          >
            <i class="fa-solid fa-plus text-xs"></i>
            <span>Asignar rutina personalizada</span>
          </button>
        </div>
      </div>

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

          <!-- Historial de avance reciente -->
          <div>
            <p class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-clock-rotate-left text-xs text-red-500"></i>
              Avance reciente registrado
            </p>
            <div v-if="(item.progreso || []).length" class="mt-2 space-y-2 max-h-36 overflow-y-auto pr-1">
              <div v-for="progress in item.progreso || []" :key="progress.id_progreso" class="rounded-xl bg-black/80 p-3 text-xs space-y-1 border border-white/5">
                <div class="flex items-center justify-between text-slate-300">
                  <span class="font-bold text-red-400">{{ progress.fecha }}</span>
                  <span class="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">{{ progress.estado }}</span>
                </div>
                <p v-if="progress.observacion" class="text-slate-400">{{ progress.observacion }}</p>
                <div v-if="(progress.ejercicios_detalle || []).length" class="mt-1 space-y-1 border-t border-white/5 pt-1">
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
            <p v-else class="mt-2 text-xs text-slate-500">Sin checks de avance registrados aún.</p>
          </div>
        </article>
      </div>

      <p v-if="!clientData.matriculas.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-slate-400">
        El cliente no tiene matrículas activas.
      </p>
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
              <select v-model="assignForm.id_matricula" class="field-input text-sm cursor-pointer font-medium">
                <option v-for="mat in clientData?.matriculas || []" :key="mat.id_matricula" :value="mat.id_matricula">
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
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button class="rounded-xl bg-slate-900 border border-white/10 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition" @click="showAssignModal = false">
              Cancelar
            </button>
            <button
              class="flex items-center gap-2 rounded-xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30 disabled:bg-slate-800 disabled:text-slate-500 disabled:border disabled:border-white/10 disabled:shadow-none disabled:cursor-not-allowed"
              :disabled="!assignForm.id_matricula || !assignForm.id_rutina"
              @click="submitAssignRoutine"
            >
              <i class="fa-solid fa-check"></i>
              <span>Guardar rutina</span>
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
          <div v-if="timerActive || timerSeconds > 0" class="rounded-2xl border border-red-500/40 bg-black p-3 shadow-xl space-y-2">
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
                <button v-if="!timerActive" class="rounded-xl bg-red-600 px-3.5 py-1.5 font-black text-white text-xs hover:bg-red-500 transition flex items-center gap-1.5" @click="startTimer">
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
                      @click="ex.series_completadas = s"
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
              <button class="flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30" @click="submitSaveProgress">
                <i class="fa-solid fa-floppy-disk"></i>
                <span>Guardar Progreso de Sesión</span>
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
            <button class="rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition" @click="submitUnassign">
              Desvincular
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onUnmounted } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const dni = ref('');
const clientData = ref(null);

// POP-UP TOAST SYSTEM
const toast = reactive({
  show: false,
  message: '',
  type: 'success',
  timer: null,
});

const showToast = (message, type = 'success') => {
  toast.message = message;
  toast.type = type;
  toast.show = true;
  if (toast.timer) clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    toast.show = false;
  }, 4000);
};

// Modales state
const showAssignModal = ref(false);
const showExercisesModal = ref(false);
const showConfirmModal = ref(false);
const selectedMatriculaItem = ref(null);

const assignForm = reactive({
  id_matricula: null,
  id_rutina: 0,
});

// Tracker maps
const trackerMap = reactive({});
const observationsMap = reactive({});

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const dayLabel = (day) => ({ lunes: 'Lunes, Miércoles, Viernes', martes: 'Martes, Jueves', miercoles: 'Miércoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sábado', domingo: 'Domingo' })[day] || day || 'Día';

const hasActiveMembership = computed(() => {
  const m = clientData.value?.matriculas || [];
  return m.length > 0;
});

const membershipLabel = computed(() => {
  return hasActiveMembership.value ? 'Vigente' : 'Sin membresía activa';
});

const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const availableRoutinesForSelectedMatricula = computed(() => {
  if (!assignForm.id_matricula) return routines.value;
  const mat = clientData.value?.matriculas.find((m) => Number(m.id_matricula) === Number(assignForm.id_matricula));
  return mat ? routinesForService(mat.servicio) : routines.value;
});

const getRoutineExercises = (idRutina) => {
  const routine = routines.value.find((r) => Number(r.id_rutina) === Number(idRutina));
  return routine && Array.isArray(routine.ejercicios) ? routine.ejercicios : [];
};

const getTracker = (idMatricula, idRutina) => {
  const key = `${idMatricula}_${idRutina}`;
  if (!trackerMap[key]) {
    const rawExs = getRoutineExercises(idRutina);
    trackerMap[key] = rawExs.map((ex, i) => ({
      id_ejercicio: ex.id_ejercicio || i + 1,
      nombre_ejercicio: ex.nombre_ejercicio || `Ejercicio #${i + 1}`,
      series_meta: ex.series || 3,
      series_completadas: ex.series || 3,
      repeticiones_logradas: ex.repeticiones || '10-12',
      peso_sugerido_kg: ex.peso_sugerido_kg || null,
      peso_utilizado_kg: ex.peso_sugerido_kg || null,
      descanso_segundos: ex.descanso_segundos || 60,
      notas: ex.notas || '',
      completado: true,
      observaciones: '',
    }));
  }
  return trackerMap[key];
};

// Métodos de interacción táctil/sin teclado
const adjustSeries = (ex, delta) => {
  const meta = Number(ex.series_meta || 3);
  const current = Number(ex.series_completadas || 0);
  ex.series_completadas = Math.max(0, Math.min(meta, current + delta));
  if (ex.series_completadas === meta) {
    ex.completado = true;
  }
};

const adjustWeight = (ex, delta) => {
  const current = Number(ex.peso_utilizado_kg || ex.peso_sugerido_kg || 0);
  ex.peso_utilizado_kg = Math.max(0, current + delta);
};

const setWeightToSuggested = (ex) => {
  if (ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== undefined) {
    ex.peso_utilizado_kg = Number(ex.peso_sugerido_kg);
  }
};

const onToggleExerciseCompleted = (ex) => {
  if (ex.completado) {
    ex.series_completadas = Number(ex.series_meta || 3);
  }
};

// Temporizador visual
const timerSeconds = ref(0);
const timerInitialSeconds = ref(60);
const timerActive = ref(false);
let timerInterval = null;

const setRestTimer = (seconds) => {
  resetTimer();
  timerInitialSeconds.value = seconds || 60;
  timerSeconds.value = seconds || 60;
  startTimer();
};

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval);
  if (timerSeconds.value <= 0) return;
  timerActive.value = true;
  timerInterval = setInterval(() => {
    if (timerSeconds.value > 0) {
      timerSeconds.value--;
    } else {
      pauseTimer();
    }
  }, 1000);
};

const pauseTimer = () => {
  timerActive.value = false;
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
};

const resetTimer = () => {
  pauseTimer();
  timerSeconds.value = 0;
};

const formatTimer = (totalSec) => {
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

onUnmounted(() => {
  pauseTimer();
});

const isSearching = ref(false);

const searchClient = async () => {
  if (!dni.value.trim()) return;
  try {
    isSearching.value = true;
    clientData.value = null;
    const [, client] = await Promise.all([
      gymStore.fetchTrainerOverview(),
      gymStore.fetchTrainerClientRoutines(dni.value),
    ]);
    clientData.value = client;
    showToast(`Cliente ${clientData.value.cliente.nombre} cargado exitosamente.`, 'success');
  } catch (error) {
    clientData.value = null;
    showToast(error instanceof Error ? error.message : 'No se pudo buscar el cliente.', 'error');
  } finally {
    isSearching.value = false;
  }
};

const reloadClient = async () => {
  if (!dni.value.trim()) return;
  clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
};

const openAssignModal = () => {
  if (clientData.value?.matriculas?.length) {
    assignForm.id_matricula = clientData.value.matriculas[0].id_matricula;
  }
  assignForm.id_rutina = 0;
  showAssignModal.value = true;
};

const submitAssignRoutine = async () => {
  if (!assignForm.id_matricula || !assignForm.id_rutina) return;
  try {
    await gymStore.assignTrainerRoutine(assignForm.id_matricula, assignForm.id_rutina);
    await reloadClient();
    showAssignModal.value = false;
    showToast('Rutina personalizada asignada exitosamente.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo asignar la rutina.', 'error');
  }
};

const openExercisesModal = (item) => {
  selectedMatriculaItem.value = item;
  showExercisesModal.value = true;
};

const submitSaveProgress = async () => {
  if (!selectedMatriculaItem.value) return;
  const item = selectedMatriculaItem.value;
  try {
    const trackerExs = getTracker(item.id_matricula, item.id_rutina);
    const ejercicios_detalle = trackerExs.map((ex) => ({
      id_ejercicio: ex.id_ejercicio,
      nombre_ejercicio: ex.nombre_ejercicio,
      completado: Boolean(ex.completado),
      series_completadas: Number(ex.series_completadas || 0),
      repeticiones_logradas: String(ex.repeticiones_logradas || ''),
      peso_utilizado_kg: ex.peso_utilizado_kg !== null && ex.peso_utilizado_kg !== '' ? Number(ex.peso_utilizado_kg) : null,
      observaciones: String(ex.observaciones || ''),
    }));

    const observacion = observationsMap[item.id_matricula] || 'Sesión de entrenamiento realizada';

    await gymStore.markTrainerRoutineProgress(item.id_matricula, {
      estado: 'REALIZADO',
      observacion,
      ejercicios_detalle,
    });

    await reloadClient();
    showExercisesModal.value = false;
    showToast('Progreso de rutina registrado en el sistema.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo registrar el progreso.', 'error');
  }
};

const confirmUnassign = (item) => {
  selectedMatriculaItem.value = item;
  showConfirmModal.value = true;
};

const submitUnassign = async () => {
  if (!selectedMatriculaItem.value) return;
  try {
    await gymStore.assignTrainerRoutine(selectedMatriculaItem.value.id_matricula, 0);
    await reloadClient();
    showConfirmModal.value = false;
    showToast('Rutina desvinculada del servicio.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo desvincular la rutina.', 'error');
  }
};
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
