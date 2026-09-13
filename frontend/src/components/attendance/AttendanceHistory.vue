<template>
  <section class="att-panel">
    <div class="att-heading-row">
      <div>
        <p class="att-eyebrow">Todas las visitas</p>
        <h2>Historial de asistencia</h2>
        <p class="att-muted">Consulta por fecha, servicio y estado.</p>
      </div>
      <button
        class="att-button"
        :disabled="loading || exporting || !total"
        @click="exportRecords"
      >
        <Download :size="16" />{{
          exporting ? 'Exportando…' : 'Exportar Excel'
        }}
      </button>
    </div>
    <form class="att-filters" @submit.prevent="apply">
      <label v-if="admin"
        >DNI del cliente<input
          v-model="draft.dni"
          inputmode="numeric"
          maxlength="8"
          pattern="[0-9]{8}"
          placeholder="8 dígitos"
      /></label>
      <label
        >Desde<input
          v-model="draft.desde"
          type="date"
          :max="draft.hasta || undefined"
      /></label>
      <label
        >Hasta<input
          v-model="draft.hasta"
          type="date"
          :min="draft.desde || undefined"
      /></label>
      <label
        >Servicio<select v-model="draft.servicio">
          <option value="">Todos</option>
          <option v-for="(label, key) in services" :key="key" :value="key">
            {{ label }}
          </option>
        </select></label
      >
      <label
        >Estado<select v-model="draft.estado">
          <option value="">Todos</option>
          <option value="dentro">Dentro</option>
          <option value="completada">Completada</option>
          <option v-if="admin" value="anulada">Anulada</option>
        </select></label
      >
      <button class="att-button att-primary" :disabled="loading">Filtrar</button
      ><button
        class="att-link"
        type="button"
        :disabled="loading"
        @click="reset"
      >
        Limpiar
      </button>
    </form>
    <p v-if="error" role="alert" class="att-message is-error">
      {{ error }} <button class="att-link" @click="load">Reintentar</button>
    </p>
    <p v-if="notice" role="status" class="att-message is-success">
      {{ notice }}
    </p>
    <div class="att-table-wrap" :aria-busy="loading">
      <table class="att-table">
        <caption class="att-sr-only">
          Registros de asistencia filtrados
        </caption>
        <thead>
          <tr>
            <th v-if="admin">Cliente</th>
            <th>Fecha / servicio</th>
            <th>Entrada</th>
            <th>Salida</th>
            <th>Estado</th>
            <th v-if="admin">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in records" :key="record.id_asistencia">
            <td v-if="admin" data-label="Cliente">
              <strong>{{ record.cliente_nombre }}</strong
              ><small>DNI {{ record.cliente_dni || 'sin registrar' }}</small>
            </td>
            <td data-label="Fecha / servicio">
              <strong>{{ dateLabel(record.fecha) }}</strong
              ><small>{{ services[record.servicio] || record.servicio }}</small>
            </td>
            <td class="att-time" data-label="Entrada">
              {{ shortTime(record.hora_entrada || record.hora) }}
            </td>
            <td class="att-time" data-label="Salida">
              {{ shortTime(record.hora_salida)
              }}<small
                v-if="
                  record.fecha_salida && record.fecha_salida !== record.fecha
                "
                >{{ dateLabel(record.fecha_salida) }}</small
              >
            </td>
            <td data-label="Estado">
              <span class="att-badge" :class="record.estado">{{
                states[record.estado]
              }}</span>
            </td>
            <td v-if="admin" data-label="Acciones">
              <div v-if="!record.anulado" class="att-row-actions">
                <button
                  class="att-link"
                  :aria-label="`Corregir asistencia de ${record.cliente_nombre}`"
                  @click="edit(record, false)"
                >
                  <Pencil :size="14" />Corregir</button
                ><button
                  class="att-link att-danger"
                  :aria-label="`Anular asistencia de ${record.cliente_nombre}`"
                  @click="edit(record, true)"
                >
                  Anular
                </button>
              </div>
              <details v-else class="att-small">
                <summary>Ver motivo</summary>
                <p
                  v-for="(event, index) in record.auditoria?.filter(
                    (e) => e.accion === 'anulacion',
                  )"
                  :key="index"
                >
                  {{ event.motivo }} · {{ event.actor_nombre }} ·
                  {{ dateLabel(event.fecha) }}
                </p>
              </details>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="loading" class="att-empty" role="status">
      Cargando asistencias…
    </div>
    <div v-else-if="!records.length && !error" class="att-empty">
      <CalendarSearch :size="30" />
      <h3>No hay visitas con estos filtros</h3>
      <p>Prueba otro rango de fechas o limpia los filtros.</p>
    </div>
    <div class="att-pagination">
      <span>{{ total }} registros · Página {{ page }} de {{ pages }}</span>
      <div class="att-row-actions">
        <button
          class="att-button"
          :disabled="loading || page <= 1"
          aria-label="Página anterior"
          @click="changePage(-1)"
        >
          <ChevronLeft :size="16" /></button
        ><button
          class="att-button"
          :disabled="loading || page >= pages"
          aria-label="Página siguiente"
          @click="changePage(1)"
        >
          <ChevronRight :size="16" />
        </button>
      </div>
    </div>
    <AttendanceCorrectionDialog
      v-if="selected"
      :record="selected"
      :annulling="annulling"
      @close="selected = null"
      @saved="saved"
    />
  </section>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import * as XLSX from 'xlsx';
