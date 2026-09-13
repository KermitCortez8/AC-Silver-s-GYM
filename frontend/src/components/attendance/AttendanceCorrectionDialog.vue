<template>
  <dialog
    ref="dialog"
    class="att-dialog"
    aria-labelledby="attendance-dialog-title"
    @cancel="cancel"
    @click="backdrop"
  >
    <form class="att-dialog-body" @submit.prevent="save">
      <div class="att-heading-row">
        <div>
          <p class="att-eyebrow">Revisión del registro</p>
          <h2 id="attendance-dialog-title">
            {{ annulling ? 'Anular asistencia' : 'Corregir asistencia' }}
          </h2>
        </div>
        <button
          type="button"
          class="att-icon-button"
          aria-label="Cerrar"
          :disabled="busy"
          @click="close"
        >
          <X :size="20" />
        </button>
      </div>
      <p class="att-muted">
        {{ record.cliente_nombre }} · {{ dateLabel(record.fecha) }} ·
        {{ services[record.servicio] }}
      </p>
      <p v-if="annulling" class="att-notice">
        La visita dejará de contar en la asistencia. El registro y su historial
        de cambios se conservarán.
      </p>
      <div v-else class="att-form-grid">
        <label
          >Fecha de entrada<input
            v-model="form.fecha"
            required
            type="date"
            :max="today"
        /></label>
        <label
          >Hora de entrada<input
            v-model="form.hora_entrada"
            required
            type="time"
            step="1"
        /></label>
        <label
          >Fecha de salida<input
            v-model="form.fecha_salida"
            type="date"
            :min="form.fecha"
            :max="today"
            :required="Boolean(form.hora_salida)"
        /></label>
        <label
          >Hora de salida<input
            v-model="form.hora_salida"
            type="time"
            step="1"
            :required="Boolean(form.fecha_salida)"
        /></label>
      </div>
      <label
        >Motivo {{ annulling ? 'de anulación' : 'de la corrección'
        }}<textarea
          v-model="form.motivo"
          required
          minlength="5"
          maxlength="500"
          rows="3"
          placeholder="Explica qué ocurrió con este registro"
        />
      </label>
      <p class="att-muted att-small">
        Las horas corresponden a Perú. Se guardará quién realizó el cambio.
      </p>
      <p v-if="error" role="alert" class="att-message is-error">{{ error }}</p>
      <details v-if="record.auditoria?.length" class="att-audit">
        <summary>Historial de cambios ({{ record.auditoria.length }})</summary>
        <ol>
          <li v-for="(event, index) in record.auditoria" :key="index">
            <strong
              >{{ actionLabels[event.accion] || event.accion }} ·
              {{ event.actor_nombre }}</strong
            ><small
              >{{ dateLabel(event.fecha) }} ·
              {{ event.fecha?.slice(11, 19) }}</small
            >
            <p v-if="event.motivo">{{ event.motivo }}</p>
            <p v-if="event.antes && event.accion === 'correccion'">
              {{ dateLabel(event.antes.fecha || event.antes.Fecha) }}
              {{ shortTime(event.antes.hora_entrada) }}–{{
                shortTime(event.antes.hora_salida)
              }}
              → {{ dateLabel(event.despues.fecha || event.despues.Fecha) }}
              {{ shortTime(event.despues.hora_entrada) }}–{{
                shortTime(event.despues.hora_salida)
              }}
            </p>
          </li>
        </ol>
      </details>
      <div class="att-dialog-actions">
        <button
          class="att-button"
          type="button"
          :disabled="busy"
          @click="close"
        >
          Cancelar</button
        ><button
          class="att-button att-primary"
          :disabled="busy || form.motivo.trim().length < 5"
        >
          {{
            busy
              ? 'Guardando…'
              : annulling
                ? 'Sí, anular asistencia'
                : 'Guardar corrección'
          }}
        </button>
      </div>
    </form>
  </dialog>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue';
import { X } from 'lucide-vue-next';
import { useAuth } from '../../composables/useAuth';
import {
  attendanceAnnul,
  attendanceCorrect,
} from '../../services/attendanceService';
import {
  dateLabel,
  limaDate,
  services,
  shortTime,
} from '../../utils/attendance';
const props = defineProps({
  record: { type: Object, required: true },
  annulling: Boolean,
});
const emit = defineEmits(['close', 'saved']);
const { token } = useAuth();
const dialog = ref(null),
  busy = ref(false),
  error = ref('');
const today = limaDate();
const actionLabels = {
  entrada: 'Entrada',
  salida: 'Salida',
  correccion: 'Corrección',
  anulacion: 'Anulación',
};
const form = reactive({
  fecha: props.record.fecha,
  hora_entrada: props.record.hora_entrada || props.record.hora,
  hora_salida: props.record.hora_salida || '',
  fecha_salida: props.record.hora_salida
    ? props.record.fecha_salida || props.record.fecha
    : '',
  motivo: '',
});
const close = () => {
  if (!busy.value) {
    dialog.value.close();
    emit('close');
  }
};
const cancel = (event) => {
  event.preventDefault();
  close();
};
const backdrop = (event) => {
  if (event.target === dialog.value) {
    const rect = dialog.value.getBoundingClientRect();
    if (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    )
      close();
  }
};
onMounted(() => dialog.value.showModal());
const save = async () => {
  if (busy.value) return;
  busy.value = true;
  error.value = '';
  try {
    const base = { version: props.record.version, motivo: form.motivo.trim() };
    const saved = props.annulling
      ? await attendanceAnnul(props.record.id_asistencia, base, token.value)
      : await attendanceCorrect(
          props.record.id_asistencia,
          { ...form, ...base, fecha_salida: form.fecha_salida || null },
          token.value,
        );
    emit('saved', saved);
    dialog.value.close();
    emit('close');
  } catch (err) {
    error.value = err.message;
  } finally {
    busy.value = false;
  }
};
</script>
