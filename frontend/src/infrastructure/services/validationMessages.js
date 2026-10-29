const labels = {
  nombre: 'Nombre', correo: 'Correo', telefono: 'Teléfono', dni: 'DNI', password: 'Contraseña', contrasena: 'Contraseña',
  cliente_nombre: 'Cliente', cliente_correo: 'Correo', cliente_dni: 'DNI', motivo: 'Motivo', hora_entrada: 'Hora de entrada', hora_salida: 'Hora de salida',
  nombre_plan: 'Nombre del plan', duracion: 'Duración', precio: 'Precio', precio_venta: 'Precio',
  nombre_item: 'Nombre del artículo', nombre_producto: 'Nombre del producto', cantidad_stock: 'Stock', stock_minimo: 'Stock mínimo',
  cantidad: 'Cantidad', cupos: 'Cupos', capacidad_total: 'Capacidad total', capacidad_por_hora: 'Capacidad por hora',
  valor_descuento: 'Descuento', fecha_inicio: 'Fecha de inicio', fecha_fin: 'Fecha de fin',
  hora_inicio: 'Hora de inicio', hora_fin: 'Hora de fin', id_pm: 'Plan', id_rutina: 'Rutina',
  nombre_rutina: 'Nombre de la rutina', rol: 'Rol', plan: 'Plan', credential: 'Credencial de Google',
};

export const validationIssue = (issue) => {
  const field = (issue.loc || []).filter(part => !['body', 'query', 'path'].includes(part)).at(-1) || '';
  const type = issue.type || '';
  let message = String(issue.msg || 'El valor ingresado no es válido.').replace(/^Value error,\s*/i, '');
  if (type === 'missing' || message === 'Field required') message = 'Este campo es obligatorio.';
  else if (type.startsWith('int_')) message = 'Ingresa un número entero válido.';
  else if (type.startsWith('float_') || type === 'finite_number') message = 'Ingresa un número válido y finito.';
  else if (type === 'string_type') message = 'Ingresa texto válido.';
  else if (type === 'literal_error') message = 'Selecciona una opción válida.';
  else if (type === 'string_pattern_mismatch') message = field === 'dni' ? 'El DNI debe tener exactamente 8 dígitos.' : 'El formato ingresado no es válido.';
  else if (type.startsWith('date_')) message = 'Ingresa una fecha válida.';
  else if (type === 'greater_than_equal') message = `El valor debe ser mayor o igual a ${message.match(/-?\d+(?:\.\d+)?/)?.[0] || '0'}.`;
  else if (type === 'greater_than') message = `El valor debe ser mayor que ${message.match(/-?\d+(?:\.\d+)?/)?.[0] || '0'}.`;
  else if (type === 'less_than_equal') message = `El valor no debe superar ${message.match(/\d+(?:\.\d+)?/)?.[0] || 'el límite permitido'}.`;
  else if (type === 'string_too_short') message = `Ingresa al menos ${message.match(/\d+/)?.[0] || 'los'} caracteres requeridos.`;
  else if (type === 'string_too_long') message = `No superes ${message.match(/\d+/)?.[0] || 'el máximo de'} caracteres permitidos.`;
  else if (/^(Input should|String should|Value error)/i.test(message)) message = 'El valor ingresado no es válido.';
  return { field, message, text: field ? `${labels[field] || field}: ${message}` : message };
};
