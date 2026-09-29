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
    <div class="att-metrics" :aria-busy="refreshing">
      <article class="att-metric">
        <span class="att-metric-icon"><LogIn :size="21" /></span>
        <div>
          <p>Entradas de hoy</p>
          <strong>{{ summary?.entradas ?? '—' }}</strong
          ><small>Visitas registradas</small>
        </div>
      </article>
      <article class="att-metric att-metric-featured">
        <span class="att-metric-icon"><Users :size="21" /></span>
        <div>
          <p>Dentro del gimnasio</p>
          <strong>{{ summary?.dentro ?? '—' }}</strong
          ><small><span class="att-live-dot" />Con entrada y sin salida</small>
        </div>
      </article>
      <article class="att-metric">
        <span class="att-metric-icon"><LogOut :size="21" /></span>
        <div>
          <p>Salidas de hoy</p>
          <strong>{{ summary?.salidas ?? '—' }}</strong
          ><small>Visitas finalizadas hoy</small>
        </div>
      </article>
    </div>
    <div class="att-toolbar">
      <div
        class="att-tabs"
        role="tablist"
        aria-label="Vistas de asistencia"
        @keydown="handleTabKey"
      >
        <button
          id="today-tab"
          :aria-selected="tab === 'today'"
          :tabindex="tab === 'today' ? 0 : -1"
          role="tab"
          aria-controls="today-panel"
          @click="tab = 'today'"
        >
          <ScanLine :size="16" />Control de hoy</button
        ><button
          id="history-tab"
          :aria-selected="tab === 'history'"
          :tabindex="tab === 'history' ? 0 : -1"
          role="tab"
          aria-controls="history-panel"
          @click="tab = 'history'"
        >
          <History :size="16" />Historial
        </button>
      </div>
      <span class="att-muted att-small"
        ><ShieldCheck :size="14" />Registro exclusivo del administrador</span
      >
    </div>
    <p v-if="error" role="alert" class="att-message is-error">{{ error }}</p>
    <p v-if="feedback" role="status" class="att-message is-success">
      {{ feedback }}
    </p>
    <div
      v-show="tab === 'today'"
      id="today-panel"
      role="tabpanel"
      aria-labelledby="today-tab"
      class="att-control-grid"
    >
      <section class="att-panel att-lookup-panel">
        <div class="att-heading-row">
          <div>
            <p class="att-eyebrow">Registrar una visita</p>
            <h2>Buscar cliente</h2>
          </div>
          <span class="att-soft-icon"><UserSearch :size="22" /></span>
        </div>
        <form class="att-search" @submit.prevent="lookupClient">
          <label for="attendance-dni"
            >DNI del cliente
            <div class="att-search-input">
              <Search :size="18" /><input
                id="attendance-dni"
                v-model="dni"
                inputmode="numeric"
                autocomplete="off"
                maxlength="8"
                pattern="[0-9]{8}"
                required
                placeholder="Ingresa los 8 dígitos"
                @input="clearClient"
              /></div></label
          ><button
            class="att-button att-primary"
            :disabled="searching || Boolean(busy) || !/^\d{8}$/.test(dni)"
          >
            {{ searching ? 'Buscando…' : 'Buscar cliente'
            }}<ArrowRight :size="16" />
          </button>
        </form>
        <p class="att-muted att-small">
          La búsqueda utiliza únicamente el DNI.
        </p>
        <p v-if="lookupError" class="att-message is-error" role="alert">
          {{ lookupError }}
        </p>
        <div v-if="clientData" class="att-client-result">
          <div class="att-client-card">
            <span class="att-avatar">{{
              initials(clientData.cliente.nombre)
            }}</span>
            <div>
              <h3>{{ clientData.cliente.nombre }}</h3>
              <p class="att-muted">DNI {{ clientData.cliente.dni }}</p>
            </div>
            <span
              class="att-badge"
              :class="
                clientData.cliente.estado === 'ACTIVO' && clientData.membresia
                  ? 'completada'
                  : 'anulada'
              "
              >{{
                clientData.cliente.estado === 'ACTIVO' && clientData.membresia
                  ? 'Membresía vigente'
                  : 'Requiere revisión'
              }}</span
            >
          </div>
          <div class="att-membership">
            <div>
              <span>Plan</span
              ><strong>{{ clientData.cliente.plan || 'Sin plan' }}</strong>
            </div>
            <div>
              <span>Vigencia</span
              ><strong>{{
                clientData.membresia
                  ? `Hasta ${dateLabel(clientData.membresia.fecha_fin)}`
                  : 'Sin membresía activa y pagada'
              }}</strong>
            </div>
            <div>
              <span>Cuenta</span
              ><strong>{{
                clientData.cliente.estado === 'ACTIVO'
                  ? 'Activada'
                  : 'Sin activar o desactivada'
              }}</strong>
            </div>
          </div>
          <p v-if="clientBlock" class="att-message is-error" role="alert">
            <strong>No se puede registrar la entrada.</strong>
            {{ clientBlock }}
          </p>
          <div class="att-heading-row att-schedule-heading">
            <h3>Horarios matriculados</h3>
            <span class="att-muted att-small"
              >{{
                visibleSchedules.length === clientData.horarios.length
                  ? `${clientData.horarios.length} horarios`
                  : `${visibleSchedules.length} de ${clientData.horarios.length} horarios`
              }}</span
            >
          </div>
          <article
            v-for="item in visibleSchedules"
            :key="item.id_matricula"
            class="att-schedule-card"
            :class="{ 'is-today': item.hoy }"
          >
            <div class="att-schedule-top">
              <span class="att-service">{{
                services[item.servicio] || item.servicio
              }}</span
              ><span
                class="att-badge"
                :class="
                  item.asistencia?.estado || (item.hoy ? 'today' : 'neutral')
                "
                >{{
                  item.asistencia
                    ? states[item.asistencia.estado]
                    : item.hoy
                      ? 'Hoy'
                      : days[item.dia]
                }}</span
              >
            </div>
            <h4>
              {{ days[item.dia] }}
              <span
                >· {{ shortTime(item.hora_inicio) }} –
                {{ shortTime(item.hora_fin) }}</span
              >
            </h4>
            <div class="att-schedule-bottom">
              <div class="att-visittimes">
                <span
                  >Entrada
                  <strong>{{
                    shortTime(item.asistencia?.hora_entrada)
                  }}</strong></span
                ><span
                  >Salida
                  <strong>{{
                    shortTime(item.asistencia?.hora_salida)
                  }}</strong></span
                >
              </div>
              <button
                v-if="item.asistencia && !item.asistencia.hora_salida"
                class="att-button att-primary"
                :disabled="Boolean(busy)"
                @click="exitRecord(item.asistencia)"
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
                @click="enter(item)"
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
              class="att-blocked-reason"
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
        </div>
        <div
          v-else-if="!searching && !lookupError"
          class="att-empty att-search-empty"
        >
          <span class="att-empty-illustration"><ScanLine :size="38" /></span>
          <h3>Todo comienza con el DNI</h3>
          <p>
            Encuentra al cliente, revisa su membresía<br />y registra la visita
            en su horario.
          </p>
          <span class="att-muted att-small"
            ><Clock3 :size="14" />Fecha y hora de Perú</span
          >
        </div>
      </section>
      <aside class="att-panel att-inside-panel">
        <div class="att-heading-row">
          <div>
            <p class="att-eyebrow">En este momento</p>
            <h2>Entradas sin salida</h2>
          </div>
          <span class="att-count">{{
            summary?.pendientes?.length ?? '—'
          }}</span>
        </div>
        <p class="att-muted att-small">
          Incluye visitas de días anteriores que necesitan revisión.
        </p>
        <div v-if="refreshing && !summary" class="att-empty" role="status">
          Cargando actividad…
        </div>
        <div v-else-if="!summary" class="att-empty">
          <Info :size="28" />
          <p>No pudimos cargar la actividad.</p>
          <button class="att-link" @click="refresh">Reintentar</button>
        </div>
        <div v-else-if="!summary.pendientes.length" class="att-empty">
          <CircleCheck :size="30" />
          <h3>Todo al día</h3>
          <p>No hay entradas pendientes de salida.</p>
        </div>
        <div v-else class="att-inside-list">
          <article
            v-for="record in summary.pendientes"
            :key="record.id_asistencia"
            class="att-person"
          >
            <div class="att-person-top">
              <span class="att-avatar small">{{
                initials(record.cliente_nombre)
              }}</span>
              <div>
                <h3>{{ record.cliente_nombre }}</h3>
                <p>DNI {{ record.cliente_dni }}</p>
              </div>
            </div>
            <div class="att-person-bottom">
              <span
                >{{ services[record.servicio]
                }}<small
                  >Entrada {{ shortTime(record.hora_entrada || record.hora)
                  }}<span
                    v-if="record.fecha !== summary.fecha"
                    class="att-overdue"
                  >
                    · {{ dateLabel(record.fecha) }}</span
                  ></small
                ></span
              ><button
                class="att-button"
                :disabled="Boolean(busy)"
                :aria-label="`Registrar salida de ${record.cliente_nombre}`"
                @click="exitRecord(record)"
              >
                {{
                  busy === `exit-${record.id_asistencia}`
                    ? 'Guardando…'
                    : 'Salida'
                }}<LogOut :size="14" />
              </button>
            </div>
          </article>
        </div>
        <div class="att-aside-note">
          <ShieldCheck :size="18" />
          <p>
            Las entradas requieren cuenta activada, membresía vigente y horario
            habilitado.
          </p>
        </div>
      </aside>
    </div>
    <div
      v-if="tab === 'history'"
      id="history-panel"
      role="tabpanel"
      aria-labelledby="history-tab"
    >
      <AttendanceHistory admin @changed="refresh" />
    </div>
  </div>
