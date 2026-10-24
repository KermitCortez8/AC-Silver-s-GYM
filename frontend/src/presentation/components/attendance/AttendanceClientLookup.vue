<template>
  <section class="att-panel att-lookup-panel">
    <div class="att-heading-row">
      <div>
        <p class="att-eyebrow">
          {{ isGeneral ? 'Gimnasio general' : 'Asistencia por horario' }}
        </p>
        <h2>{{ clientData ? 'Registrar visita' : 'Buscar cliente' }}</h2>
        <p class="att-muted att-small">
          {{
            isGeneral
              ? 'Registra el acceso al gimnasio con una membresía vigente.'
              : 'Registra la asistencia a una clase matriculada.'
          }}
        </p>
      </div>
      <span class="att-soft-icon"><UserSearch :size="22" /></span>
    </div>
    <div class="att-viewport">
      <div class="att-slider" :class="{ 'at-result': Boolean(clientData) }">
        <div class="att-slide att-slide-search" :inert="Boolean(clientData)">
          <form class="att-search" @submit.prevent="$emit('search')">
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
                  @input="$emit('input')"
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
              Encuentra al cliente, revisa su membresía<br />y
              {{
                isGeneral
                  ? 'registra su entrada al gimnasio.'
                  : 'registra la visita en su horario.'
              }}
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
            @click="$emit('back')"
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
            <AttendanceGeneralVisit
              v-if="isGeneral"
              :client-data="clientData"
              :client-block="clientBlock"
              :busy="busy"
              :saved-key="savedKey"
              @entry="$emit('general-entry')"
              @exit="$emit('exit', $event)"
            />
            <AttendanceSchedules
              v-else
              :client-data="clientData"
              :client-block="clientBlock"
              :busy="busy"
              :saved-key="savedKey"
              @entry="$emit('entry', $event)"
              @exit="$emit('exit', $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import {
  ArrowLeft,
  ArrowRight,
  Clock3,
  ScanLine,
  Search,
  UserSearch,
} from 'lucide-vue-next';
import { initials, dateLabel } from '../../utils/attendance.js';
import AttendanceGeneralVisit from './AttendanceGeneralVisit.vue';
import AttendanceSchedules from './AttendanceSchedules.vue';
const props = defineProps({
  clientData: Object,
  isGeneral: Boolean,
  searching: Boolean,
  lookupError: String,
  busy: String,
  savedKey: String,
});
defineEmits(['search', 'input', 'back', 'entry', 'general-entry', 'exit']);
const dni = defineModel('dni', { type: String, default: '' });
const dniInput = ref(null),
  resultBack = ref(null);
const clientBlock = computed(() => {
  const data = props.clientData;
  if (!data) return '';
  if (data.cliente.estado !== 'ACTIVO')
    return 'La cuenta del cliente no está activada. Confirma su pago y activa su membresía desde el módulo Clientes.';
  if (!data.membresia)
    return 'El cliente no tiene una membresía activa, pagada y vigente. Revisa su membresía en el módulo Clientes.';
  return '';
});
watch(
  () => props.clientData,
  async (data, previous) => {
    await nextTick();
    if (data && !previous) resultBack.value?.focus();
    else if (!data && previous) dniInput.value?.focus();
  },
);
</script>
