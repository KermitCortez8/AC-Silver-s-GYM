import { clientMembershipGroup } from './clientDirectory.js';

const normalize = (value) =>
  String(value || '')
    .trim()
    .toUpperCase();
export const summarizeDashboardClients = (clients) => {
  const memberships = { active: 0, pending: 0, expired: 0 };
  const origins = [
    { key: 'ADMIN', label: 'Administración', paid: 0, pending: 0, unknown: 0 },
    {
      key: 'PUBLICO',
      label: 'Registro público',
      paid: 0,
      pending: 0,
      unknown: 0,
    },
    {
      key: '',
      label: 'Sin origen registrado',
      paid: 0,
      pending: 0,
      unknown: 0,
    },
  ];
  let readyToActivate = 0;
  let pendingPayment = 0;
  for (const client of clients) {
    const group = clientMembershipGroup(client);
    memberships[group] += 1;
    const payment = normalize(client.paymentStatus);
    if (group === 'pending' && payment === 'PAGADO') readyToActivate += 1;
    if (payment === 'PENDIENTE') pendingPayment += 1;
    const origin =
      origins.find(
        (item) => item.key === normalize(client.registrationOrigin),
      ) || origins[2];
    origin[
      payment === 'PAGADO'
        ? 'paid'
        : payment === 'PENDIENTE'
          ? 'pending'
          : 'unknown'
    ] += 1;
  }
  return {
    memberships,
    origins,
    readyToActivate,
    pendingPayment,
    total: clients.length,
  };
};

export const peruDateKey = (instant = new Date()) => {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Lima',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(instant);
  const part = (type) => parts.find((item) => item.type === type).value;
  return `${part('year')}-${part('month')}-${part('day')}`;
};

export const lastSevenPeruDays = (instant = new Date()) => {
  const date = new Date(`${peruDateKey(instant)}T12:00:00Z`);
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(date);
    day.setUTCDate(day.getUTCDate() - (6 - index));
    return day.toISOString().slice(0, 10);
  });
};
