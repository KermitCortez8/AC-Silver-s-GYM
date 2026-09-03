<template>
  <div class="space-y-6 pb-12">
    <!-- Hero Header Principal -->
    <section class="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/90 via-slate-950/95 to-slate-900/90 p-6 shadow-2xl backdrop-blur-xl sm:p-8">
      <div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-red-600/10 blur-3xl pointer-events-none"></div>

      <div class="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div class="max-w-2xl">
          <div class="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3.5 py-1 text-xs font-black uppercase tracking-wider text-cyan-300">
            <Sparkles class="h-3.5 w-3.5" />
            Matrícula de Clases
          </div>
          <h1 class="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">
            Registro de Horario del Cliente
          </h1>
          <p class="mt-2 text-sm leading-relaxed text-slate-300 sm:text-base">
            Compara el <strong class="text-cyan-300">Horario Completo del Gimnasio</strong> con tu <strong class="text-emerald-300">Horario Propio</strong>. Selecciona el ejercicio que más te guste, verifica cupos y horas, y matricúlate con 1 solo clic.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-bold text-slate-200 transition hover:bg-white/10 hover:text-white disabled:cursor-wait disabled:opacity-60"
            :disabled="isRefreshing"
            @click="refreshAll({ announce: true })"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': isRefreshing }" />
            {{ isRefreshing ? 'Actualizando…' : 'Actualizar' }}
          </button>
        </div>
      </div>

      <!-- Resumen de los 2 Horarios -->
      <div class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-2xl border border-white/10 bg-slate-950/60 p-3.5 sm:p-4">
          <p class="text-xs uppercase tracking-wider text-slate-400">Total Clases Gym</p>
          <p class="mt-1 text-2xl font-black text-white">{{ schedules.length }}</p>
          <span class="text-[11px] text-cyan-400">Horario completo</span>
        </div>
        <div class="rounded-2xl border border-white/10 bg-slate-950/60 p-3.5 sm:p-4">
          <p class="text-xs uppercase tracking-wider text-slate-400">Cupos Libres Gym</p>
          <p class="mt-1 text-2xl font-black text-emerald-400">{{ totalAvailableSlots }}</p>
          <span class="text-[11px] text-slate-400">Disponibles ahora</span>
        </div>
        <div class="rounded-2xl border border-white/10 bg-slate-950/60 p-3.5 sm:p-4">
          <p class="text-xs uppercase tracking-wider text-slate-400">Mis Clases</p>
          <p class="mt-1 text-2xl font-black text-cyan-300">{{ visibleEnrollments.length }}</p>
          <span class="text-[11px]" :class="visibleEnrollments.length ? 'text-cyan-400' : 'text-amber-400'">
            {{ visibleEnrollments.length ? 'Matriculadas' : 'Horario vacío' }}
          </span>
        </div>
        <div class="rounded-2xl border border-white/10 bg-slate-950/60 p-3.5 sm:p-4">
          <p class="text-xs uppercase tracking-wider text-slate-400">Cliente Activo</p>
          <p class="mt-1 truncate text-base font-black text-white sm:text-lg">
            {{ currentClient?.name || 'Cliente' }}
          </p>
          <span class="text-[11px] text-slate-400 truncate block">
            {{ currentClient?.dni ? `DNI: ${currentClient.dni}` : 'Sesión personal' }}
          </span>
        </div>
      </div>
    </section>

    <!-- Búsqueda de cliente por DNI para Administradores -->
    <section v-if="isAdminUser" class="rounded-3xl border border-amber-400/20 bg-amber-400/5 p-5 backdrop-blur-xl">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end">
        <form class="flex flex-1 flex-col gap-3 sm:flex-row sm:items-end" @submit.prevent="loadAdminClient">
          <label class="flex-1 space-y-1.5">
            <span class="text-xs font-bold uppercase tracking-wider text-amber-200">Panel Admin: DNI del cliente a matricular</span>
            <input
              v-model="dniSearch"
              inputmode="numeric"
              autocomplete="off"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition focus:border-amber-400"
              placeholder="Ingresa el DNI del cliente..."
            />
          </label>
          <button
            type="submit"
            class="inline-flex items-center justify-center gap-2 rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-amber-300 disabled:cursor-wait disabled:opacity-60"
            :disabled="isSearchingClient"
          >
            <Search class="h-4 w-4" />
            {{ isSearchingClient ? 'Buscando…' : 'Buscar cliente' }}
          </button>
        </form>

        <div v-if="selectedClient" class="rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
          Gestionando a: <strong class="text-white">{{ selectedClient.name }}</strong> (DNI {{ selectedClient.dni }})
        </div>
      </div>
    </section>

    <!-- Notificación / Feedback Flotante -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="feedback"
        class="flex items-center justify-between gap-3 rounded-2xl border p-4 text-sm font-semibold shadow-xl"
        :class="feedbackTone === 'error'
          ? 'border-rose-500/30 bg-rose-500/15 text-rose-100'
          : 'border-emerald-500/30 bg-emerald-500/15 text-emerald-100'"
        role="status"
        aria-live="polite"
      >
        <div class="flex items-center gap-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-full" :class="feedbackTone === 'error' ? 'bg-rose-500/20' : 'bg-emerald-500/20'">
            <CheckCircle2 v-if="feedbackTone === 'success'" class="h-4 w-4 text-emerald-300" />
            <AlertCircle v-else class="h-4 w-4 text-rose-300" />
          </span>
          <p>{{ feedback }}</p>
        </div>
        <button type="button" class="text-xs opacity-70 hover:opacity-100" @click="feedback = ''">
          <X class="h-4 w-4" />
        </button>
      </div>
    </Transition>

    <!-- Flujo simple en 3 pasos -->
    <div class="grid gap-3 sm:grid-cols-3">
      <div class="flex items-center gap-3 rounded-2xl border border-white/5 bg-slate-900/40 p-3.5 backdrop-blur-sm">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 font-black text-cyan-400">1</div>
        <div class="min-w-0">
          <p class="text-xs font-black uppercase text-white">Explora el Gym</p>
          <p class="text-xs text-slate-400 truncate">Revisa el horario completo</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border border-white/5 bg-slate-900/40 p-3.5 backdrop-blur-sm">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 font-black text-cyan-400">2</div>
        <div class="min-w-0">
          <p class="text-xs font-black uppercase text-white">Elige tu Ejercicio</p>
          <p class="text-xs text-slate-400 truncate">Consulta cupos libres y horas</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border border-white/5 bg-slate-900/40 p-3.5 backdrop-blur-sm">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-400/10 font-black text-emerald-400">3</div>
        <div class="min-w-0">
          <p class="text-xs font-black uppercase text-white">Matricúlate</p>
          <p class="text-xs text-slate-400 truncate">Se añadirá a tu horario personal</p>
        </div>
      </div>
    </div>

    <!-- Barra de Selección de Vista de los 2 Horarios -->
    <section class="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/60 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold uppercase tracking-wider text-slate-400 pl-2">Modo de Vista:</span>
        <div class="inline-flex rounded-xl border border-white/10 bg-slate-900/80 p-1">
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition"
            :class="viewMode === 'split' ? 'bg-cyan-400 text-slate-950 shadow-md font-black' : 'text-slate-300 hover:text-white'"
            @click="viewMode = 'split'"
          >
            <Columns2 class="h-3.5 w-3.5" />
            2 Horarios en Paralelo
          </button>
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition"
            :class="viewMode === 'full' ? 'bg-cyan-400 text-slate-950 shadow-md font-black' : 'text-slate-300 hover:text-white'"
            @click="viewMode = 'full'"
          >
            <Calendar class="h-3.5 w-3.5" />
            Solo Horario Completo Gym
          </button>
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition"
            :class="viewMode === 'own' ? 'bg-cyan-400 text-slate-950 shadow-md font-black' : 'text-slate-300 hover:text-white'"
            @click="viewMode = 'own'"
          >
            <Clock class="h-3.5 w-3.5" />
            Solo Mi Horario ({{ visibleEnrollments.length }})
          </button>
        </div>
      </div>

      <!-- Indicador visual de estado del horario propio -->
      <div class="flex items-center gap-2 pl-2 sm:pl-0">
        <span class="inline-block h-2.5 w-2.5 rounded-full" :class="visibleEnrollments.length ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'"></span>
        <span class="text-xs font-medium text-slate-300">
          Tu horario personal:
          <strong :class="visibleEnrollments.length ? 'text-emerald-300 font-bold' : 'text-amber-300 font-bold'">
            {{ visibleEnrollments.length ? `${visibleEnrollments.length} clase(s) agregada(s)` : 'Vacío (Sin clases aún)' }}
          </strong>
        </span>
      </div>
    </section>

    <!-- Panel de Clase Seleccionada para Matrícula Rápida (Destacado) -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform -translate-y-4 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <article
        v-if="selectedSchedule"
        class="relative overflow-hidden rounded-3xl border-2 border-cyan-400/50 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 p-6 shadow-2xl shadow-cyan-950/20"
      >
        <div class="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded-full bg-cyan-400/20 px-3 py-1 text-xs font-black uppercase tracking-wider text-cyan-300">
                Clase Seleccionada
              </span>
              <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200">
                {{ serviceLabel(selectedSchedule.servicio) }}
              </span>
              <span
                v-if="selectedIsEnrolled"
                class="rounded-full border border-emerald-400/40 bg-emerald-400/15 px-3 py-1 text-xs font-bold text-emerald-300 inline-flex items-center gap-1"
              >
                <Check class="h-3 w-3" /> Ya en tu horario
              </span>
            </div>

            <h3 class="text-2xl font-black text-white sm:text-3xl">
              {{ exerciseName(selectedSchedule) }}
            </h3>

            <p v-if="selectedSchedule.zonas_musculares" class="text-sm text-slate-300 flex items-center gap-1.5">
              <Dumbbell class="h-4 w-4 text-cyan-400" />
              <span>Zonas musculares: <strong>{{ selectedSchedule.zonas_musculares }}</strong></span>
            </p>
          </div>

          <!-- Métricas de la clase seleccionada: Horas y Cupos -->
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div class="rounded-2xl border border-white/10 bg-white/5 p-3.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Día</span>
              <p class="mt-1 font-black text-white capitalize">{{ dayLabel(selectedSchedule.dia) }}</p>
            </div>
            <div class="rounded-2xl border border-white/10 bg-white/5 p-3.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Horas</span>
              <p class="mt-1 whitespace-nowrap font-black text-cyan-300">{{ formatScheduleHours(selectedSchedule) }}</p>
            </div>
            <div class="col-span-2 sm:col-span-1 rounded-2xl border border-white/10 bg-white/5 p-3.5">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Cupos</span>
              <p class="mt-1 whitespace-nowrap font-black" :class="slotsBadgeInfo(selectedSchedule).tone === 'danger' ? 'text-rose-400' : 'text-emerald-300'">
                {{ availableSlots(selectedSchedule) }} libres de {{ selectedSchedule.cupos || 0 }}
              </p>
            </div>
          </div>

          <!-- Botón de Matrícula -->
          <div class="flex flex-col gap-2">
            <button
              type="button"
              class="inline-flex items-center justify-center gap-2 rounded-2xl px-6 py-4 text-base font-black shadow-lg transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              :class="canEnrollSelected
                ? 'bg-gradient-to-r from-cyan-400 to-teal-400 text-slate-950 hover:brightness-110 shadow-cyan-500/20'
                : selectedIsEnrolled
                  ? 'border border-emerald-400/40 bg-emerald-500/20 text-emerald-100'
                  : 'bg-slate-800 text-slate-400'"
              :disabled="!canEnrollSelected || Boolean(actionBusy)"
              @click="enrollSelected"
            >
              <CheckCircle2 v-if="selectedIsEnrolled" class="h-5 w-5 text-emerald-400" />
              <Sparkles v-else class="h-5 w-5" />
              {{ enrollButtonLabel }}
            </button>
            <button
              type="button"
              class="text-center text-xs text-slate-400 hover:text-white"
              @click="selectedScheduleId = ''"
            >
              Cerrar selección
            </button>
          </div>
        </div>
      </article>
    </Transition>

    <!-- Explorador Rápido de Clases (Filtros por Día y Servicio) -->
    <section class="rounded-3xl border border-white/10 bg-slate-950/40 p-5 backdrop-blur-xl">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 class="text-base font-black text-white">Explorador Rápido de Clases</h3>
          <p class="text-xs text-slate-400">Filtra por día o tipo de ejercicio para ver cupos, horas y matricularte al instante.</p>
        </div>

        <!-- Buscador -->
        <div class="relative min-w-[240px]">
          <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            v-model="searchQuery"
            class="w-full rounded-2xl border border-white/10 bg-slate-900/80 pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 outline-none transition focus:border-cyan-400"
            placeholder="Buscar por ejercicio o rutina..."
          />
        </div>
      </div>

      <!-- Chips de Filtros de Días -->
      <div class="mt-4 flex flex-wrap gap-1.5">
        <button
          v-for="day in dayFilterOptions"
          :key="day.value"
          type="button"
          class="rounded-xl px-3 py-1.5 text-xs font-bold transition"
          :class="selectedDayFilter === day.value
            ? 'bg-cyan-400 text-slate-950 font-black shadow-md shadow-cyan-950/40'
            : 'border border-white/5 bg-slate-900/80 text-slate-300 hover:bg-white/10'"
          @click="selectedDayFilter = day.value"
        >
          {{ day.label }}
        </button>
      </div>

      <!-- Chips de Servicios -->
      <div class="mt-2 flex flex-wrap gap-1.5">
        <button
          v-for="srv in serviceFilterOptions"
          :key="srv.value"
          type="button"
          class="rounded-xl px-3 py-1.5 text-xs font-bold transition"
          :class="selectedServiceFilter === srv.value
            ? 'bg-white text-slate-950 font-black shadow-md'
            : 'border border-white/5 bg-slate-900/80 text-slate-400 hover:bg-white/10'"
          @click="selectedServiceFilter = srv.value"
        >
          {{ srv.label }}
        </button>
      </div>

      <!-- Tarjetas de Clases Rápidas Disponibles -->
      <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 max-h-[360px] overflow-y-auto pr-1">
        <div
          v-for="item in quickFilteredSchedules"
          :key="item.id_horario_servicio"
          class="group flex flex-col justify-between rounded-2xl border p-4 transition cursor-pointer"
          :class="Number(selectedScheduleId) === Number(item.id_horario_servicio)
            ? 'border-cyan-400 bg-cyan-950/30 shadow-lg shadow-cyan-950/20'
            : isEnrolledIn(item.id_horario_servicio)
              ? 'border-emerald-500/40 bg-emerald-950/20 hover:border-emerald-400'
              : 'border-white/10 bg-slate-900/60 hover:border-white/20 hover:bg-slate-900/90'"
          @click="selectAvailableSchedule(item)"
        >
          <div>
            <div class="flex items-center justify-between gap-2">
              <span class="rounded-lg bg-white/10 px-2 py-0.5 text-[10px] font-black uppercase text-slate-300">
                {{ serviceLabel(item.servicio) }}
              </span>
              <span
                class="rounded-md px-2 py-0.5 text-[10px] font-black"
                :class="isEnrolledIn(item.id_horario_servicio)
                  ? 'bg-emerald-400/20 text-emerald-300'
                  : slotsBadgeInfo(item).tone === 'danger'
                    ? 'bg-rose-400/20 text-rose-300'
                    : slotsBadgeInfo(item).tone === 'warning'
                      ? 'bg-amber-400/20 text-amber-300'
                      : 'bg-emerald-400/10 text-emerald-300'"
              >
                {{ isEnrolledIn(item.id_horario_servicio) ? '✓ Matriculado' : slotsBadgeInfo(item).shortLabel }}
              </span>
            </div>

            <h4 class="mt-2 text-sm font-black text-white group-hover:text-cyan-300 transition">
              {{ exerciseName(item) }}
            </h4>
            <p class="mt-1 text-xs text-slate-400 flex items-center gap-1">
              <Clock class="h-3 w-3 text-slate-500" />
              <span class="capitalize">{{ dayLabel(item.dia) }}</span> · {{ formatScheduleHours(item) }}
            </p>
          </div>

          <div class="mt-3 flex items-center justify-between border-t border-white/5 pt-3">
            <span class="text-[11px] text-slate-400">
              Cupos: <strong>{{ availableSlots(item) }}</strong> / {{ item.cupos }}
            </span>

            <button
              v-if="!isEnrolledIn(item.id_horario_servicio)"
              type="button"
              class="rounded-xl px-2.5 py-1 text-xs font-black transition disabled:opacity-40"
              :class="isScheduleFull(item)
                ? 'bg-slate-800 text-slate-500'
                : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'"
              :disabled="isScheduleFull(item) || Boolean(actionBusy)"
              @click.stop="quickEnroll(item)"
            >
              {{ isScheduleFull(item) ? 'Lleno' : 'Matricular' }}
            </button>
            <span v-else class="text-xs font-bold text-emerald-400">
              En tu horario
            </span>
          </div>
        </div>

        <p v-if="!quickFilteredSchedules.length" class="col-span-full rounded-2xl border border-dashed border-white/10 p-6 text-center text-xs text-slate-400">
          No hay clases que coincidan con los filtros seleccionados.
        </p>
      </div>
    </section>

    <!-- Layout de los 2 Horarios (Completo y Propio) -->
    <div
      class="grid gap-6"
      :class="viewMode === 'split' ? 'xl:grid-cols-2' : 'grid-cols-1'"
    >
      <!-- HORARIO 1: HORARIO COMPLETO DEL GIMNASIO -->
      <section
        v-if="viewMode === 'split' || viewMode === 'full'"
        class="space-y-4 rounded-3xl border border-white/10 bg-slate-950/60 p-4 shadow-xl backdrop-blur-xl sm:p-6"
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="inline-flex items-center gap-1.5 rounded-full bg-cyan-400/10 px-3 py-1 text-xs font-black uppercase tracking-wider text-cyan-300">
              <Calendar class="h-3.5 w-3.5" />
              1. Horario Completo del Gimnasio
            </div>
            <h2 class="mt-2 text-xl font-black text-white sm:text-2xl">Todas las clases del gimnasio</h2>
            <p class="text-xs text-slate-400">Horario lleno con todas las disciplinas, ejercicios y cupos del gym.</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="rounded-xl bg-slate-900 px-3 py-1.5 text-xs font-bold text-slate-300">
              {{ schedules.length }} clases activas
            </span>
          </div>
        </div>

        <ExcelScheduleGrid
          title="Calendario General del Gimnasio"
          subtitle="Haz clic en cualquier clase para ver el ejercicio, cupos y matricularte."
          :items="enrichedSchedules"
          file-name="horario-general-gimnasio.xlsx"
          empty-message="No hay horarios activos disponibles en este momento."
          interactive
          :selected-item-id="selectedScheduleId"
          @select="selectAvailableSchedule"
        />
      </section>

      <!-- HORARIO 2: MI HORARIO PROPIO (INICIALMENTE VACÍO) -->
      <section
        v-if="viewMode === 'split' || viewMode === 'own'"
        class="space-y-4 rounded-3xl border border-white/10 bg-slate-950/60 p-4 shadow-xl backdrop-blur-xl sm:p-6"
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-black uppercase tracking-wider text-emerald-300">
              <Clock class="h-3.5 w-3.5" />
              2. Mi Horario Propio
            </div>
            <h2 class="mt-2 text-xl font-black text-white sm:text-2xl">{{ ownCalendarTitle }}</h2>
            <p class="text-xs text-slate-400">Inicia vacío; las clases matriculadas se colocarán automáticamente aquí.</p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="rounded-xl px-3 py-1.5 text-xs font-bold"
              :class="visibleEnrollments.length ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-400/10 text-amber-300'"
            >
              {{ visibleEnrollments.length ? `${visibleEnrollments.length} matriculada(s)` : 'Horario vacío' }}
            </span>
          </div>
        </div>

        <ExcelScheduleGrid
          title="Mi Calendario Personal"
          subtitle="Las clases que matricules aparecerán automáticamente en esta cuadrícula."
          :items="enrichedEnrollments"
          file-name="mi-horario-personal.xlsx"
          empty-message="Tu horario está vacío. Selecciona una clase del horario general y pulsa Matricular."
          interactive
          :selected-item-id="selectedOwnScheduleId"
          @select="selectOwnSchedule"
        />

        <!-- Lista de clases matriculadas con opción de desmatricularse -->
        <div v-if="visibleEnrollments.length" class="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
            <h4 class="text-xs font-black uppercase tracking-wider text-slate-400">Clases en tu horario</h4>
            <div class="mt-3 space-y-2">
              <div
                v-for="enrollment in visibleEnrollments"
                :key="enrollment.id_matricula"
                class="flex flex-col gap-3 rounded-xl border border-white/5 bg-white/5 p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p class="text-sm font-black text-white">{{ exerciseName(enrollment) }}</p>
                  <p class="text-xs text-slate-300">
                    <span class="capitalize">{{ dayLabel(enrollment.dia) }}</span> · {{ formatScheduleHours(enrollment) }} · {{ serviceLabel(enrollment.servicio) }}
                  </p>
                </div>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-bold text-rose-200 transition hover:bg-rose-500/20 disabled:opacity-50"
                  :disabled="actionBusy === `cancel-${enrollment.id_matricula}`"
                  @click="cancelEnrollment(enrollment)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                  {{ actionBusy === `cancel-${enrollment.id_matricula}` ? 'Quitando…' : 'Quitar de mi horario' }}
                </button>
              </div>
            </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  AlertCircle,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  Columns2,
  Dumbbell,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
} from 'lucide-vue-next';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import {
  buildClientIdentityFromUser,
  findClientForUser,
  normalizeDni,
  resolveClientIdForUser,
} from '../utils/clientIdentity';
import {
  activeServiceSchedules,
  availableSlots,
  dayLabel,
  enrollmentsForClient,
  exerciseName,
  formatScheduleHours,
  isScheduleFull,
  serviceLabel,
  slotsBadgeInfo,
} from '../utils/scheduleEnrollment';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const viewMode = ref('split'); // 'split', 'full', 'own'
const selectedDayFilter = ref('todos');
const selectedServiceFilter = ref('todos');
const searchQuery = ref('');

