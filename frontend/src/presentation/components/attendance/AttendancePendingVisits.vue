<template>
  <aside class="att-panel att-inside-panel">
    <div class="att-heading-row">
      <div>
        <p class="att-eyebrow">En este momento</p>
        <h2>
          {{
            isGeneral ? 'Visitas generales sin salida' : 'Horarios sin salida'
          }}
        </h2>
      </div>
      <span class="att-count">{{ summary ? pendingSorted.length : '—' }}</span>
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
      <button class="att-link" @click="$emit('refresh')">Reintentar</button>
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
              }}<span v-if="record.fecha !== summary.fecha" class="att-overdue">
                · {{ dateLabel(record.fecha) }}</span
              ><span v-if="elapsed(record)" class="att-elapsed">
                · {{ elapsed(record) }}</span
              ></small
            ></span
          ><button
            class="att-button"
            :disabled="Boolean(busy)"
            :aria-label="`Registrar salida de ${record.cliente_nombre}`"
            @click="$emit('exit', record)"
          >
            {{
              busy === `exit-${record.id_asistencia}` ? 'Guardando…' : 'Salida'
            }}<LogOut :size="14" />
          </button>
        </div>
      </article>
    </div>
    <div class="att-aside-note">
      <ShieldCheck :size="18" />
      <p>
        {{
          isGeneral
            ? 'Las visitas generales requieren cuenta activada y membresía pagada y vigente.'
            : 'Las entradas por horario requieren cuenta activada, membresía vigente y horario habilitado.'
        }}
      </p>
    </div>
  </aside>
</template>
<script setup>
import { computed } from 'vue';
import { CircleCheck, Info, LogOut, ShieldCheck } from 'lucide-vue-next';
import {
  initials,
  dateLabel,
  services,
  shortTime,
} from '../../utils/attendance.js';
const props = defineProps({
  summary: Object,
  isGeneral: Boolean,
  refreshing: Boolean,
  busy: String,
  now: Number,
});
defineEmits(['refresh', 'exit']);
const pendingSorted = computed(() => {
  const at = (r) => `${r.fecha}${r.hora_entrada || r.hora || ''}`;
  return (props.summary?.pendientes || [])
    .filter((r) =>
      props.isGeneral ? r.tipo === 'general' : r.tipo !== 'general',
    )
    .sort((a, b) => at(a).localeCompare(at(b)));
});
const elapsed = (record) => {
  const time = String(record.hora_entrada || record.hora || '').slice(0, 8);
  const date = String(record.fecha || '').slice(0, 10);
  const start = new Date(`${date}T${time}-05:00`).getTime();
  if (!date || !time || Number.isNaN(start)) return '';
  const minutes = Math.max(0, Math.floor((props.now - start) / 60000));
  if (minutes < 1) return 'recién';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `hace ${h} h${m ? ` ${m} min` : ''}` : `hace ${m} min`;
};
</script>
