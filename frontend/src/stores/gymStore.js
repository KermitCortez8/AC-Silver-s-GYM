import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

const STORAGE_KEY = 'gym_frontend_data_v1';

const seedState = () => ({
  members: [
    {
      id: 'member-1',
      name: 'María Fernández',
      email: 'maria@ejemplo.com',
      phone: '999 111 222',
      role: 'user',
      plan: 'Mensual',
      status: 'Activa',
      joinedAt: '2026-01-12',
      attendanceRate: 92,
    },
    {
      id: 'member-2',
      name: 'Carlos Rojas',
      email: 'carlos@urp.edu.pe',
      phone: '988 222 333',
      role: 'admin',
      plan: 'Anual',
      status: 'Activa',
      joinedAt: '2025-11-03',
      attendanceRate: 88,
    },
    {
      id: 'member-3',
      name: 'Lucía Torres',
      email: 'lucia@ejemplo.com',
      phone: '977 444 555',
      role: 'user',
      plan: 'Trimestral',
      status: 'Pendiente',
      joinedAt: '2026-03-20',
      attendanceRate: 76,
    },
  ],
  attendance: [
    {
      id: 'attendance-1',
      memberId: 'member-1',
      memberName: 'María Fernández',
      type: 'Entrada',
      time: '07:10',
      date: '2026-05-03',
      note: 'Rutina funcional',
    },
    {
      id: 'attendance-2',
      memberId: 'member-2',
      memberName: 'Carlos Rojas',
      type: 'Entrada',
      time: '06:45',
      date: '2026-05-03',
      note: 'Revisión general',
    },
    {
      id: 'attendance-3',
      memberId: 'member-3',
      memberName: 'Lucía Torres',
      type: 'Salida',
      time: '19:05',
      date: '2026-05-02',
      note: 'Finalizó cardio',
    },
  ],
  inventory: [
    {
      id: 'item-1',
      name: 'Mancuernas ajustables',
      category: 'Pesas',
      quantity: 12,
      minQuantity: 6,
      location: 'Sala 1',
      status: 'Disponible',
    },
    {
      id: 'item-2',
      name: 'Tapetes de yoga',
      category: 'Accesorios',
      quantity: 8,
      minQuantity: 10,
      location: 'Depósito',
      status: 'Stock bajo',
    },
    {
      id: 'item-3',
      name: 'Bandas de resistencia',
      category: 'Accesorios',
      quantity: 18,
      minQuantity: 8,
      location: 'Recepción',
      status: 'Disponible',
    },
  ],
  schedule: [
    { day: 'Lunes', hours: '06:00 - 22:00', focus: 'Piernas y glúteos' },
    { day: 'Martes', hours: '06:00 - 22:00', focus: 'Espalda y core' },
    { day: 'Miércoles', hours: '06:00 - 22:00', focus: 'Pecho y hombros' },
    { day: 'Jueves', hours: '06:00 - 22:00', focus: 'Cardio y movilidad' },
    { day: 'Viernes', hours: '06:00 - 22:00', focus: 'Full body' },
    { day: 'Sábado', hours: '08:00 - 18:00', focus: 'Clases dirigidas' },
    { day: 'Domingo', hours: '09:00 - 14:00', focus: 'Mantenimiento' },
  ],
});

const todayISO = () => new Date().toISOString().slice(0, 10);
const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const loadState = () => {
  if (typeof window === 'undefined') {
    return seedState();
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    return seedState();
  }

  try {
    const parsed = JSON.parse(stored);
    return {
      ...seedState(),
      ...parsed,
    };
  } catch (error) {
    return seedState();
  }
};

export const useGymStore = defineStore('gym', () => {
  const members = ref(loadState().members);
  const attendance = ref(loadState().attendance);
  const inventory = ref(loadState().inventory);
  const schedule = ref(loadState().schedule);

  const persist = () => {
    if (typeof window === 'undefined') return;

    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        members: members.value,
        attendance: attendance.value,
        inventory: inventory.value,
        schedule: schedule.value,
      }),
    );
  };

  const stats = computed(() => {
    const today = todayISO();
    const lowStockItems = inventory.value.filter((item) => item.quantity <= item.minQuantity).length;

    return {
      totalMembers: members.value.length,
      activeMembers: members.value.filter((member) => member.status === 'Activa').length,
      attendanceToday: attendance.value.filter((entry) => entry.date === today).length,
      inventoryItems: inventory.value.length,
      lowStockItems,
      attendanceRate: members.value.length
        ? Math.round(
            members.value.reduce((sum, member) => sum + Number(member.attendanceRate || 0), 0) /
              members.value.length,
          )
        : 0,
    };
  });

  const recentAttendance = computed(() =>
    [...attendance.value].sort((a, b) => `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)).slice(0, 10),
  );

  const lowStockInventory = computed(() =>
    inventory.value.filter((item) => item.quantity <= item.minQuantity),
  );

  const userAttendance = (email) => {
    const member = members.value.find((entry) => entry.email === email);
    if (!member) return [];

    return attendance.value.filter((entry) => entry.memberId === member.id).slice(0, 10);
  };

  const memberByEmail = (email) => members.value.find((member) => member.email === email) || null;

  const upsertMember = (payload) => {
    const member = {
      id: payload.id || `member-${Date.now()}`,
      name: payload.name?.trim() || 'Sin nombre',
      email: payload.email?.trim() || '',
      phone: payload.phone?.trim() || '',
      role: payload.role || 'user',
      plan: payload.plan || 'Mensual',
      status: payload.status || 'Activa',
      joinedAt: payload.joinedAt || todayISO(),
      attendanceRate: Number(payload.attendanceRate ?? 0),
    };

    const index = members.value.findIndex((entry) => entry.id === member.id);
    if (index >= 0) {
      members.value[index] = member;
    } else {
      members.value.unshift(member);
    }
    persist();
    return member;
  };

  const deleteMember = (id) => {
    members.value = members.value.filter((member) => member.id !== id);
    attendance.value = attendance.value.filter((entry) => entry.memberId !== id);
    persist();
  };

  const recordAttendance = (memberId, type = 'Entrada', note = '') => {
    const member = members.value.find((entry) => entry.id === memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    const record = {
      id: `attendance-${Date.now()}`,
      memberId,
      memberName: member.name,
      type,
      time: nowTime(),
      date: todayISO(),
      note,
    };

    attendance.value.unshift(record);
    persist();
    return record;
  };

  const upsertInventoryItem = (payload) => {
    const item = {
      id: payload.id || `item-${Date.now()}`,
      name: payload.name?.trim() || 'Sin nombre',
      category: payload.category || 'General',
      quantity: Number(payload.quantity ?? 0),
      minQuantity: Number(payload.minQuantity ?? 0),
      location: payload.location || 'Sin ubicación',
      status: payload.status || 'Disponible',
    };

    const index = inventory.value.findIndex((entry) => entry.id === item.id);
    if (index >= 0) {
      inventory.value[index] = item;
    } else {
      inventory.value.unshift(item);
    }
    persist();
    return item;
  };

  const deleteInventoryItem = (id) => {
    inventory.value = inventory.value.filter((item) => item.id !== id);
    persist();
  };

  return {
    members,
    attendance,
    inventory,
    schedule,
    stats,
    recentAttendance,
    lowStockInventory,
    userAttendance,
    memberByEmail,
    upsertMember,
    deleteMember,
    recordAttendance,
    upsertInventoryItem,
    deleteInventoryItem,
  };
});
