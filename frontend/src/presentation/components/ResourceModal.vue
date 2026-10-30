<template>
  <Teleport to="body">
    <Transition name="rm-fade" appear>
      <div
        v-if="open"
        class="inv-store-theme rm-backdrop"
        @mousedown.self="pressedOnBackdrop = true"
        @click.self="handleBackdropClick"
      >
        <form
          ref="panel"
          class="rm-panel"
          :class="`rm-panel--${size}`"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          @submit.prevent="emit('submit')"
          @keydown="handleKeydown"
        >
          <header class="rm-header">
            <span v-if="icon" class="rm-header-icon" aria-hidden="true">
              <component :is="icon" :size="22" stroke-width="2.25" />
            </span>
            <div class="min-w-0">
              <p v-if="eyebrow" class="rm-eyebrow">{{ eyebrow }}</p>
              <h2 :id="titleId" class="rm-title">{{ title }}</h2>
              <p v-if="subtitle" class="rm-subtitle">{{ subtitle }}</p>
            </div>
            <button
              type="button"
              class="rm-close"
              :disabled="busy"
              aria-label="Cerrar"
              title="Cerrar (Esc)"
              @click="requestClose"
            >
              <X :size="20" aria-hidden="true" />
            </button>
          </header>

          <div class="rm-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="rm-footer">
            <slot name="footer" />
          </footer>
        </form>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
// Modales abiertos a la vez: el scroll de la pagina se libera al cerrar el ultimo.
let openModals = 0;
</script>

<script setup>
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue';
import { X } from 'lucide-vue-next';

const props = defineProps({
  open: Boolean,
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  busy: Boolean,
  size: { type: String, default: 'lg' },
});
const emit = defineEmits(['close', 'submit']);

const titleId = `rm-title-${useId()}`;
const panel = ref(null);
const pressedOnBackdrop = ref(false);
let previousFocus = null;

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
const FIRST_FIELD = 'input:not([disabled]):not([readonly]):not([type="hidden"]):not([type="file"]):not([type="radio"]), select:not([disabled]), textarea:not([disabled]):not([readonly])';

/**
 * Cierra el modal salvo que haya una operacion en curso.
 */
const requestClose = () => {
  if (!props.busy) emit('close');
};

/**
 * Solo cierra si el clic empezo y termino en el fondo (evita cerrar al soltar una seleccion de texto).
 */
const handleBackdropClick = () => {
  if (pressedOnBackdrop.value) requestClose();
  pressedOnBackdrop.value = false;
};

/**
 * Esc cierra y Tab mantiene el foco dentro del modal.
 */
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    event.preventDefault();
    requestClose();
    return;
  }
  if (event.key !== 'Tab' || !panel.value) return;
  const focusable = [...panel.value.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
};

const lockScroll = (locked) => {
  openModals = Math.max(0, openModals + (locked ? 1 : -1));
  document.body.style.overflow = openModals ? 'hidden' : '';
};

watch(
  () => props.open,
  async (open, wasOpen) => {
    if (typeof document === 'undefined' || open === Boolean(wasOpen)) return;
    if (open) {
      previousFocus = document.activeElement;
      lockScroll(true);
      await nextTick();
      (panel.value?.querySelector(FIRST_FIELD) || panel.value?.querySelector(FOCUSABLE))?.focus();
    } else {
      lockScroll(false);
      previousFocus?.focus?.();
      previousFocus = null;
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (props.open && typeof document !== 'undefined') lockScroll(false);
});
</script>
