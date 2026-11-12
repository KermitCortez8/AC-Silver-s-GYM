import { limaDate, addDays } from './dates.js';

export const canPayClientWithStripe = (client) =>
  client?.registrationOrigin === 'ADMIN' &&
  String(client.paymentStatus || '').trim().toUpperCase() === 'PENDIENTE' &&
  Number(client.id_membresia) > 0;


export const canRenewClientMembership = (client, today = limaDate()) => {
  if (Number(client?.id_cliente) <= 0 || !Number(client?.id_cliente)
    || !['ACTIVO', 'ACTIVA', 'VENCIDA', 'VENCIDO'].includes(String(client?.status || '').trim().toUpperCase())) return false;
  if (typeof client.canRenewMembership === 'boolean') return client.canRenewMembership;
  if (String(client.membershipStart || '').slice(0, 10) > today) return false;
  const end = String(client.membershipEnd || '').slice(0, 10);
  const parsed = new Date(`${end}T12:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(end) || !Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== end) return false;
  return end <= addDays(today, 7);
};
