<template>
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
  <div
    v-if="summary"
    class="att-capacity"
    :class="{ 'is-full': !summary.disponibles }"
  >
    <div class="att-capacity-label">
      <Users :size="17" />
      <span
        ><strong>{{
          summary.disponibles
            ? `${summary.disponibles} lugares disponibles`
            : 'Aforo completo'
        }}</strong>
        <small
          >{{ summary.dentro }} de {{ summary.capacidad }} personas · Incluye
          visitas generales y por horario</small
        >
      </span>
    </div>
    <progress
      :value="summary.dentro"
      :max="summary.capacidad"
      aria-label="Ocupación del gimnasio"
    />
  </div>
</template>
<script setup>
import { LogIn, LogOut, Users } from 'lucide-vue-next';
defineProps({ summary: Object, refreshing: Boolean });
</script>