</template>
<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import {
  ArrowRight,
  CalendarDays,
  CircleCheck,
  Clock3,
  History,
  Info,
  LogIn,
  LogOut,
  RefreshCw,
  ScanLine,
  Search,
  ShieldCheck,
  Users,
  UserSearch,
} from 'lucide-vue-next';
import { useAuth } from '../composables/useAuth';
import {
  attendanceEntry,
  attendanceExit,
  attendanceGet,
} from '../services/attendanceService';
import {
  dateLabel,
  days,
  initials,
  limaDate,
  services,
  shortTime,
  states,
} from '../utils/attendance';
import AttendanceHistory from '../components/attendance/AttendanceHistory.vue';
import '../styles/attendance.css';
const { token } = useAuth();
const tab = ref('today'),
  summary = ref(null),
  dni = ref(''),
  clientData = ref(null),
  lookupError = ref(''),
  error = ref(''),
  feedback = ref('');
const searching = ref(false),
  refreshing = ref(false),
  busy = ref('');
let searchNumber = 0,
  summaryNumber = 0,
  timer;
// Motivo que impide registrar entradas a nivel de cliente (no depende del horario).
const clientBlock = computed(() => {
  const data = clientData.value;
  if (!data) return '';
  if (data.cliente.estado !== 'ACTIVO')
    return 'La cuenta del cliente no está activada. Confirma su pago y activa su membresía desde el módulo Clientes.';
  if (!data.membresia)
    return 'El cliente no tiene una membresía activa, pagada y vigente. Revisa su membresía en el módulo Clientes.';
  return '';
});
const todayName = () =>
  new Date(
    `${clientData.value?.fecha || limaDate()}T12:00:00`,
  ).toLocaleDateString('es-PE', { weekday: 'long' });
