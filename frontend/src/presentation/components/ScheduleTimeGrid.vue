<template><FullCalendar ref="calendar" :options="optionsWithPlugins" /></template>
<script setup>
import { computed, ref, watch } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
const props = defineProps({ options: { type: Object, required: true }, selectedEventId: { type: String, default: '' } });
const calendar = ref(null);
const mountedEvents = new Map();
const setSelected = (element, selected) => element.classList.toggle('excel-event-selected', selected);
const optionsWithPlugins = computed(() => ({
  ...props.options,
  plugins: [timeGridPlugin, interactionPlugin],
  eventDidMount: (info) => {
    const { event, el } = info;
    props.options.eventDidMount?.(info);
    mountedEvents.set(el, event.id);
    setSelected(el, event.id === props.selectedEventId);
  },
  eventWillUnmount: ({ el }) => mountedEvents.delete(el),
}));
// Resaltar una clase no cambia las opciones ni vuelve a renderizar la cuadrícula.
watch(() => props.selectedEventId, (current, previous) => {
  for (const [el, id] of mountedEvents) {
    if (id === current || id === previous) setSelected(el, id === current);
  }
});
watch(() => props.options.initialDate, (date) => calendar.value?.getApi().gotoDate(date));
</script>
