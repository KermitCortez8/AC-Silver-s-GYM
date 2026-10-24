<template>
  <div class="att-heading-row att-schedule-heading">
    <h3>
      {{
        showAllSchedules || !todaySchedules.length
          ? 'Horarios matriculados'
          : 'Horarios de hoy'
      }}
    </h3>
    <span class="att-muted att-small">{{
      visibleSchedules.length === clientData.horarios.length
        ? `${clientData.horarios.length} horario${clientData.horarios.length === 1 ? '' : 's'}`
        : `${visibleSchedules.length} de ${clientData.horarios.length} horarios`
    }}</span>
  </div>
  <article
    v-for="item in visibleSchedules"
    :key="item.id_matricula"
    class="att-row"
    :class="{
      'is-today': item.hoy,
      'is-inside': item.asistencia && !item.asistencia.hora_salida,
      'is-saved': isSaved(item),
    }"
  >
    <div class="att-row-main">
      <div class="att-row-title">
        <h4>{{ services[item.servicio] || item.servicio }}</h4>
        <span
          v-if="item.asistencia || item.hoy"
          class="att-badge"
          :class="item.asistencia?.estado || 'today'"
          >{{ item.asistencia ? states[item.asistencia.estado] : 'Hoy' }}</span
        >
      </div>
      <p class="att-muted">
        {{ days[item.dia] }} · {{ shortTime(item.hora_inicio) }} –
        {{ shortTime(item.hora_fin) }}
      </p>
    </div>
    <div class="att-row-action">
      <p v-if="item.asistencia" class="att-row-times">
        Entrada
        <strong>{{ shortTime(item.asistencia.hora_entrada) }}</strong>
        · Salida
        <strong>{{ shortTime(item.asistencia.hora_salida) }}</strong>
      </p>
      <button
        v-if="item.asistencia && !item.asistencia.hora_salida"
        class="att-button att-primary"
        :disabled="Boolean(busy)"
        @click="$emit('exit', item.asistencia)"
      >
        <LogOut :size="16" />{{
          busy === `exit-${item.asistencia.id_asistencia}`
            ? 'Guardando…'
            : 'Registrar salida'
        }}</button
      ><button
        v-else-if="!item.asistencia"
        class="att-button att-primary"
        :disabled="!item.puede_entrar || Boolean(busy)"
        :title="item.puede_entrar ? '' : blockedText(item)"
        @click="$emit('entry', item)"
      >
        <LogIn :size="16" />{{
          busy === `entry-${item.id_matricula}`
            ? 'Guardando…'
            : 'Registrar entrada'
        }}
      </button>
    </div>
    <p
      v-if="item.motivo && !item.asistencia && !clientBlock"
      class="att-blocked-reason att-row-note"
      role="status"
    >
      <Info :size="16" /><span>{{ blockedText(item) }}</span>
    </p>
  </article>
  <button
    v-if="canToggleSchedules"
    type="button"
    class="att-link att-schedule-toggle"
    @click="showAllSchedules = !showAllSchedules"
  >
    {{
      showAllSchedules
        ? 'Mostrar solo los de hoy'
        : `Ver ${hiddenSchedules} horario${hiddenSchedules === 1 ? '' : 's'} de otros días`
    }}
  </button>
  <div v-if="!clientData.horarios.length" class="att-empty">
    <CalendarDays :size="28" />
    <h3>Sin horarios matriculados</h3>
    <p>Matricula al cliente en un horario para registrar su visita.</p>
    <router-link class="att-link" to="/admin/enrollment"
      >Ir a matrículas <ArrowRight :size="15"
    /></router-link>
  </div>
</template>
<script setup>
import { toRef } from 'vue';
import { CalendarDays, ArrowRight, LogIn, LogOut, Info } from 'lucide-vue-next';
import { days, services, states, shortTime } from '../../utils/attendance.js';
import { useAttendanceSchedules } from '../../composables/attendance/useAttendanceSchedules.js';
const props = defineProps({
  clientData: { type: Object, required: true },
  clientBlock: String,
  busy: String,
  savedKey: String,
});
defineEmits(['entry', 'exit']);
const {
  blockedText,
  showAllSchedules,
  todaySchedules,
  visibleSchedules,
  hiddenSchedules,
  canToggleSchedules,
} = useAttendanceSchedules(toRef(props, 'clientData'));
const isSaved = (item) =>
  props.savedKey === `entry-${item.id_matricula}` ||
  Boolean(
    item.asistencia &&
    props.savedKey === `exit-${item.asistencia.id_asistencia}`,
  );
</script>
