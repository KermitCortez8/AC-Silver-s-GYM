const searchable = (value) => String(value || '').normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '').toLowerCase();

export const filterMembershipPayments = (payments, {
  search = '', status = '', method = '', from = '', to = '',
} = {}) => {
  const query = searchable(search).trim();
  return payments.filter((payment) => {
    if (status && payment.estado_pago !== status) return false;
    if (method && payment.metodo_pago !== method) return false;
    const date = String(payment.fecha_pago || '').slice(0, 10);
    if ((from || to) && !date) return false;
    if (from && date < from) return false;
    if (to && date > to) return false;
    return !query || searchable([
      payment.nombre, payment.correo, payment.dni, payment.id_usuario,
      payment.id_membresia, payment.plan, payment.referencia_pago,
    ].join(' ')).includes(query);
  });
};

export const summarizeMembershipPayments = (payments) => payments.reduce((summary, payment) => {
  const amount = Number(payment.monto_pago) || 0;
  if (payment.estado_pago === 'PAGADO') {
    summary.paid += 1;
    summary.collected += amount;
  } else if (payment.estado_pago === 'PENDIENTE') {
    summary.pending += 1;
    summary.outstanding += amount;
  }
  return summary;
}, { total: payments.length, paid: 0, collected: 0, pending: 0, outstanding: 0 });
