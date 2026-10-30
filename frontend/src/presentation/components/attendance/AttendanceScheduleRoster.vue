<template>
  <section class="att-panel att-schedule-control" aria-label="Asistencia por horario">
    <div class="att-heading-row">
      <div>
        <p class="att-eyebrow">Asistencia por horario</p>
        <h2>Selecciona una clase</h2>
        <p class="att-muted att-small">Abre un horario para registrar a sus clientes matriculados. Hora de Perú.</p>
      </div>
      <label class="att-day-filter">Día
        <select v-model="dayFilter">
          <option value="">Todos los días</option>
          <option v-for="(label, key) in days" :key="key" :value="key">{{ label }}</option>
        </select>
      </label>
    </div>
    <p v-if="schedulesError" role="alert" class="att-message is-error">
      {{ schedulesError }} <button class="att-link" @click="$emit('reload')">Reintentar</button>
    </p>
    <div v-if="schedulesLoading && !scheduleData" class="att-empty" role="status">Cargando horarios…</div>
    <div v-else-if="scheduleData" class="att-table-wrap">
      <table class="att-table att-schedules-table">
        <caption class="att-sr-only">Horarios disponibles para registrar asistencia</caption>
        <thead><tr><th>Clase</th><th>Día</th><th>Horario</th><th>Matriculados</th><th>Seleccionar</th></tr></thead>
        <tbody>
          <tr v-for="item in visibleSchedules" :key="item.id_horario_servicio"
            :class="{ 'is-selected': selectedSchedule === item.id_horario_servicio }"
            @click="!busy && $emit('select', item.id_horario_servicio)">
            <td data-label="Clase"><strong>{{ services[item.servicio] || item.servicio }}</strong><small>{{ item.rutina_nombre || item.nombre_rutina || '' }}</small></td>
            <td data-label="Día">{{ days[item.dia] }} <span v-if="item.hoy" class="att-badge today">Hoy</span></td>
            <td data-label="Horario">{{ shortTime(item.hora_inicio) }} – {{ shortTime(item.hora_fin) }}</td>
            <td data-label="Matriculados">{{ item.matriculados }}</td>
            <td data-label="Seleccionar"><button class="att-button" :disabled="Boolean(busy)"
              :aria-pressed="selectedSchedule === item.id_horario_servicio"
              :aria-label="`Ver matriculados de ${services[item.servicio] || item.servicio}, ${days[item.dia]}, ${shortTime(item.hora_inicio)}`"
              @click.stop="$emit('select', item.id_horario_servicio)">
              <Users :size="16" />{{ selectedSchedule === item.id_horario_servicio ? 'Seleccionado' : 'Ver clientes' }}
            </button></td>
          </tr>
          <tr v-if="!visibleSchedules.length"><td colspan="5"><div class="att-empty">No hay horarios para este día.</div></td></tr>
        </tbody>
      </table>
    </div>
    <div class="att-roster" aria-live="polite" :aria-busy="rosterLoading">
      <div v-if="!selectedSchedule" class="att-empty"><CalendarDays :size="28" /><p>Selecciona un horario para ver sus matriculados.</p></div>
      <div v-else-if="rosterLoading && !roster" class="att-empty" role="status">Cargando matriculados…</div>
      <p v-else-if="rosterError" role="alert" class="att-message is-error">{{ rosterError }} <button class="att-link" @click="$emit('retry')">Reintentar</button></p>
      <template v-else-if="roster">
        <div class="att-heading-row">
          <div>
            <p class="att-eyebrow">Clientes matriculados · {{ dateLabel(roster.fecha) }}</p>
            <h3>{{ services[roster.horario.servicio] }} · {{ days[roster.horario.dia] }} · {{ shortTime(roster.horario.hora_inicio) }} – {{ shortTime(roster.horario.hora_fin) }}</h3>
          </div>
          <span class="att-count">{{ roster.clientes.length }}</span>
        </div>
        <p class="att-muted att-small">Entrada durante la clase. Salida hasta una hora después del término; pasado ese límite, la asistencia queda incompleta.</p>
        <div v-if="!roster.clientes.length" class="att-empty">Este horario todavía no tiene clientes matriculados.</div>
        <div v-else class="att-table-wrap">
          <table class="att-table att-roster-table">
            <caption class="att-sr-only">Clientes matriculados y asistencia de hoy</caption>
            <thead><tr><th>Cliente</th><th>Entrada</th><th>Salida</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody>
              <tr v-for="student in roster.clientes" :key="student.id_matricula" :class="{ 'is-saved': savedKey === `entry-${student.id_matricula}` || savedKey === `exit-${student.asistencia?.id_asistencia}` }">
                <td data-label="Cliente"><strong>{{ student.cliente.nombre }}</strong><small>DNI {{ student.cliente.dni || 'sin registrar' }}</small></td>
                <td data-label="Entrada">{{ shortTime(student.asistencia?.hora_entrada) }}</td>
                <td data-label="Salida">{{ shortTime(student.asistencia?.hora_salida) }}</td>
                <td data-label="Estado"><span class="att-badge" :class="student.asistencia?.estado || 'neutral'">{{ student.asistencia ? states[student.asistencia.estado] : 'Sin registro' }}</span>
                  <small v-if="student.asistencia?.aviso" class="att-late-notice">{{ student.asistencia.aviso }}</small></td>
                <td data-label="Acción">
                  <button v-if="student.asistencia && !student.asistencia.hora_salida" class="att-button att-primary"
                    :disabled="Boolean(busy) || rosterLoading" :aria-label="`Registrar salida de ${student.cliente.nombre}`"
                    @click="$emit('exit', student.asistencia)"><LogOut :size="16" />{{ busy === `exit-${student.asistencia.id_asistencia}` ? 'Guardando…' : 'Registrar salida' }}</button>
                  <template v-else-if="!student.asistencia">
                    <button class="att-button att-primary" :disabled="!student.puede_entrar || Boolean(busy) || rosterLoading"
                      :title="student.motivo" :aria-label="`Registrar entrada de ${student.cliente.nombre}`"
                      @click="$emit('entry', student)"><LogIn :size="16" />{{ busy === `entry-${student.id_matricula}` ? 'Guardando…' : 'Registrar entrada' }}</button>
                    <small v-if="student.motivo" class="att-late-notice">{{ student.motivo }}</small>
                  </template>
                  <span v-else class="att-muted att-small">Salida registrada</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </section>
</template>
<script setup>
import { computed, ref } from 'vue';
import { CalendarDays, Users, LogIn, LogOut } from 'lucide-vue-next';
import { days, services, states, shortTime, dateLabel } from '../../utils/attendance.js';
const props = defineProps({ scheduleData: Object, selectedSchedule: Number, roster: Object,
  schedulesLoading: Boolean, rosterLoading: Boolean, schedulesError: String, rosterError: String,
  busy: String, savedKey: String });
defineEmits(['select', 'reload', 'retry', 'entry', 'exit']);
const dayFilter = ref('');
const visibleSchedules = computed(() => (props.scheduleData?.horarios || []).filter((s) => !dayFilter.value || s.dia === dayFilter.value));
</script>
