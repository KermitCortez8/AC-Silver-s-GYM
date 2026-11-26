<template>
  <section class="att-schedule-control" aria-label="Asistencia por horario">
    <div class="att-heading-row">
      <div>
        <p class="att-eyebrow">Asistencia por horario</p>
        <h2>Selecciona una clase</h2>
        <p class="att-muted att-small">Selecciona una fecha para consultar sus matriculados. Cada sesión tiene su propia lista; las entradas se registran el día de la clase, hora de Perú.</p>
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
    <ExcelScheduleGrid v-else-if="scheduleData"
      title="Calendario de clases" subtitle="Selecciona un bloque para consultar la asistencia de esa fecha."
      :date="scheduleData.fecha" :items="visibleSchedules" :interactive="!busy"
      :selected-item-id="selectedSchedule" file-name="horarios-asistencia.xlsx"
      empty-message="No hay horarios con el filtro de día seleccionado."
      modal-feedback @notification="$emit('notification', $event)"
      @select="selectClass" @range-change="changeRange" />
    <dialog ref="rosterDialog" class="att-dialog att-roster" :aria-labelledby="titleId" @cancel.prevent="closeRoster">
      <div v-if="selectedSchedule" class="att-dialog-body">
        <header class="att-heading-row">
          <div>
            <p v-if="selectedSession || roster?.fecha" class="att-eyebrow">{{ dateLabel(selectedSession || roster.fecha, { weekday: 'long' }) }}</p>
            <h2 :id="titleId">Clientes matriculados</h2>
          </div>
          <button type="button" class="att-icon-button" aria-label="Cerrar matriculados" :disabled="Boolean(busy)" autofocus @click="closeRoster"><X :size="20" /></button>
        </header>
        <FloatingNotice v-if="rosterError" in-dialog :message="rosterError" tone="error" action-label="Reintentar"
          @action="$emit('retry')" @dismiss="$emit('dismiss-roster-error')" />
        <FloatingNotice v-else in-dialog :message="noticeMessage" :tone="noticeTone" @dismiss="$emit('dismiss-notice')" />
        <div class="att-roster-content" :aria-busy="rosterLoading">
          <div v-if="rosterLoading && !roster" class="att-empty" role="status">Cargando matriculados…</div>
          <template v-else-if="roster">
            <div class="att-heading-row">
              <h3>{{ services[roster.horario.servicio] }} · {{ days[roster.horario.dia] }} · {{ shortTime(roster.horario.hora_inicio) }} – {{ shortTime(roster.horario.hora_fin) }}</h3>
              <span class="att-count">{{ roster.clientes.length }}</span>
            </div>
            <p class="att-muted att-small">Entrada durante la clase. Salida hasta una hora después del término; pasado ese límite, la asistencia queda incompleta.</p>
            <div v-if="!roster.clientes.length" class="att-empty">Este horario todavía no tiene clientes matriculados.</div>
            <div v-else class="att-table-wrap">
              <table class="att-table att-roster-table">
                <caption class="att-sr-only">Clientes matriculados y asistencia de la fecha seleccionada</caption>
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
                        <small v-if="student.motivo_coincidencia && student.motivo_coincidencia !== student.motivo" class="att-late-notice">{{ student.motivo_coincidencia }}</small>
                        <button v-if="student.asistencia_abierta" class="att-button"
                          :disabled="Boolean(busy) || rosterLoading"
                          :aria-label="`Registrar salida pendiente de ${student.cliente.nombre}`"
                          @click="$emit('exit', student.asistencia_abierta)"><LogOut :size="16" />{{ busy === `exit-${student.asistencia_abierta.id_asistencia}` ? 'Guardando…' : 'Registrar salida pendiente' }}</button>
                      </template>
                      <span v-else class="att-muted att-small">Salida registrada</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <div v-else-if="!rosterError" class="att-empty"><button type="button" class="att-button" @click="$emit('retry')">Reintentar consulta</button></div>
        </div>
      </div>
    </dialog>
  </section>
</template>
<script setup>
import { computed, ref, useId, watchPostEffect } from 'vue';
import { LogIn, LogOut, X } from 'lucide-vue-next';
import ExcelScheduleGrid from '../ExcelScheduleGrid.vue';
import FloatingNotice from '../FloatingNotice.vue';
import { days, services, states, shortTime, dateLabel } from '../../utils/attendance.js';
const props = defineProps({ scheduleData: Object, selectedSchedule: Number, selectedSession: String, roster: Object,
  schedulesLoading: Boolean, rosterLoading: Boolean, schedulesError: String, rosterError: String,
  busy: String, savedKey: String, noticeMessage: String, noticeTone: String });
const emit = defineEmits(['select', 'reload', 'retry', 'entry', 'exit', 'dismiss-notice', 'dismiss-roster-error', 'notification']);
const dayFilter = ref('');
const rosterDialog = ref(null);
const titleId = useId();
watchPostEffect(() => {
  const dialog = rosterDialog.value;
  if (!dialog) return;
  if (props.selectedSchedule && !dialog.open) dialog.showModal();
  else if (!props.selectedSchedule && dialog.open) dialog.close();
});
const visibleSchedules = computed(() => (props.scheduleData?.horarios || [])
  .filter((s) => !dayFilter.value || s.dia === dayFilter.value)
  .map((s) => ({ ...s, cupos_usados: s.matriculados,
    rutina_nombre: s.rutina_nombre || s.nombre_rutina || '' })));
const selectClass = (item) => {
  if (props.busy) return;
  emit('select', item.id_horario_servicio, item.fecha);
};
const closeRoster = () => {
  if (!props.busy) emit('select', null);
};
const changeRange = ({ start, end }) => {
  if (props.selectedSession && (props.selectedSession < start || props.selectedSession > end)) {
    emit('select', null);
  }
};
</script>
