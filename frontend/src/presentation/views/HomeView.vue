<template>
  <div class="workspace-view space-y-6">
    <header class="ws-panel ws-hero ws-toolbar">
      <div>
        <p class="ws-eyebrow">
          {{ isAdmin ? 'Administración · Resumen' : 'Mi gimnasio' }}
        </p>
        <h1 class="ws-title">
          {{
            isAdmin
              ? 'Todo listo para un gran día'
              : `Hola, ${user?.name || 'cliente'}`
          }}
        </h1>
        <p class="ws-description">
          {{
            isAdmin
              ? 'Revisa la actividad del gimnasio y organiza las tareas de tu equipo.'
              : 'Tu membresía, tus clases y tu progreso, en un solo lugar.'
          }}
        </p>
      </div>
      <div class="flex flex-col items-start gap-2">
        <button
          class="ws-btn"
          :disabled="isRefreshing"
          @click="refreshDashboard(true)"
        >
          <RefreshCw :size="16" :class="{ 'ws-spin': isRefreshing }" />{{
            isRefreshing ? 'Actualizando…' : 'Actualizar datos'
          }}
        </button>
        <p v-if="lastUpdated" class="ws-muted text-xs" role="status">
          Actualizado a las {{ lastUpdated }}
        </p>
      </div>
    </header>
    <p
      v-if="refreshError"
      role="alert"
      class="ws-notice ws-tint-danger ws-danger"
    >
      {{ refreshError }}
    </p>

    <nav class="grid gap-3 md:grid-cols-3" aria-label="Accesos rápidos">
      <RouterLink
        v-for="action in quickActions"
        :key="action.to"
        :to="action.to"
        class="ws-action-link"
        ><component :is="action.icon" :size="22" /><span
          ><strong class="text-sm">{{ action.label }}</strong
          ><small>{{ action.detail }}</small></span
        ><ChevronRight :size="18"
      /></RouterLink>
    </nav>

    <section
      class="dashboard-metrics"
      :class="
        isAdmin ? 'dashboard-metrics--admin' : 'dashboard-metrics--client'
      "
      aria-label="Resumen de actividad"
      :aria-busy="isRefreshing"
    >
      <article
        v-for="item in isAdmin ? adminCards : clientCards"
        :key="item.label"
        class="ws-metric"
      >
        <p class="ws-muted text-sm">{{ item.label }}</p>
        <p class="ws-metric-value">{{ item.value }}</p>
        <p class="text-xs font-medium" :class="item.tone">{{ item.detail }}</p>
      </article>
    </section>

    <template v-if="isAdmin">
      <section class="grid gap-5 xl:grid-cols-2">
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Clientes</p>
              <h2 class="ws-heading mt-1">Estado de membresías</h2>
            </div>
            <RouterLink to="/admin/clients" class="ws-btn"
              >Ver clientes <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="members.length" class="chart-box">
            <Doughnut
              :data="membershipChartData"
              :options="doughnutOptions"
              aria-label="Distribución de clientes por estado de membresía"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <UsersRound :size="30" />
            <h3>Aún no hay clientes</h3>
            <p>
              El resumen aparecerá cuando registres a tus primeros clientes.
            </p>
          </div>
          <nav
            v-if="members.length"
            class="mt-4 grid gap-2 sm:grid-cols-3"
            aria-label="Filtrar clientes por membresía"
          >
            <RouterLink
              v-for="segment in membershipSegments"
              :key="segment.key"
              :to="{ path: '/admin/clients', query: { status: segment.key } }"
              class="membership-segment ws-hover"
            >
              <span class="flex items-center gap-2"
                ><span
                  class="h-2 w-2 rounded-full"
                  :style="{ backgroundColor: segment.color }"
                ></span
                >{{ segment.label }}</span
              >
              <strong>{{ segment.count }}</strong>
            </RouterLink>
          </nav>
        </article>
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Cobros de membresías</p>
              <h2 class="ws-heading mt-1">Pagos por origen del cliente</h2>
            </div>
            <RouterLink
              :to="{ path: '/admin/clients', query: { payment: 'PENDIENTE' } }"
              class="ws-btn"
              >Revisar pagos <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="members.length" class="chart-box">
            <Bar
              :data="paymentChartData"
              :options="barOptions"
              aria-label="Clientes con pago confirmado, pendiente o sin información según su origen"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <UsersRound :size="30" />
            <h3>Pagos de tus clientes</h3>
            <p>Los cobros aparecerán aquí cuando registres clientes.</p>
          </div>
          <p class="ws-muted text-sm mt-4">
            {{ clientSummary.pendingPayment }} pendientes de pago ·
            {{ clientSummary.readyToActivate }} con pago confirmado por activar.
          </p>
          <p class="ws-muted text-xs mt-2">
            Un pago confirmado requiere activación para habilitar la membresía.
            Se muestra el último pago de cada cliente.
          </p>
        </article>
      </section>
      <section class="grid gap-5 xl:grid-cols-2">
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Horarios</p>
              <h2 class="ws-heading mt-1">Cupos por servicio</h2>
            </div>
            <RouterLink to="/admin/service-schedules" class="ws-btn"
              >Ver horarios <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="schedules.length" class="chart-box">
            <Bar
              :data="serviceCapacityData"
              :options="barOptions"
              aria-label="Cupos ocupados y disponibles por servicio"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <CalendarDays :size="30" />
            <h3>Organiza tus clases</h3>
            <p>Los horarios registrados aparecerán en este resumen.</p>
          </div>
        </article>
        <article class="ws-panel">
          <p class="ws-eyebrow">Asistencia</p>
          <h2 class="ws-heading mt-1">Últimos 7 días</h2>
          <div class="chart-box">
            <Line
              :data="attendanceTrendData"
              :options="lineOptions"
              aria-label="Asistencias registradas en los últimos siete días"
            />
          </div>
        </article>
      </section>
      <section>
        <article class="ws-panel">
          <p class="ws-eyebrow">Organiza tu día</p>
          <h2 class="ws-heading mt-1">Por revisar</h2>
          <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <RouterLink
              v-for="item in operationalAlerts"
              :key="item.label"
              :to="item.to"
              class="ws-action-link"
              ><div class="flex-1">
                <p class="font-bold text-sm">{{ item.label }}</p>
                <p class="ws-muted text-xs mt-1">{{ item.detail }}</p>
              </div>
              <span class="text-2xl font-black" :class="item.color">{{
                item.value
              }}</span
              ><ChevronRight :size="16"
            /></RouterLink>
          </div>
        </article>
      </section>
    </template>
    <section v-else class="ws-panel">
      <div class="ws-toolbar">
        <div>
          <p class="ws-eyebrow">Mi semana</p>
          <h2 class="ws-heading mt-1">Tu próximo entrenamiento empieza aquí</h2>
          <p class="ws-muted text-sm mt-2">
            Consulta tus clases y organiza el tiempo para ti.
          </p>
        </div>
        <RouterLink to="/user/schedule" class="ws-btn ws-primary"
          ><CalendarDays :size="17" />{{
            clientEnrollments.length
              ? 'Gestionar mis horarios'
              : 'Elegir un horario'
          }}</RouterLink
        >
      </div>
      <div class="mt-5">
        <ExcelScheduleGrid
          title="Mi horario"
          subtitle="Tus clases se actualizan con cada matrícula registrada."
          :items="clientScheduleItems"
          file-name="mi-horario.xlsx"
          empty-message="Todavía no tienes clases. Elige un horario para empezar a entrenar."
        />
      </div>
    </section>
  </div>
