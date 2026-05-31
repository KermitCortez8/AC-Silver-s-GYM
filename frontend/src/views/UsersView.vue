<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administración</p>
          <h1 class="mt-2 text-3xl font-black text-white">Clientes y expedientes</h1>
          <p class="mt-2 text-slate-300">Gestiona clientes, busca por DNI o código interno, y deja trazabilidad de sus cambios.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-4">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ members.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeMembers }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Admins</p>
            <p class="text-xl font-black text-white">{{ adminMembers }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Vence pronto</p>
            <p class="text-xl font-black text-white">{{ expiringMembers }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Formulario</p>
            <h2 class="text-2xl font-black text-white">{{ editingId ? 'Editar miembro' : 'Nuevo miembro' }}</h2>
          </div>
          <button v-if="editingId" type="button" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm" @click="resetForm">
            Cancelar
          </button>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.name" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="Nombre completo" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="form.dni" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="74281635" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Código interno</span>
            <input v-model="form.internalCode" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="GYM-0004" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="form.email" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="correo@ejemplo.com" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Teléfono</span>
            <input v-model="form.phone" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="999 888 777" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Plan</span>
            <select v-model="form.plan" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Mensual</option>
              <option>Trimestral</option>
              <option>Anual</option>
              <option>Acceso total</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Rol</span>
            <select v-model="form.role" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="user">Miembro</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.status" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Activa</option>
              <option>Pendiente</option>
              <option>Bloqueada</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Plan de membresía</span>
            <select v-model="form.planId" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option v-for="plan in activePlans" :key="plan.id" :value="plan.id">{{ plan.name }} · {{ plan.durationMonths }} mes(es)</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Promoción</span>
            <select v-model="form.promotionId" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="">Sin promoción</option>
              <option v-for="promotion in activePromotions" :key="promotion.id" :value="promotion.id">{{ promotion.name }}</option>
            </select>
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nota de membresía</span>
            <input v-model="form.membershipNote" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="Alta, renovación o descuento aplicado" />
          </label>
          <label class="flex items-center gap-3 sm:col-span-2">
            <input v-model="form.assignMembership" type="checkbox" class="h-4 w-4 accent-cyan-300" />
            <span class="text-sm text-slate-300">Asignar o renovar membresía al guardar</span>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar expediente' : 'Registrar cliente' }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
            <h2 class="text-2xl font-black text-white">Clientes registrados</h2>
          </div>
          <input v-model="search" class="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-white outline-none" placeholder="Buscar por DNI, nombre o código..." />
        </div>

        <div class="mt-5 space-y-3">
          <article
            v-for="member in filteredMembers"
            :key="member.id"
            class="rounded-3xl border border-white/10 bg-slate-900/80 p-5"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ member.name }}</p>
                <p class="text-sm text-slate-400">{{ member.email }} · {{ member.phone }}</p>
                <p class="text-sm text-slate-400">DNI: {{ member.dni || 'Sin DNI' }} · Código: {{ member.internalCode || 'Sin código' }}</p>
                <p class="mt-2 text-sm text-slate-300">Plan: {{ member.plan }} · Estado: {{ member.status }} · Rol: {{ member.role }}</p>
                <p class="mt-1 text-sm text-cyan-200">Vence: {{ member.membershipEnd || 'Sin vencimiento' }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editMember(member)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteMember(member.id)">
                  Eliminar
                </button>
              </div>
            </div>
          </article>
        </div>

        <div v-if="selectedMember" class="mt-6 rounded-[1.5rem] border border-white/10 bg-slate-950/50 p-5">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Expediente</p>
              <h3 class="mt-1 text-xl font-black text-white">{{ selectedMember.name }}</h3>
            </div>
            <div class="rounded-2xl bg-white/5 px-4 py-2 text-sm text-slate-200">
              {{ selectedMember.internalCode }}
            </div>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-3">
            <div class="rounded-2xl bg-white/5 p-4">
              <p class="text-xs text-slate-400">Membresía</p>
              <p class="mt-1 font-bold text-white">{{ selectedMember.plan }}</p>
            </div>
            <div class="rounded-2xl bg-white/5 p-4">
              <p class="text-xs text-slate-400">Inicio</p>
              <p class="mt-1 font-bold text-white">{{ selectedMember.membershipStart || 'N/D' }}</p>
            </div>
            <div class="rounded-2xl bg-white/5 p-4">
              <p class="text-xs text-slate-400">Fin</p>
              <p class="mt-1 font-bold text-white">{{ selectedMember.membershipEnd || 'N/D' }}</p>
            </div>
          </div>

          <div class="mt-4">
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial de cambios</p>
            <div class="mt-3 space-y-2">
              <div v-for="item in selectedMember.changeHistory || []" :key="item.id" class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
                <p class="font-semibold text-white">{{ item.action }}</p>
                <p class="text-slate-400">{{ item.at }} · {{ item.note || 'Sin nota' }}</p>
              </div>
              <p v-if="!(selectedMember.changeHistory || []).length" class="text-sm text-slate-400">Todavía no hay cambios registrados para este expediente.</p>
            </div>
          </div>

          <div class="mt-4">
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial de membresía</p>
            <div class="mt-3 space-y-2">
              <div v-for="item in selectedMember.membershipHistory || []" :key="item.id" class="rounded-2xl border border-cyan-400/10 bg-cyan-400/5 px-4 py-3 text-sm text-slate-200">
                <p class="font-semibold text-white">{{ item.type }} · {{ item.planName }}</p>
                <p class="text-slate-400">{{ item.startDate }} → {{ item.endDate }} · Descuento: {{ item.discount }} · Precio final: {{ item.finalPrice }}</p>
              </div>
              <p v-if="!(selectedMember.membershipHistory || []).length" class="text-sm text-slate-400">No hay asignaciones o renovaciones registradas.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const members = computed(() => gymStore.members);
const activePlans = computed(() => gymStore.activePlans);
const activePromotions = computed(() => gymStore.activePromotions);
const search = ref('');
const editingId = ref('');

const form = reactive({
  name: '',
  dni: '',
  internalCode: '',
  email: '',
  phone: '',
  plan: 'Mensual',
  planId: 'plan-monthly',
  promotionId: '',
  membershipNote: '',
  assignMembership: true,
  role: 'user',
  status: 'Activa',
});

const filteredMembers = computed(() => {
  return gymStore.searchMembers(search.value);
});

const activeMembers = computed(() => members.value.filter((member) => member.status === 'Activa').length);
const adminMembers = computed(() => members.value.filter((member) => member.role === 'admin').length);
const expiringMembers = computed(() => gymStore.membershipAlerts.length);
const selectedMember = computed(() => (editingId.value ? gymStore.memberById(editingId.value) : null));

const resetForm = () => {
  editingId.value = '';
  form.name = '';
  form.dni = '';
  form.internalCode = '';
  form.email = '';
  form.phone = '';
  form.plan = 'Mensual';
  form.planId = 'plan-monthly';
  form.promotionId = '';
  form.membershipNote = '';
  form.assignMembership = true;
  form.role = 'user';
  form.status = 'Activa';
};

const editMember = (member) => {
  editingId.value = member.id;
  form.name = member.name;
  form.dni = member.dni || '';
  form.internalCode = member.internalCode || '';
  form.email = member.email;
  form.phone = member.phone;
  form.plan = member.plan;
  form.planId = member.planId || 'plan-monthly';
  form.promotionId = '';
  form.membershipNote = '';
  form.assignMembership = false;
  form.role = member.role;
  form.status = member.status;
};

const handleSubmit = async () => {
  try {
    const member = await gymStore.upsertMember({ id: editingId.value || undefined, ...form });

    if (form.assignMembership) {
      await gymStore.assignPlanToMember(member.id, form.planId, form.promotionId, form.membershipNote || 'Asignación/renovación desde expediente');
    }

    resetForm();
  } catch (error) {
    console.error('Error al guardar miembro:', error);
    // Aquí puedes mostrar un toast/alerta
  }
};
</script>
