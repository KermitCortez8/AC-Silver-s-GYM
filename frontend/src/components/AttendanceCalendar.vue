<template>
  <div class="w-full">
    <!-- Navegación del mes -->
    <div class="mb-6 flex items-center justify-between">
      <button
        @click="previousMonth"
        class="rounded-smooth bg-primary/20 p-2 text-primary transition hover:bg-primary/30"
      >
        ← Anterior
      </button>
      <h2 class="text-2xl font-bold text-gray-800">
        {{ monthName }} {{ currentYear }}
      </h2>
      <button
        @click="nextMonth"
        class="rounded-smooth bg-primary/20 p-2 text-primary transition hover:bg-primary/30"
      >
        Siguiente →
      </button>
    </div>

    <!-- Días de la semana -->
    <div class="mb-4 grid grid-cols-7 gap-2 text-center">
      <div v-for="day in weekDays" :key="day" class="font-semibold text-gray-600">
        {{ day }}
      </div>
    </div>

    <!-- Calendario -->
    <div class="grid grid-cols-7 gap-2">
      <div
        v-for="(day, index) in calendarDays"
        :key="index"
        :class="[
          'h-24 rounded-smooth border-2 p-2 text-sm transition',
          day === null
            ? 'bg-gray-100'
            : hasAttendance(day)
              ? 'border-primary bg-primary/10 cursor-pointer hover:bg-primary/20'
              : 'border-gray-300 bg-white cursor-pointer hover:border-primary/50 hover:bg-primary-light/20',
        ]"
        @click="selectDay(day)"
      >
        <div v-if="day !== null">
          <p class="font-bold text-gray-800">{{ day }}</p>
          <div
            v-if="hasAttendance(day)"
            class="mt-1 flex flex-col gap-1 text-xs text-primary"
          >
            <span class="font-semibold">✓ Asistencia</span>
            <span>{{ getAttendanceTime(day) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Detalle del día seleccionado -->
    <div v-if="selectedDay" class="mt-6 rounded-smoother border-2 border-primary/30 bg-primary-light/30 p-4">
      <h3 class="font-bold text-gray-800">
        Detalles del {{ selectedDay }} de {{ monthName }}
      </h3>
      <div v-if="hasAttendance(selectedDay)" class="mt-3 space-y-2 text-gray-700">
        <p><strong>Entrada:</strong> {{ getAttendanceTime(selectedDay) }}</p>
        <p><strong>Duración:</strong> Ver detalles completos</p>
      </div>
      <div v-else class="mt-3 text-gray-600">
        No hay asistencia registrada este día.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const today = new Date();
const currentMonth = ref(today.getMonth());
const currentYear = ref(today.getFullYear());
const selectedDay = ref(null);

const weekDays = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'];

const monthName = computed(() => {
  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  return months[currentMonth.value];
});

// Datos de asistencia (esto debería venir del API/store)
const attendanceData = ref({
  1: '06:30',
  5: '07:15',
  8: '18:00',
  12: '06:45',
  15: '19:30',
  19: '07:00',
  22: '18:15',
  26: '06:30',
});

const calendarDays = computed(() => {
  const firstDay = new Date(currentYear.value, currentMonth.value, 1);
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startingDayOfWeek = firstDay.getDay();

  const days = [];
  
  // Días vacíos antes del primer día del mes
  for (let i = 0; i < (startingDayOfWeek === 0 ? 6 : startingDayOfWeek - 1); i++) {
    days.push(null);
  }

  // Días del mes
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  return days;
});

const hasAttendance = (day) => {
  return day && attendanceData.value[day];
};

const getAttendanceTime = (day) => {
  return attendanceData.value[day] || '';
};

const previousMonth = () => {
  currentMonth.value--;
  if (currentMonth.value < 0) {
    currentMonth.value = 11;
    currentYear.value--;
  }
  selectedDay.value = null;
};

const nextMonth = () => {
  currentMonth.value++;
  if (currentMonth.value > 11) {
    currentMonth.value = 0;
    currentYear.value++;
  }
  selectedDay.value = null;
};

const selectDay = (day) => {
  if (day !== null) {
    selectedDay.value = selectedDay.value === day ? null : day;
  }
};
</script>