const dniSearch = ref('');
const selectedClient = ref(null);
const selectedScheduleId = ref('');
const selectedOwnScheduleId = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const actionBusy = ref('');
const isRefreshing = ref(false);
const isSearchingClient = ref(false);

const dayFilterOptions = [
  { label: 'Todos los días', value: 'todos' },
  { label: 'Lunes', value: 'lunes' },
  { label: 'Martes', value: 'martes' },
  { label: 'Miércoles', value: 'miercoles' },
  { label: 'Jueves', value: 'jueves' },
  { label: 'Viernes', value: 'viernes' },
  { label: 'Sábado', value: 'sabado' },
];

const serviceFilterOptions = [
  { label: 'Todos los servicios', value: 'todos' },
  { label: 'Musculación', value: 'musculacion' },
  { label: 'Cardio', value: 'cardio' },
  { label: 'Fitness', value: 'fitness' },
  { label: 'Baile', value: 'baile' },
];

const isAdminUser = computed(() => Boolean(isAdmin.value));
const authUser = computed(() => user.value || {});
const authClient = computed(() => findClientForUser(authUser.value, gymStore.members));
const authClientId = computed(() =>
  Number(authClient.value?.id_cliente || resolveClientIdForUser(authUser.value, gymStore.members) || 0),
);
const currentClient = computed(() =>
  isAdminUser.value
    ? selectedClient.value
    : authClient.value || buildClientIdentityFromUser(authUser.value, gymStore.members),
);
const currentClientId = computed(() =>
  Number(currentClient.value?.id_cliente || (isAdminUser.value ? 0 : authClientId.value) || 0),
);