</template>
<script setup>
import { defineAsyncComponent } from 'vue';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import { RouterLink } from 'vue-router';
import { ArrowUpRight, CalendarDays, ChevronRight, RefreshCw, UsersRound } from 'lucide-vue-next';
import { useDashboardOverview } from '../composables/dashboard/useDashboardOverview.js';

const ExcelScheduleGrid = defineAsyncComponent(() => import('../components/ExcelScheduleGrid.vue'));
const {
  user, isAdmin, userRole, isDarkTheme,
  gymStore, isRefreshing, refreshError, lastUpdated, quickActions,
  normalizeStatus, todayKey, members, schedules, enrollments,
  attendance, storeProducts, currentClient, currentClientId, currentClientIdentity,
  clientEnrollments, attendanceFor, clientScheduleItems, clientSummary, activeMembers,
  pendingMembers, usedSlots, totalSlots, adminCards, membershipSegments,
  membershipChartData, paymentChartData, services, serviceLabel, readableStatus,
  serviceUsedColors, serviceFreeColors, serviceCapacityData, lastSevenDays, attendanceTrendData,
  chartTextColor, gridColor, baseScale, barOptions, lineOptions,
  doughnutOptions, operationalAlerts, clientAttendanceCount, clientCards, refreshDashboard,
} = useDashboardOverview();
</script>

<style scoped>
.dashboard-metrics {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr);
}
@media (min-width: 768px) {
  .dashboard-metrics--admin {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (min-width: 1280px) {
  .dashboard-metrics--client {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.chart-box {
  position: relative;
  height: 280px;
  margin-top: 1.5rem;
}
.membership-segment {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 0.8rem;
  border: 1px solid var(--ws-border);
  border-radius: 0.8rem;
  font-size: 0.8rem;
}
@media (max-width: 480px) {
  .chart-box {
    height: 230px;
  }
}
</style>
