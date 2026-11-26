<template>
  <div class="attendance-page">
    <header class="att-page-header">
      <div>
        <p class="att-eyebrow">Recepción · Silver's Gym</p>
        <h1>Asistencias</h1>
        <p class="att-muted">
          Cada visita, en orden. Gestiona las entradas y salidas de tus
          clientes.
        </p>
      </div>
      <div class="att-header-tools">
        <span class="att-date"
          ><CalendarDays :size="16" />{{
            dateLabel(summary?.fecha || limaDate())
          }}</span
        ><button
          class="att-button"
          :disabled="refreshing || Boolean(busy)"
          @click="refresh"
        >
          <RefreshCw
            :size="16"
            :class="{ 'att-spinning': refreshing }"
          />Actualizar
        </button>
      </div>
    </header>
    <AttendanceSummary :summary="summary" :refreshing="refreshing" />

    <div class="att-toolbar">
      <div
        class="att-tabs"
        role="tablist"
        aria-label="Vistas de asistencia"
        @keydown="handleTabKey"
      >
        <button
          v-for="item in attendanceTabs"
          :id="`${item.key}-tab`"
          :key="item.key"
          :aria-selected="tab === item.key"
          :tabindex="tab === item.key ? 0 : -1"
          role="tab"
          :aria-controls="
            item.key === 'history' ? 'history-panel' : 'control-panel'
          "
          @click="tab = item.key"
        >
          <component :is="item.icon" :size="16" />{{ item.label }}
        </button>
      </div>
      <span class="att-muted att-small"
        ><ShieldCheck :size="14" />Registro exclusivo del administrador</span
      >
    </div>
    <FloatingNotice v-if="tab !== 'history' && !selectedSchedule" :message="error || feedback" :tone="noticeTone" @dismiss="dismissNotice" />
    <div
      v-show="tab !== 'history'"
      id="control-panel"
      role="tabpanel"
      :aria-labelledby="`${tab}-tab`"
      class="att-attendance-controls" :class="{ 'att-control-grid': isGeneral }"
    >
      <AttendanceScheduleRoster v-show="tab === 'today'"
        :schedule-data="scheduleData" :selected-schedule="selectedSchedule" :selected-session="selectedSession" :roster="roster"
        :schedules-loading="schedulesLoading" :roster-loading="rosterLoading"
        :schedules-error="schedulesError" :roster-error="rosterError" :busy="busy" :saved-key="savedKey"
        :notice-message="error || feedback" :notice-tone="noticeTone"
        @dismiss-notice="dismissNotice" @dismiss-roster-error="rosterError = ''" @notification="showCalendarNotice"
        @select="selectSchedule" @reload="loadSchedules" @retry="loadRoster" @entry="enter" @exit="exitRecord" />
      <AttendanceClientLookup
        v-if="isGeneral"
        v-model:dni="dni"
        :client-data="clientData"
        :is-general="isGeneral"
        :searching="searching"
        :lookup-error="lookupError"
        :busy="busy"
        :saved-key="savedKey"
        @input="onDniInput"
        @search="lookupClient()"
        @back="backToSearch"
        @entry="enter"
        @general-entry="enterGeneral"
        @exit="exitRecord"
      />
      <AttendancePendingVisits
        :summary="summary"
        :is-general="isGeneral"
        :refreshing="refreshing"
        :busy="busy"
        :now="now"
        @refresh="refresh"
        @exit="exitRecord"
      />
    </div>
    <div
      v-if="tab === 'history'"
      id="history-panel"
      role="tabpanel"
      aria-labelledby="history-tab"
    >
      <AttendanceHistory admin :refresh-error="error" @changed="refresh" @dismiss-refresh-error="error = ''" />
    </div>
  </div>
</template>
<script setup>
import { computed, nextTick, ref } from 'vue';
import {
  CalendarDays,
  RefreshCw,
  ScanLine,
  Users,
  History,
  ShieldCheck,
} from 'lucide-vue-next';
import { useAuth } from '../../application/composables/useAuth';
import { useAttendance } from '../../application/services/attendance.js';
import { useAttendanceControl } from '../composables/attendance/useAttendanceControl.js';
import { dateLabel, limaDate } from '../utils/attendance.js';
import AttendanceHistory from '../components/attendance/AttendanceHistory.vue';
import AttendanceSummary from '../components/attendance/AttendanceSummary.vue';
import AttendanceClientLookup from '../components/attendance/AttendanceClientLookup.vue';
import AttendancePendingVisits from '../components/attendance/AttendancePendingVisits.vue';
import AttendanceScheduleRoster from '../components/attendance/AttendanceScheduleRoster.vue';
import FloatingNotice from '../components/FloatingNotice.vue';
import '../styles/attendance.css';
import '../styles/attendance-control.css';
const { token } = useAuth();
const {
  dni,
  clientData,
  lookupError,
  searching,
  onDniInput,
  backToSearch,
  lookupClient,
  summary,
  refreshing,
  busy,
  error,
  feedback,
  feedbackWarning,
  savedKey,
  now,
  refresh,
  enter,
  enterGeneral,
  exitRecord,
  scheduleData,
  selectedSchedule,
  selectedSession,
  roster,
  schedulesLoading,
  rosterLoading,
  schedulesError,
  rosterError,
  loadSchedules,
  loadRoster,
  selectSchedule,
} = useAttendanceControl({ ...useAttendance(), token });
const attendanceTabs = [
  { key: 'today', label: 'Por horarios', icon: ScanLine },
  { key: 'general', label: 'Gimnasio general', icon: Users },
  { key: 'history', label: 'Historial', icon: History },
];
const tab = ref('today');
const isGeneral = computed(() => tab.value === 'general');
const noticeTone = computed(() => error.value ? 'error' : feedbackWarning.value ? 'warning' : 'success');
const dismissNotice = () => {
  if (error.value) error.value = '';
  else feedback.value = '';
};
const showCalendarNotice = ({ message, tone }) => {
  if (tone === 'error') error.value = message;
  else {
    error.value = '';
    feedbackWarning.value = false;
    feedback.value = message;
  }
};
const handleTabKey = async (event) => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault();
  const tablist = event.currentTarget;
  const keys = attendanceTabs.map((item) => item.key);
  const index = keys.indexOf(tab.value);
  tab.value =
    event.key === 'Home'
      ? keys[0]
      : event.key === 'End'
        ? keys.at(-1)
        : keys[
            (index + (event.key === 'ArrowRight' ? 1 : -1) + keys.length) %
              keys.length
          ];
  await nextTick();
  tablist.querySelector('[aria-selected="true"]')?.focus();
};
</script>