const schedules = computed(() => activeServiceSchedules(gymStore.serviceSchedules || []));

const visibleEnrollments = computed(() =>
  enrollmentsForClient(
    gymStore.enrollments || [],
    gymStore.serviceSchedules || [],
    currentClientId.value,
  ),
);

const totalAvailableSlots = computed(() =>
  schedules.value.reduce((total, schedule) => total + availableSlots(schedule), 0),
);

const isEnrolledIn = (scheduleId) =>
  visibleEnrollments.value.some(
    (item) => Number(item.id_horario_servicio) === Number(scheduleId),
  );

const enrichedSchedules = computed(() =>
  schedules.value.map((schedule) => ({
    ...schedule,
    is_enrolled: isEnrolledIn(schedule.id_horario_servicio),
  })),
);

const enrichedEnrollments = computed(() =>
  visibleEnrollments.value.map((item) => ({
    ...item,
    is_enrolled: true,
  })),
);

const quickFilteredSchedules = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  return schedules.value.filter((item) => {
    const matchesDay = selectedDayFilter.value === 'todos' || String(item.dia).toLowerCase() === selectedDayFilter.value;
    const matchesService = selectedServiceFilter.value === 'todos' || String(item.servicio).toLowerCase() === selectedServiceFilter.value;
    const name = exerciseName(item).toLowerCase();
    const matchesQuery = !query || name.includes(query) || String(item.servicio).toLowerCase().includes(query);
    return matchesDay && matchesService && matchesQuery;
  });
});

