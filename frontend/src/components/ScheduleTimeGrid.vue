<template><FullCalendar ref="calendar" :options="optionsWithPlugins" /></template>
<script setup>
import { computed, ref, watch } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
const props = defineProps({ options: { type: Object, required: true } });
const calendar = ref(null);
const optionsWithPlugins = computed(() => ({ ...props.options, plugins: [timeGridPlugin, interactionPlugin] }));
watch(() => props.options.initialDate, (date) => calendar.value?.getApi().gotoDate(date));
</script>
