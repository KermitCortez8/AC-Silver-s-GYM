export const CLIENTS_PER_PAGE = 7;

const normalize = (value) =>
  String(value || '')
    .trim()
    .toUpperCase();
const searchable = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

export const normalizeMembershipStatus = (value) => {
  const status = normalize(value);
  if (['ACTIVO', 'ACTIVA'].includes(status)) return 'ACTIVO';
  if (['VENCIDO', 'VENCIDA'].includes(status)) return 'VENCIDA';
  return 'EN_TRAMITE';
};

export const clientMembershipGroup = (client) =>
  ({ ACTIVO: 'active', VENCIDA: 'expired', EN_TRAMITE: 'pending' })[
    normalizeMembershipStatus(client.membershipStatus || client.status)
  ];

export const clientMembershipLabel = (client) =>
  ({ active: 'Activo', expired: 'Vencida', pending: 'En trámite' })[
    clientMembershipGroup(client)
  ];

const clientNumber = (client) =>
  Number(client.id_cliente) ||
  Number(String(client.id || '').match(/(?:SGCLI|cliente-)(\d+)/i)?.[1]) ||
  0;

export const filterClientDirectory = (
  clients,
  { search = '', status = '', plan = '', payment = '', sort = 'recent' } = {},
) => {
  const query = searchable(search).trim();
  const result = clients.filter((client) => {
    if (status && clientMembershipGroup(client) !== status) return false;
    if (plan && normalize(client.plan) !== normalize(plan)) return false;
    const paymentStatus = normalize(client.paymentStatus) || 'UNKNOWN';
    if (payment && paymentStatus !== payment) return false;
    return (
      !query ||
      searchable(
        [
          client.id,
          client.name,
          client.email,
          client.phone,
          client.dni,
          client.plan,
          client.promocion,
          client.status,
          client.membershipStatus,
          clientMembershipLabel(client),
          client.paymentReference,
        ].join(' '),
      ).includes(query)
    );
  });
  return result.sort((a, b) => {
    if (sort === 'name')
      return (
        String(a.name || '').localeCompare(String(b.name || ''), 'es', {
          sensitivity: 'base',
        }) || clientNumber(b) - clientNumber(a)
      );
    // El ID se asigna al registrar y permite ordenar incluso antes de refrescar la fecha.
    return sort === 'oldest'
      ? clientNumber(a) - clientNumber(b)
      : clientNumber(b) - clientNumber(a);
  });
};

export const paginateClients = (clients, requestedPage = 1) => {
  const total = clients.length;
  const totalPages = Math.max(1, Math.ceil(total / CLIENTS_PER_PAGE));
  const page = Math.max(
    1,
    Math.min(totalPages, Math.trunc(Number(requestedPage)) || 1),
  );
  const offset = (page - 1) * CLIENTS_PER_PAGE;
  const visiblePages = [...new Set([1, totalPages, page - 1, page, page + 1])]
    .filter((n) => n >= 1 && n <= totalPages)
    .sort((a, b) => a - b);
  const pages = [];
  visiblePages.forEach((number, index) => {
    const previous = visiblePages[index - 1];
    if (number - previous === 2) pages.push(previous + 1);
    else if (number - previous > 2) pages.push(`gap-${number}`);
    pages.push(number);
  });
  return {
    page,
    totalPages,
    total,
    start: total ? offset + 1 : 0,
    end: Math.min(offset + CLIENTS_PER_PAGE, total),
    items: clients.slice(offset, offset + CLIENTS_PER_PAGE),
    pages,
  };
};