import {
  CalendarSearch,
  ChevronLeft,
  ChevronRight,
  Download,
  Pencil,
} from 'lucide-vue-next';
import { useAuth } from '../../composables/useAuth';
import { attendanceGet } from '../../services/attendanceService';
import { dateLabel, services, shortTime, states } from '../../utils/attendance';
import AttendanceCorrectionDialog from './AttendanceCorrectionDialog.vue';
const props = defineProps({ admin: Boolean });
const emit = defineEmits(['changed']);
const { token } = useAuth();
const emptyFilters = () => ({
  dni: '',
  desde: '',
  hasta: '',
  servicio: '',
  estado: '',
});
const draft = reactive(emptyFilters()),
  active = ref(emptyFilters());
const records = ref([]),
  total = ref(0),
  page = ref(1),
  loading = ref(false),
  exporting = ref(false),
  error = ref(''),
  notice = ref('');
const selected = ref(null),
  annulling = ref(false);
const pages = computed(() => Math.max(1, Math.ceil(total.value / 15)));
let requestNumber = 0;
const load = async () => {
  const request = ++requestNumber;
  loading.value = true;
  error.value = '';
  records.value = [];
  try {
    const data = await attendanceGet(
      '/historial',
      { ...active.value, page: page.value, page_size: 15 },
      token.value,
    );
    if (request !== requestNumber) return;
    const lastPage = Math.max(1, Math.ceil(data.total / 15));
    if (page.value > lastPage) {
      page.value = lastPage;
      await load();
      return;
    }
    records.value = data.items;
    total.value = data.total;
  } catch (err) {
    if (request === requestNumber) {
      error.value = err.message;
      total.value = 0;
    }
  } finally {
    if (request === requestNumber) loading.value = false;
  }
};
const apply = () => {
  active.value = { ...draft, dni: props.admin ? draft.dni.trim() : '' };
  page.value = 1;
  notice.value = '';
  load();
};
const reset = () => {
  Object.assign(draft, emptyFilters());
  apply();
};
const changePage = (delta) => {
  page.value += delta;
  load();
};
const edit = (record, annul) => {
  annulling.value = annul;
  selected.value = record;
};
const saved = () => {
  notice.value = annulling.value
    ? 'Asistencia anulada. El motivo quedó guardado.'
    : 'Corrección guardada.';
  emit('changed');
  load();
};
const exportRecords = async () => {
  if (exporting.value) return;
  exporting.value = true;
  error.value = '';
  try {
    const filters = { ...active.value };
    const rows = await attendanceGet('/exportar', filters, token.value);
    const sheet = XLSX.utils.json_to_sheet(
      rows.map((r) => ({
        ...(props.admin
          ? { Cliente: r.cliente_nombre, DNI: r.cliente_dni }
          : {}),
        Fecha: r.fecha,
        Servicio: services[r.servicio] || r.servicio,
        Entrada: r.hora_entrada || r.hora,
        Salida: r.hora_salida || '',
        'Fecha de salida': r.hora_salida ? r.fecha_salida || r.fecha : '',
        Estado: states[r.estado],
        'Zona horaria': 'America/Lima',
      })),
    );
    sheet['!cols'] = Array(props.admin ? 9 : 7).fill({ wch: 24 });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, sheet, 'Asistencias');
    XLSX.writeFile(workbook, 'asistencias.xlsx');
    notice.value = `Se exportaron ${rows.length} registros con los filtros aplicados.`;
  } catch (err) {
    error.value = err.message;
  } finally {
    exporting.value = false;
  }
};
onMounted(load);
defineExpose({ reload: load });
</script>
