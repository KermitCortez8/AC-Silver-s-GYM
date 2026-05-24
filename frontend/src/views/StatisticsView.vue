<template>
  <div class="space-y-8">
    <!-- Encabezado -->
    <section class="rounded-smoother border-2 border-primary/20 bg-gradient-to-r from-primary/10 to-primary-light/10 p-8">
      <h1 class="text-3xl font-bold text-gray-800">Estadísticas Avanzadas</h1>
      <p class="mt-2 text-gray-600">Análisis detallado de métricas y desempeño del gimnasio</p>
    </section>

    <!-- Todos los gráficos -->
    <StatisticsCharts />
  </div>
</template>

<script setup>
import StatisticsCharts from '../components/StatisticsCharts.vue';
</script>