const selectedSchedule = computed(() =>
  schedules.value.find(
    (schedule) => Number(schedule.id_horario_servicio) === Number(selectedScheduleId.value),
  ) || null,
);

const selectedIsEnrolled = computed(() =>
  Boolean(selectedSchedule.value && isEnrolledIn(selectedSchedule.value.id_horario_servicio)),
);

const canEnrollSelected = computed(() =>
  Boolean(
    selectedSchedule.value &&
    currentClientId.value &&
    !selectedIsEnrolled.value &&
    !isScheduleFull(selectedSchedule.value),
  ),
);

const enrollButtonLabel = computed(() => {
  if (actionBusy.value === `enroll-${selectedSchedule.value?.id_horario_servicio}`) return 'Matriculando…';
  if (!currentClientId.value) return isAdminUser.value ? 'Busca un cliente por DNI primero' : 'Identificando sesión…';
  if (selectedIsEnrolled.value) return 'Ya estás matriculado en esta clase';
  if (selectedSchedule.value && isScheduleFull(selectedSchedule.value)) return 'Sin cupos disponibles';
  return 'Matricularme en esta clase';
});

const ownCalendarTitle = computed(() => {
  if (isAdminUser.value && !selectedClient.value) return 'Horario del cliente';
  return currentClient.value?.name ? `Horario de ${currentClient.value.name}` : 'Mi horario personal';
});

