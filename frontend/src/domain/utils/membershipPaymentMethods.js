export const ONLINE_PAYMENT_OPTIONS = Object.freeze([
  { value: 'stripe', label: 'Stripe', description: 'Tarjeta y confirmación automática' },
  { value: 'yape_plin', label: 'Yape o Plin', description: 'Escanea el QR' },
  { value: 'mercado_pago', label: 'POS virtual', description: 'Enlace de Mercado Pago' },
]);

export const esPagoExterno = (metodo) => metodo === 'yape_plin' || metodo === 'mercado_pago';
export const etiquetaPagoExterno = (metodo) => metodo === 'yape_plin' ? 'Yape o Plin' : 'Mercado Pago';

export const ADMIN_PAYMENT_OPTIONS = Object.freeze([
  ...ONLINE_PAYMENT_OPTIONS,
  { value: 'pendiente', label: 'Registrar sin cobrar', description: 'Dejar el pago pendiente' },
]);
