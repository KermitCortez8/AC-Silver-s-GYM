<template>
  <div class="w-full space-y-6">
    <!-- Gráfico de Asistencias del Mes -->
    <div class="card">
      <h3 class="text-2xl font-bold text-gray-800">Asistencias del Mes</h3>
      <div class="mt-6 flex gap-1 overflow-x-auto pb-4">
        <div
          v-for="(day, index) in monthAttendance"
          :key="index"
          class="flex flex-col items-center gap-2"
        >
          <div
            class="h-16 w-6 rounded-t-smooth transition hover:scale-110 cursor-pointer"
            :style="{
              background: `linear-gradient(180deg, rgba(239, 129, 107, ${Math.min(day / 30, 1)}) 0%, rgba(212, 106, 82, ${Math.min(day / 30, 1) * 0.7}) 100%)`
            }"
            :title="`Día ${index + 1}: ${day} asistencias`"
          ></div>
          <span class="text-xs font-semibold text-gray-600">{{ index + 1 }}</span>
        </div>
      </div>
      <div class="mt-6 grid grid-cols-3 gap-4">
        <div class="rounded-smooth bg-gradient-to-br from-primary/20 to-primary/10 p-5 border-2 border-primary/20">
          <p class="text-xs uppercase tracking-widest text-primary font-semibold">Total</p>
          <p class="text-3xl font-bold text-primary mt-2">{{ totalAttendance }}</p>
          <p class="text-xs text-gray-600 mt-1">asistencias</p>
        </div>
        <div class="rounded-smooth bg-gradient-to-br from-accent/20 to-accent/10 p-5 border-2 border-accent/20">
          <p class="text-xs uppercase tracking-widest text-accent font-semibold">Promedio</p>
          <p class="text-3xl font-bold text-accent mt-2">{{ (totalAttendance / 30).toFixed(1) }}</p>
          <p class="text-xs text-gray-600 mt-1">por día</p>
        </div>
        <div class="rounded-smooth bg-gradient-to-br from-warning/20 to-warning/10 p-5 border-2 border-warning/20">
          <p class="text-xs uppercase tracking-widest text-warning font-semibold">Pico</p>
          <p class="text-3xl font-bold text-warning mt-2">{{ Math.max(...monthAttendance) }}</p>
          <p class="text-xs text-gray-600 mt-1">máximo</p>
        </div>
      </div>
    </div>

    <!-- Productos Más Vendidos -->
    <div class="card">
      <h3 class="text-2xl font-bold text-gray-800">Productos Más Vendidos</h3>
      <div class="mt-6 space-y-4">
        <div v-for="(product, index) in topProducts" :key="index" class="flex items-center gap-4">
          <div class="flex-shrink-0 w-10 h-10 rounded-smooth bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
            <span class="text-white font-bold text-lg">{{ index + 1 }}</span>
          </div>
          <div class="flex-1">
            <div class="flex justify-between mb-2">
              <p class="font-semibold text-gray-800">{{ product.name }}</p>
              <p class="font-bold text-primary">{{ product.sales }} ventas</p>
            </div>
            <div class="h-2 overflow-hidden rounded-smooth bg-gray-200">
              <div
                class="h-full bg-gradient-to-r from-primary to-primary-dark transition-all"
                :style="{ width: (product.sales / 150) * 100 + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mes con Más Clientes -->
    <div class="card">
      <h3 class="text-2xl font-bold text-gray-800">Clientes por Mes</h3>
      <div class="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(month, index) in monthlyClients"
          :key="index"
          class="rounded-smooth border-2 border-success/30 bg-gradient-to-br from-success/20 to-success/10 p-5 text-center hover:shadow-lg transition"
        >
          <p class="text-xs uppercase tracking-widest text-success font-semibold">{{ month.name }}</p>
          <p class="mt-3 text-3xl font-bold text-success">{{ month.count }}</p>
        </div>
      </div>
    </div>

    <!-- Hora de Más Ingresos -->
    <div class="card">
      <h3 class="text-2xl font-bold text-gray-800">Ingresos por Hora</h3>
      <div class="mt-6 flex gap-1 items-end h-56">
        <div
          v-for="(hour, index) in hourlyIncome"
          :key="index"
          class="flex-1 flex flex-col items-center gap-2"
        >
          <div
            class="w-full rounded-t-smooth bg-gradient-to-t from-accent to-primary transition hover:scale-105 cursor-pointer"
            :style="{ height: (hour.income / 100) * 100 + '%', minHeight: '6px' }"
            :title="`${hour.time}: $${hour.income}`"
          ></div>
          <span class="text-xs font-semibold text-gray-600">{{ hour.time }}</span>
        </div>
      </div>
      <div class="mt-6 flex items-center justify-between bg-gradient-to-r from-accent/10 to-primary/10 p-5 rounded-smooth border-2 border-accent/20">
        <div>
          <p class="text-xs uppercase tracking-widest text-accent font-semibold">Hora Pico</p>
          <p class="text-3xl font-bold text-accent mt-2">
            {{ hourlyIncome.reduce((max, h) => h.income > max.income ? h : max).time }}
          </p>
        </div>
        <div class="text-right">
          <p class="text-xs uppercase tracking-widest text-primary font-semibold">Ingresos Máximos</p>
          <p class="text-3xl font-bold text-primary mt-2">
            ${{ hourlyIncome.reduce((max, h) => h.income > max.income ? h : max).income }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

// Datos simulados para gráficos
const monthAttendance = [25, 18, 22, 24, 19, 28, 21, 26, 20, 23, 27, 25, 22, 24, 19, 28, 25, 23, 21, 26, 24, 22, 25, 20, 27, 23, 26, 19, 21, 28];

const topProducts = [
  { name: 'Proteína Bar', sales: 145 },
  { name: 'Agua', sales: 132 },
  { name: 'Bebida Energética', sales: 118 },
  { name: 'Jugo Natural', sales: 95 },
  { name: 'Café', sales: 87 },
];

const monthlyClients = [
  { name: 'Enero', count: 1240 },
  { name: 'Febrero', count: 1350 },
  { name: 'Marzo', count: 1180 },
  { name: 'Abril', count: 1420 },
];

const hourlyIncome = [
  { time: '6am', income: 25 },
  { time: '7am', income: 55 },
  { time: '8am', income: 42 },
  { time: '12pm', income: 35 },
  { time: '5pm', income: 68 },
  { time: '6pm', income: 85 },
  { time: '7pm', income: 72 },
  { time: '8pm', income: 45 },
];

const totalAttendance = computed(() => {
  return monthAttendance.reduce((a, b) => a + b, 0);
});
</script>
