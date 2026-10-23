export const canPayClientWithStripe = (client) =>
  client?.registrationOrigin === 'ADMIN' &&
  String(client.paymentStatus || '').trim().toUpperCase() === 'PENDIENTE' &&
  Number(client.id_membresia) > 0;