const setFeedback = (message, tone = 'success') => {
  feedback.value = message;
  feedbackTone.value = tone;
};

const selectAvailableSchedule = (schedule) => {
  selectedScheduleId.value = schedule?.id_horario_servicio || '';
  feedback.value = '';
};

const selectOwnSchedule = (schedule) => {
  selectedOwnScheduleId.value = schedule?.id_horario_servicio || '';
  feedback.value = '';
};

const refreshAll = async ({ announce = false } = {}) => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;

  try {
    try {
      await gymStore.fetchFromBackend?.();
    } catch (primaryError) {
      const fallback = await Promise.allSettled([
        gymStore.refreshServiceSchedulesFromBackend?.(),
        gymStore.refreshEnrollmentsFromBackend?.(),
      ]);
      if (fallback.every((result) => result.status === 'rejected')) throw primaryError;
    }

    if (currentClientId.value) {
      await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    }
    if (announce) setFeedback('Horarios actualizados correctamente.');
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudieron cargar los horarios.', 'error');
  } finally {
    isRefreshing.value = false;
  }
};

const loadAdminClient = async () => {
  const dni = normalizeDni(dniSearch.value);
  if (!dni) {
    selectedClient.value = null;
    setFeedback('Ingresa el DNI del cliente.', 'error');
    return;
  }

  isSearchingClient.value = true;
  try {
    await gymStore.fetchFromBackend?.().catch(() => {});
    const client = gymStore.members.find((member) => normalizeDni(member.dni) === dni) || null;
    if (!client) {
      selectedClient.value = null;
      setFeedback('Cliente no encontrado por DNI.', 'error');
      return;
    }

    selectedClient.value = client;
    selectedOwnScheduleId.value = '';
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: client.id_cliente });
    setFeedback(`Horario de ${client.name} cargado con éxito.`);
  } catch (error) {
    selectedClient.value = null;
    setFeedback(error instanceof Error ? error.message : 'No se pudo buscar al cliente.', 'error');
  } finally {
    isSearchingClient.value = false;
  }
};

