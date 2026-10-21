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
    <div v-if="summary" class="att-capacity" :class="{ 'is-full': !summary.disponibles }">
      <div class="att-capacity-label">
        <Users :size="17" />
        <span><strong>{{ summary.disponibles ? `${summary.disponibles} lugares disponibles` : 'Aforo completo' }}</strong>
          <small>{{ summary.dentro }} de {{ summary.capacidad }} personas · Incluye visitas generales y por horario</small>
        </span>
      </div>
      <progress :value="summary.dentro" :max="summary.capacidad" aria-label="Ocupación del gimnasio" />
    </div>
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
          :aria-controls="item.key === 'history' ? 'history-panel' : 'control-panel'"
          @click="tab = item.key"
        >
          <component :is="item.icon" :size="16" />{{ item.label }}
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
      v-show="tab !== 'history'"
      id="control-panel"
      role="tabpanel"
      :aria-labelledby="`${tab}-tab`"
      class="att-control-grid"
    >
      <section class="att-panel att-lookup-panel">
        <div class="att-heading-row">
          <div>
            <p class="att-eyebrow">{{ isGeneral ? 'Gimnasio general' : 'Asistencia por horario' }}</p>
            <h2>{{ clientData ? 'Registrar visita' : 'Buscar cliente' }}</h2>
            <p class="att-muted att-small">{{ isGeneral ? 'Registra el acceso al gimnasio con una membresía vigente.' : 'Registra la asistencia a una clase matriculada.' }}</p>
          </div>
          <span class="att-soft-icon"><UserSearch :size="22" /></span>
        </div>
        <div class="att-viewport">
        <div class="att-slider" :class="{ 'at-result': Boolean(clientData) }">
          <div class="att-slide att-slide-search" :inert="Boolean(clientData)">
            <form class="att-search" @submit.prevent="lookupClient()">
              <label for="attendance-dni"
                >DNI del cliente
                <div class="att-search-input">
                  <Search :size="18" /><input
                    id="attendance-dni"
                    ref="dniInput"
                    v-model="dni"
                    inputmode="numeric"
                    autocomplete="off"
                    maxlength="8"
                    pattern="[0-9]{8}"
                    required
                    placeholder="Ingresa los 8 dígitos"
                    @input="onDniInput"
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
            <div
              v-if="!clientData && !searching && !lookupError"
              class="att-empty att-search-empty"
            >
              <span class="att-empty-illustration"><ScanLine :size="38" /></span>
              <h3>Todo comienza con el DNI</h3>
              <p>
                Encuentra al cliente, revisa su membresía<br />y {{ isGeneral ? 'registra su entrada al gimnasio.' : 'registra la visita en su horario.' }}
              </p>
              <span class="att-muted att-small"
                ><Clock3 :size="14" />Fecha y hora de Perú</span
              >
            </div>
          </div>
          <div class="att-slide att-slide-result" :inert="!clientData">
            <button
              ref="resultBack"
              type="button"
              class="att-back"
              @click="backToSearch"
            >
              <ArrowLeft :size="15" />Buscar otro cliente
            </button>
            <div v-if="clientData" class="att-client-result">
              <div class="att-ficha">
                <span class="att-avatar">{{
                  initials(clientData.cliente.nombre)
                }}</span>
                <div class="att-ficha-body">
                  <h3>{{ clientData.cliente.nombre }}</h3>
                  <p class="att-muted">
                    DNI {{ clientData.cliente.dni }} ·
                    {{
                      clientData.cliente.plan
                        ? `Plan ${clientData.cliente.plan}`
                        : 'Sin plan'
                    }}
                  </p>
                  <div class="att-chips">
                    <span
                      class="att-badge"
                      :class="clientData.membresia ? 'completada' : 'anulada'"
                      >{{
                        clientData.membresia
                          ? `Membresía hasta ${dateLabel(clientData.membresia.fecha_fin)}`
                          : 'Sin membresía activa y pagada'
                      }}</span
                    ><span
                      class="att-badge"
                      :class="
                        clientData.cliente.estado === 'ACTIVO'
                          ? 'completada'
                          : 'anulada'
                      "
                      >{{
                        clientData.cliente.estado === 'ACTIVO'
                          ? 'Cuenta activada'
                          : 'Cuenta sin activar'
                      }}</span
                    >
                  </div>
                </div>
              </div>
              <p v-if="clientBlock" class="att-message is-error" role="alert">
                <strong>No se puede registrar la entrada.</strong>
                {{ clientBlock }}
              </p>
              <div v-if="isGeneral" class="att-general-visit">
                <div class="att-heading-row">
                  <div>
                    <h3>{{ openVisit ? 'El cliente ya está dentro' : 'Una visita a su ritmo' }}</h3>
                    <p class="att-muted att-small">{{ openVisit ? 'Registra su salida antes de abrir otra visita.' : 'Acceso general sin seleccionar un horario. La hora se guarda automáticamente.' }}</p>
                  </div>
                  <span class="att-soft-icon"><Users :size="22" /></span>
                </div>
                <article v-if="openVisit" class="att-row is-inside" :class="{ 'is-saved': savedKey === `exit-${openVisit.id_asistencia}` }">
                  <div class="att-row-main">
                    <h4>{{ services[openVisit.servicio] || openVisit.servicio }}</h4>
                    <p class="att-muted">Entrada {{ shortTime(openVisit.hora_entrada || openVisit.hora) }} · {{ dateLabel(openVisit.fecha) }}</p>
                    <span class="att-badge dentro">Dentro del gimnasio</span>
                  </div>
                  <button class="att-button att-primary" :disabled="Boolean(busy)" @click="exitRecord(openVisit)">
                    <LogOut :size="16" />{{ busy === `exit-${openVisit.id_asistencia}` ? 'Guardando…' : 'Registrar salida' }}
                  </button>
                </article>
                <template v-else>
                  <p v-if="clientData.general?.motivo && !clientBlock" class="att-blocked-reason" role="status">
                    <Info :size="16" />{{ clientData.general.motivo }}
                  </p>
                  <button class="att-button att-primary att-general-entry" :disabled="!clientData.general?.puede_entrar || Boolean(busy)" @click="enterGeneral">
                    <LogIn :size="17" />{{ busy === 'general-entry' ? 'Guardando…' : 'Registrar entrada al gimnasio' }}
                  </button>
                  <p class="att-muted att-small">Puedes registrar otra visita el mismo día después de cerrar la anterior.</p>
                </template>
              </div>
              <template v-else>
              <div class="att-heading-row att-schedule-heading">
                <h3>
                  {{
                    showAllSchedules || !todaySchedules.length
                      ? 'Horarios matriculados'
                      : 'Horarios de hoy'
                  }}
                </h3>
                <span class="att-muted att-small"
                  >{{
                    visibleSchedules.length === clientData.horarios.length
                      ? `${clientData.horarios.length} horario${clientData.horarios.length === 1 ? '' : 's'}`
                      : `${visibleSchedules.length} de ${clientData.horarios.length} horarios`
                  }}</span
                >
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
                      >{{
                        item.asistencia ? states[item.asistencia.estado] : 'Hoy'
                      }}</span
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
            </div>
          </div>
        </div>
        </div>
      </section>
      <aside class="att-panel att-inside-panel">
        <div class="att-heading-row">
          <div>
            <p class="att-eyebrow">En este momento</p>
            <h2>{{ isGeneral ? 'Visitas generales sin salida' : 'Horarios sin salida' }}</h2>
          </div>
          <span class="att-count">{{
            summary ? pendingSorted.length : '—'
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
        <div v-else-if="!pendingSorted.length" class="att-empty">
          <CircleCheck :size="30" />
          <h3>Todo al día</h3>
          <p>No hay entradas pendientes de salida.</p>
        </div>
        <div v-else class="att-inside-list">
          <article
            v-for="record in pendingSorted"
            :key="record.id_asistencia"
            class="att-person"
            :class="{ 'is-overdue': record.fecha !== summary.fecha }"
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
                >{{ services[record.servicio] || record.servicio
                }}<small
                  >Entrada {{ shortTime(record.hora_entrada || record.hora)
                  }}<span
                    v-if="record.fecha !== summary.fecha"
                    class="att-overdue"
                  >
                    · {{ dateLabel(record.fecha) }}</span
                  ><span v-if="elapsed(record)" class="att-elapsed">
                    · {{ elapsed(record) }}</span
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
            {{ isGeneral ? 'Las visitas generales requieren cuenta activada y membresía pagada y vigente.' : 'Las entradas por horario requieren cuenta activada, membresía vigente y horario habilitado.' }}
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
  ArrowLeft,
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
  generalAttendanceEntry,
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
const attendanceTabs = [
  { key: 'today', label: 'Por horarios', icon: ScanLine },
  { key: 'general', label: 'Gimnasio general', icon: Users },
  { key: 'history', label: 'Historial', icon: History },
];
const tab = ref('today'),
  summary = ref(null),
  dni = ref(''),
  clientData = ref(null),
  lookupError = ref(''),
  error = ref(''),
  feedback = ref('');
const isGeneral = computed(() => tab.value === 'general');
const openVisit = computed(() => clientData.value?.general?.asistencia_abierta);
const generalRequests = new Map();
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
  const keys = attendanceTabs.map((item) => item.key);
  const index = keys.indexOf(tab.value);
  tab.value = event.key === 'Home' ? keys[0]
    : event.key === 'End' ? keys.at(-1)
    : keys[(index + (event.key === 'ArrowRight' ? 1 : -1) + keys.length) % keys.length];
  await nextTick();
  tablist.querySelector('[aria-selected="true"]')?.focus();
};
const dniInput = ref(null);
const resultBack = ref(null);
const savedKey = ref('');
const now = ref(Date.now());
const clearClient = () => {
  searchNumber++;
  searching.value = false;
  clientData.value = null;
  lookupError.value = '';
  feedback.value = '';
  showAllSchedules.value = false;
};
// Solo dígitos; al completar los 8 dígitos busca automáticamente.
const onDniInput = () => {
  dni.value = dni.value.replace(/\D/g, '').slice(0, 8);
  clearClient();
  if (dni.value.length === 8) lookupClient();
};
// Vuelve a la vista de búsqueda (el riel se desliza) y deja el campo listo para escribir.
const backToSearch = () => {
  clearClient();
  dni.value = '';
  nextTick(() => dniInput.value?.focus());
};
// silent = true: actualiza la ficha ya abierta SIN vaciarla (evita que la pantalla
// vuelva a "Buscar cliente" y parpadee después de guardar o en cada refresco).
const lookupClient = async ({ silent = false } = {}) => {
  const query = silent ? clientData.value?.cliente?.dni : dni.value;
  if (!/^\d{8}$/.test(query || '')) {
    if (!silent) lookupError.value = 'Ingresa un DNI de 8 dígitos.';
    return;
  }
  const request = silent ? searchNumber : ++searchNumber;
  if (!silent) {
    searching.value = true;
    lookupError.value = '';
    clientData.value = null;
  }
  try {
    const data = await attendanceGet('/cliente', { dni: query }, token.value);
    if (request === searchNumber) {
      clientData.value = data;
      if (!silent) {
        await nextTick();
        resultBack.value?.focus();
      }
    }
  } catch (err) {
    if (request === searchNumber) {
      const text = err?.message || 'No se pudo consultar al cliente.';
      if (silent) error.value = `No se pudo actualizar la ficha. ${text}`;
      else lookupError.value = text;
    }
  } finally {
    if (request === searchNumber && !silent) searching.value = false;
  }
};
const loadSummary = async () => {
  const request = ++summaryNumber;
  refreshing.value = true;
  try {
    const data = await attendanceGet('/resumen', {}, token.value);
    if (request === summaryNumber) summary.value = data;
  } catch (err) {
    // Se conserva el último resumen cargado; solo se avisa del error.
    if (request === summaryNumber) throw err;
  } finally {
    if (request === summaryNumber) refreshing.value = false;
  }
};
const refresh = async () => {
  error.value = '';
  const results = await Promise.allSettled([
    loadSummary(),
    ...(clientData.value ? [lookupClient({ silent: true })] : []),
  ]);
  results.forEach((result) => {
    if (result.status === 'rejected')
      error.value = result.reason?.message || 'No se pudo actualizar.';
  });
};
let feedbackTimer;
const mutate = async (key, action, message) => {
  if (busy.value) return;
  busy.value = key;
  error.value = '';
  feedback.value = '';
  savedKey.value = '';
  clearTimeout(feedbackTimer);
  try {
    await action();
    feedback.value = message;
    savedKey.value = key;
    feedbackTimer = setTimeout(() => {
      feedback.value = '';
      savedKey.value = '';
    }, 4000);
    await refresh();
  } catch (err) {
    const message =
      err?.message || 'No se pudo guardar. Revisa tu conexión e inténtalo de nuevo.';
    // Relee resumen y ficha (p. ej. tras un conflicto 409) y conserva el mensaje del error.
    await refresh();
    error.value = message;
  } finally {
    busy.value = '';
  }
};
// Resalta por unos segundos la fila que se acaba de guardar.
const isSaved = (item) =>
  savedKey.value === `entry-${item.id_matricula}` ||
  Boolean(
    item.asistencia && savedKey.value === `exit-${item.asistencia.id_asistencia}`,
  );
// Entradas sin salida: primero las más antiguas (las más urgentes de revisar).
const pendingSorted = computed(() => {
  const at = (r) => `${r.fecha}${r.hora_entrada || r.hora || ''}`;
  return (summary.value?.pendientes || []).filter((r) =>
    isGeneral.value ? r.tipo === 'general' : r.tipo !== 'general',
  ).sort((a, b) =>
    at(a).localeCompare(at(b)),
  );
});
// "hace 2 h 15 min" desde la entrada (hora de Perú, UTC-5).
const elapsed = (record) => {
  const time = String(record.hora_entrada || record.hora || '').slice(0, 8);
  const date = String(record.fecha || '').slice(0, 10);
  const start = new Date(`${date}T${time}-05:00`).getTime();
  if (!date || !time || Number.isNaN(start)) return '';
  const minutes = Math.max(0, Math.floor((now.value - start) / 60000));
  if (minutes < 1) return 'recién';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `hace ${h} h${m ? ` ${m} min` : ''}` : `hace ${m} min`;
};
const enter = (item) =>
  mutate(
    `entry-${item.id_matricula}`,
    () => attendanceEntry(item.id_matricula, token.value),
    'Entrada registrada correctamente.',
  );
const enterGeneral = () => {
  const clientDni = clientData.value?.cliente.dni;
  if (!clientDni || !clientData.value?.general?.puede_entrar) return;
  if (!generalRequests.has(clientDni)) generalRequests.set(clientDni, crypto.randomUUID());
  return mutate('general-entry', async () => {
    await generalAttendanceEntry(clientDni, generalRequests.get(clientDni), token.value);
    generalRequests.delete(clientDni);
  }, 'Entrada general registrada correctamente. ¡Buen entrenamiento!');
};
const exitRecord = (record) =>
  mutate(
    `exit-${record.id_asistencia}`,
    async () => {
      await attendanceExit(record.id_asistencia, token.value);
      // Una visita cerrada permite iniciar un nuevo intento de entrada.
      if (record.tipo === 'general') generalRequests.delete(record.cliente_dni);
    },
    'Salida registrada correctamente.',
  );
onMounted(() => {
  refresh();
  timer = setInterval(() => {
    now.value = Date.now();
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
  clearTimeout(feedbackTimer);
  searchNumber++;
  summaryNumber++;
});
</script>

<style scoped>
/* Aviso ámbar: explica por qué no se puede registrar */
.att-blocked-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--att-warm);
  border-radius: 10px;
  background: var(--att-warm-bg);
  color: var(--att-warm);
  font-size: 0.9rem;
  line-height: 1.4;
}
.att-blocked-reason svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* Espacio uniforme entre los bloques de la pantalla */
.att-control-grid {
  gap: 24px;
}
.att-control-grid > * {
  min-width: 0;
}
.att-client-result {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.att-client-result > * {
  margin-top: 0;
  margin-bottom: 0;
}

/* Ficha del cliente: nombre, datos clave y estados en un solo bloque */
.att-ficha {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--app-border);
}
.att-ficha-body {
  min-width: 0;
}
.att-ficha-body h3 {
  margin: 0;
}
.att-ficha-body > p {
  margin: 2px 0 10px;
}
.att-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Cada horario es una fila: qué clase, cuándo y qué acción */
.att-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px 16px;
  padding: 14px 16px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  background: var(--app-surface);
}
.att-row.is-today {
  background: var(--app-surface-soft);
  border-color: var(--app-border-strong);
}
.att-row-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.att-row-title h4 {
  margin: 0;
}
.att-row-main p {
  margin: 2px 0 0;
}
.att-row-action {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
}
.att-row-times {
  margin: 0;
  font-size: 0.85rem;
  white-space: nowrap;
}
.att-row-note {
  grid-column: 1 / -1;
}
.att-schedule-toggle {
  display: block;
  margin: 0 auto;
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
    overflow-x: auto;
  }
  .att-tabs button {
    flex: 1;
    justify-content: center;
    min-height: 44px;
    white-space: nowrap;
    padding: 10px;
    font-size: 11px;
    gap: 5px;
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
  .att-row-action .att-button {
    width: 100%;
    justify-content: center;
  }
  .att-row {
    grid-template-columns: minmax(0, 1fr);
  }
  .att-row-action {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .att-row-times {
    white-space: normal;
  }
  .att-person-bottom {
    flex-wrap: wrap;
    gap: 8px;
  }
}

/* Más aire en el encabezado, las métricas y la barra de pestañas */
.att-page-header {
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}
.att-metrics {
  gap: 16px;
  margin-bottom: 20px;
}
.att-metric {
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
}
.att-toolbar {
  margin-bottom: 18px;
}
.att-panel {
  padding: 20px;
}

/* Panel "Entradas sin salida": misma respiración que la ficha del cliente */
.att-inside-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.att-person {
  padding: 12px 14px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
}
.att-person-bottom {
  margin-top: 8px;
}
.att-aside-note {
  margin-top: 16px;
}

/* Deslizamiento buscador <-> resultado.
   El recorte se hace en .att-viewport (dentro del contenido del panel, sin su padding),
   así la vista que sale nunca se asoma por los bordes. Cada vista mide exactamente
   el 100% y no hay separación entre ellas. */
.att-viewport {
  overflow: hidden;
  width: 100%;
}
.att-viewport .att-slider {
  display: flex;
  align-items: flex-start;
  gap: 0;
  width: 100%;
  transform: none;
  transition: transform 0.35s ease;
}
.att-viewport .att-slider.at-result {
  transform: translateX(-100%);
}
.att-viewport .att-slide {
  flex: 0 0 100%;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 3px; /* deja espacio al anillo de foco de los campos */
  box-sizing: border-box;
  position: static;
  transform: none;
}
@media (prefers-reduced-motion: reduce) {
  .att-viewport .att-slider {
    transition: none;
  }
}

/* Estado de cada horario: se nota de un vistazo quién está dentro */
.att-row.is-inside {
  border-left: 3px solid var(--att-good);
}
/* Confirmación visual en la fila que se acaba de guardar */
.att-row.is-saved {
  animation: att-saved 1.8s ease-out;
}
@keyframes att-saved {
  from {
    background: var(--att-good-bg);
    box-shadow: 0 0 0 3px var(--att-good);
  }
  to {
    background: var(--app-surface);
    box-shadow: 0 0 0 0 transparent;
  }
}
@media (prefers-reduced-motion: reduce) {
  .att-row.is-saved {
    animation: none;
  }
}
/* Visitas de días anteriores: necesitan revisión */
.att-person.is-overdue {
  border-color: var(--att-warm);
  background: var(--att-warm-bg);
}
.att-elapsed {
  font-variant-numeric: tabular-nums;
}
.att-general-visit {
  display: grid;
  gap: 16px;
  padding: 18px;
  background: var(--app-surface-soft);
  border: 1px solid var(--app-border);
  border-radius: 14px;
}
.att-general-entry {
  width: 100%;
}
.att-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 8px 0;
  border: 0;
  background: transparent;
  color: var(--app-text-soft);
  font-size: 12px;
  cursor: pointer;
}
.att-capacity {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 18px;
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  border-radius: 12px;
}
.att-capacity-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.att-capacity small {
  display: block;
  color: var(--app-text-muted);
  font-size: 11px;
  margin-top: 3px;
}
.att-capacity progress {
  width: 160px;
  height: 8px;
  accent-color: var(--att-good);
  border: 0;
  border-radius: 8px;
  overflow: hidden;
  appearance: none;
  background: var(--app-surface-strong);
}
.att-capacity progress::-webkit-progress-bar {
  background: var(--app-surface-strong);
}
.att-capacity progress::-webkit-progress-value {
  background: var(--att-good);
  border-radius: 8px;
}
.att-capacity progress::-moz-progress-bar {
  background: var(--att-good);
}
.att-capacity.is-full {
  border-color: var(--att-warm);
}
.att-capacity.is-full progress {
  accent-color: var(--att-warm);
}
.att-capacity.is-full progress::-webkit-progress-value {
  background: var(--att-warm);
}
.att-capacity.is-full progress::-moz-progress-bar {
  background: var(--att-warm);
}
@media (max-width: 480px) {
  .att-tabs button svg { display: none; }
  .att-capacity progress { width: 100%; }
}
</style>
