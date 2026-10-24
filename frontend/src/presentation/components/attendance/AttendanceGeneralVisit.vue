<template>
  <div class="att-general-visit">
    <div class="att-heading-row">
      <div>
        <h3>
          {{
            openVisit ? 'El cliente ya está dentro' : 'Una visita a su ritmo'
          }}
        </h3>
        <p class="att-muted att-small">
          {{
            openVisit
              ? 'Registra su salida antes de abrir otra visita.'
              : 'Acceso general sin seleccionar un horario. La hora se guarda automáticamente.'
          }}
        </p>
      </div>
      <span class="att-soft-icon"><Users :size="22" /></span>
    </div>
    <article
      v-if="openVisit"
      class="att-row is-inside"
      :class="{ 'is-saved': savedKey === `exit-${openVisit.id_asistencia}` }"
    >
      <div class="att-row-main">
        <h4>{{ services[openVisit.servicio] || openVisit.servicio }}</h4>
        <p class="att-muted">
          Entrada {{ shortTime(openVisit.hora_entrada || openVisit.hora) }} ·
          {{ dateLabel(openVisit.fecha) }}
        </p>
        <span class="att-badge dentro">Dentro del gimnasio</span>
      </div>
      <button
        class="att-button att-primary"
        :disabled="Boolean(busy)"
        @click="$emit('exit', openVisit)"
      >
        <LogOut :size="16" />{{
          busy === `exit-${openVisit.id_asistencia}`
            ? 'Guardando…'
            : 'Registrar salida'
        }}
      </button>
    </article>
    <template v-else>
      <p
        v-if="clientData.general?.motivo && !clientBlock"
        class="att-blocked-reason"
        role="status"
      >
        <Info :size="16" />{{ clientData.general.motivo }}
      </p>
      <button
        class="att-button att-primary att-general-entry"
        :disabled="!clientData.general?.puede_entrar || Boolean(busy)"
        @click="$emit('entry')"
      >
        <LogIn :size="17" />{{
          busy === 'general-entry'
            ? 'Guardando…'
            : 'Registrar entrada al gimnasio'
        }}
      </button>
      <p class="att-muted att-small">
        Puedes registrar otra visita el mismo día después de cerrar la anterior.
      </p>
    </template>
  </div>
</template>
<script setup>
import { computed } from 'vue';
import { Users, LogIn, LogOut, Info } from 'lucide-vue-next';
import { services, shortTime, dateLabel } from '../../utils/attendance.js';
const props = defineProps({
  clientData: { type: Object, required: true },
  clientBlock: String,
  busy: String,
  savedKey: String,
});
defineEmits(['entry', 'exit']);
const openVisit = computed(() => props.clientData.general?.asistencia_abierta);
</script>