// Explica con días y horas concretos por qué el botón está inhabilitado.
const blockedText = (item) =>
  !item.hoy && item.motivo?.includes('no corresponde a hoy')
    ? `Esta clase es el ${String(days[item.dia] || item.dia).toLowerCase()} de ${shortTime(item.hora_inicio)} a ${shortTime(item.hora_fin)}. Hoy es ${todayName()}, así que todavía no se puede registrar la entrada.`
    : item.motivo;
// Los horarios de hoy van primero; los de otros días quedan a un clic.
const showAllSchedules = ref(false);
const todaySchedules = computed(() =>
  (clientData.value?.horarios || []).filter((item) => item.hoy),
);
const visibleSchedules = computed(() => {
  const all = clientData.value?.horarios || [];
  return showAllSchedules.value || !todaySchedules.value.length
    ? all
    : todaySchedules.value;
});
const hiddenSchedules = computed(
  () => (clientData.value?.horarios.length || 0) - visibleSchedules.value.length,
);
const canToggleSchedules = computed(
  () =>
    todaySchedules.value.length > 0 &&
    (clientData.value?.horarios.length || 0) > todaySchedules.value.length,
);
const handleTabKey = async (event) => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault();
  const tablist = event.currentTarget;
  tab.value =
    event.key === 'Home'
      ? 'today'
      : event.key === 'End'
        ? 'history'
        : tab.value === 'today'
          ? 'history'
          : 'today';
  await nextTick();
  tablist.querySelector('[aria-selected="true"]')?.focus();
};
const clearClient = () => {
  searchNumber++;
  searching.value = false;
  clientData.value = null;
  lookupError.value = '';
  feedback.value = '';
  showAllSchedules.value = false;
};
const lookupClient = async () => {
  if (!/^\d{8}$/.test(dni.value)) {
    lookupError.value = 'Ingresa un DNI de 8 dígitos.';
    return;
  }
  const request = ++searchNumber;
  const query = dni.value;
  searching.value = true;
  lookupError.value = '';
  clientData.value = null;
  try {
    const data = await attendanceGet('/cliente', { dni: query }, token.value);
    if (request === searchNumber) clientData.value = data;
  } catch (err) {
    if (request === searchNumber) lookupError.value = err.message;
  } finally {
    if (request === searchNumber) searching.value = false;
  }
};
const loadSummary = async () => {
  const request = ++summaryNumber;
  refreshing.value = true;
  try {
    const data = await attendanceGet('/resumen', {}, token.value);
    if (request === summaryNumber) summary.value = data;
  } catch (err) {
    if (request === summaryNumber) {
      summary.value = null;
      throw err;
    }
  } finally {
    if (request === summaryNumber) refreshing.value = false;
  }
};
const refresh = async () => {
  error.value = '';
  const results = await Promise.allSettled([
    loadSummary(),
    ...(clientData.value ? [lookupClient()] : []),
  ]);
  results.forEach((result) => {
    if (result.status === 'rejected') error.value = result.reason.message;
  });
};
const mutate = async (key, action, message) => {
  if (busy.value) return;
  busy.value = key;
  error.value = '';
  feedback.value = '';
  try {
    await action();
    feedback.value = message;
    await refresh();
  } catch (err) {
    error.value = err.message;
    if (clientData.value) await lookupClient();
  } finally {
    busy.value = '';
  }
};
const enter = (item) =>
  mutate(
    `entry-${item.id_matricula}`,
    () => attendanceEntry(item.id_matricula, token.value),
    'Entrada registrada correctamente.',
  );
