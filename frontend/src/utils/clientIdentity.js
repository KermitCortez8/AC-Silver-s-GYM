export const normalizeEmail = (value) => String(value || '').trim().toLowerCase();

export const normalizeCode = (value) => String(value || '').trim().toUpperCase();

export const normalizeDni = (value) => String(value || '').replace(/\D/g, '');

const unwrapUser = (user = {}) => user?.value ?? user ?? {};

const numericFromCode = (value) => {
  const normalized = normalizeCode(value);
  const prefixed = normalized.match(/(?:SGCLI|CLIENTE[-_]?)(\d+)/);
  if (prefixed) return Number(prefixed[1]);
  if (/^\d{1,6}$/.test(normalized)) return Number(normalized);
  return 0;
};

const userCodeCandidates = (user = {}) => {
  const currentUser = unwrapUser(user);
  return [
    currentUser.id_usuario,
    currentUser.id,
    currentUser.internalCode,
    currentUser.memberCode,
    currentUser.codigo,
    currentUser.cliente_codigo,
    currentUser.cliente?.id_usuario,
    currentUser.sub,
  ].map(normalizeCode).filter(Boolean);
};

export const findClientForUser = (user = {}, members = []) => {
  const currentUser = unwrapUser(user);
  const idCliente = Number(currentUser.id_cliente || currentUser.idCliente || currentUser.cliente?.id_cliente || 0);
  const idCodes = userCodeCandidates(currentUser);
  const idUsuarioNumber = idCodes.map(numericFromCode).find(Boolean) || 0;
  const email = normalizeEmail(currentUser.email || currentUser.correo || currentUser.mail);
  const dni = normalizeDni(currentUser.dni || currentUser.documento);

  return (
    members.find((member) => Number(member.id_cliente || 0) === idCliente && idCliente > 0) ||
    members.find((member) => {
      const memberIdCliente = Number(member.id_cliente || 0);
      const identifiers = [member.id, member.internalCode, member.memberCode, member.id_usuario, member.cliente_codigo, member.id_cliente].map(normalizeCode);
      return idCodes.some((code) => identifiers.includes(code)) || Boolean(idUsuarioNumber && memberIdCliente === idUsuarioNumber);
    }) ||
    members.find((member) => dni && normalizeDni(member.dni) === dni) ||
    members.find((member) => {
      const memberEmails = [member.email, member.correo, member.google_email].map(normalizeEmail).filter(Boolean);
      return Boolean(email && memberEmails.includes(email));
    }) ||
    null
  );
};

export const resolveClientIdForUser = (user = {}, members = []) => {
  const currentUser = unwrapUser(user);
  const explicitId = Number(currentUser.id_cliente || currentUser.idClient || currentUser.idCliente || currentUser.cliente?.id_cliente || 0);
  if (explicitId) return explicitId;

  const client = findClientForUser(currentUser, members);
  if (client?.id_cliente) return Number(client.id_cliente);

  return userCodeCandidates(currentUser).map(numericFromCode).find(Boolean) || 0;
};

export const buildClientIdentityFromUser = (user = {}, members = []) => {
  const currentUser = unwrapUser(user);
  const client = findClientForUser(currentUser, members);
  if (client) return client;

  const idCliente = resolveClientIdForUser(currentUser, members);
  const preferredCode = userCodeCandidates(currentUser).find((code) => numericFromCode(code) === idCliente) || (idCliente ? `SGCLI${String(idCliente).padStart(3, '0')}` : '');
  const email = normalizeEmail(currentUser.email || currentUser.correo || currentUser.mail);
  const dni = normalizeDni(currentUser.dni || currentUser.documento);

  if (!idCliente && !preferredCode && !dni) return null;

  return {
    id_cliente: idCliente || null,
    id: preferredCode,
    id_usuario: preferredCode,
    internalCode: preferredCode,
    memberCode: preferredCode,
    name: currentUser.name || currentUser.nombre || 'Cliente',
    email,
    correo: email,
    dni,
    plan: currentUser.plan || '',
    membershipStatus: currentUser.membershipStatus || currentUser.estado || currentUser.status || '',
    status: currentUser.status || currentUser.estado || '',
    membershipEnd: currentUser.membershipEnd || currentUser.fecha_fin || '',
  };
};

export const attendanceBelongsToClient = (entry = {}, client = {}) => {
  const targetClient = client || {};
  const idCliente = Number(targetClient.id_cliente || 0);
  const entryClientNumber = Number(entry.id_cliente_num || entry.id_cliente || 0) || numericFromCode(entry.id_cliente || entry.memberCode || entry.memberId);
  const clientCodes = [targetClient.id, targetClient.internalCode, targetClient.memberCode, targetClient.id_cliente].map(normalizeCode).filter(Boolean);
  const entryCodes = [entry.memberId, entry.memberCode, entry.id_cliente].map(normalizeCode).filter(Boolean);

  return Boolean(
    (idCliente && entryClientNumber === idCliente) ||
      entryCodes.some((code) => clientCodes.includes(code))
  );
};

export const weekdayFromISO = (dateValue) => {
  if (!dateValue) return '';
  const date = new Date(`${String(dateValue).slice(0, 10)}T12:00:00`);
  return ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'][date.getDay()] || '';
};