const enrollSelected = async () => {
  const schedule = selectedSchedule.value;
  if (!schedule) return;
  await processEnrollment(schedule);
};

const quickEnroll = async (schedule) => {
  selectedScheduleId.value = schedule.id_horario_servicio;
  await processEnrollment(schedule);
};

const processEnrollment = async (schedule) => {
  if (!currentClientId.value) {
    setFeedback(isAdminUser.value ? 'Busca primero un cliente por DNI.' : 'No se encontró la identidad de tu cuenta.', 'error');
    return;
  }
  if (isEnrolledIn(schedule.id_horario_servicio)) {
    setFeedback('Esta clase ya está en tu horario.', 'error');
    return;
  }
  if (isScheduleFull(schedule)) {
    setFeedback('Este horario ya no tiene cupos disponibles.', 'error');
    return;
  }

  actionBusy.value = `enroll-${schedule.id_horario_servicio}`;
  try {
    await gymStore.enrollSchedule({
      id_cliente: currentClientId.value,
      id_horario_servicio: schedule.id_horario_servicio,
    });
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    selectedOwnScheduleId.value = schedule.id_horario_servicio;
    setFeedback(`¡Matrícula exitosa! "${exerciseName(schedule)}" se agregó a tu horario.`);
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudo registrar la matrícula.', 'error');
  } finally {
    actionBusy.value = '';
  }
};

const cancelEnrollment = async (enrollment) => {
  if (!enrollment?.id_matricula) return;

  actionBusy.value = `cancel-${enrollment.id_matricula}`;
  try {
    await gymStore.deleteEnrollment(enrollment.id_matricula);
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    selectedOwnScheduleId.value = '';
    setFeedback(`"${exerciseName(enrollment)}" se quitó de tu horario.`);
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudo quitar la clase de tu horario.', 'error');
  } finally {
    actionBusy.value = '';
  }
};

watch(currentClientId, () => {
  selectedOwnScheduleId.value = '';
});

watch(schedules, (items) => {
  if (selectedScheduleId.value && !items.some(
    (schedule) => Number(schedule.id_horario_servicio) === Number(selectedScheduleId.value),
  )) {
    selectedScheduleId.value = '';
  }
});

onMounted(() => refreshAll());
</script>