const exitRecord = (record) =>
  mutate(
    `exit-${record.id_asistencia}`,
    () => attendanceExit(record.id_asistencia, token.value),
    'Salida registrada correctamente.',
  );
onMounted(() => {
  refresh();
  timer = setInterval(() => {
    if (
      !document.hidden &&
      !busy.value &&
      !searching.value &&
      !refreshing.value
    )
      refresh();
  }, 60000);
});
onUnmounted(() => {
  clearInterval(timer);
  searchNumber++;
  summaryNumber++;
});
</script>

<style scoped>
.att-blocked-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 12px 0 0;
  padding: 10px 12px;
  border: 1px solid #f0c98f;
  border-radius: 10px;
  background: #fff6e8;
  color: #7a4b00;
  font-size: 0.9rem;
  line-height: 1.4;
}
.att-blocked-reason svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* Más aire entre bloques y columnas que no se desbordan */
.att-control-grid {
  gap: 24px;
}
.att-control-grid > * {
  min-width: 0;
}
.att-membership {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px 24px;
}
.att-schedule-bottom {
  gap: 12px;
}
.att-schedule-toggle {
  display: block;
  margin: 12px auto 0;
  padding: 8px 12px;
}

/* Tablet: el panel de "Entradas sin salida" pasa debajo de la búsqueda */
@media (max-width: 1100px) {
  .att-control-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* Celular */
@media (max-width: 720px) {
  .att-page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .att-header-tools {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  .att-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }
  .att-metric {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 12px;
  }
  .att-metric small {
    display: none;
  }
  .att-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .att-toolbar > span {
    display: none;
  }
  .att-tabs {
    display: flex;
    width: 100%;
  }
  .att-tabs button {
    flex: 1;
    justify-content: center;
    min-height: 44px;
  }
  .att-search {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }
  .att-search-input input {
    font-size: 16px;
  }
  .att-button {
    min-height: 44px;
  }
  .att-search .att-button,
  .att-schedule-bottom .att-button {
    width: 100%;
    justify-content: center;
  }
  .att-client-card {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }
  .att-client-card > div {
    flex: 1 1 140px;
    min-width: 0;
  }
  .att-membership {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }
  .att-schedule-bottom {
    flex-direction: column;
    align-items: stretch;
  }
  .att-visittimes {
    display: flex;
    justify-content: space-between;
  }
  .att-person-bottom {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
