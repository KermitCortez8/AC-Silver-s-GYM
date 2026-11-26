// Pestaña Bajas: unidades con N° de activo dadas de baja y artículos retirados del inventario.
import { RETIRED_UNIT_STATUS } from './inventoryUnits.js';

export const RETIREMENT_NAME_MAX_LENGTH = 40;
const NO_DATE = 'Sin fecha';
const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

const itemNumber = (item) => Number(String(item?.id ?? '').replace('item-', ''));
const normalize = (text) => String(text ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

// Motivo de la baja de una unidad: la salida ligada a ella, sin la lista de códigos que agrega el sistema.
const unitReason = (unit, movements) => {
  const exit = movements
    .filter((movement) => movement.tipo_movimiento === 'salida' && (
      Number(movement.id_unidad) === Number(unit.id_unidad)
      || String(movement.descripcion || '').includes(unit.codigo)))
    .sort((a, b) => Number(b.id_mov || 0) - Number(a.id_mov || 0))[0];
  const reason = String(exit?.descripcion || '').replace(/\s*·?\s*Unidad(es)?:.*$/, '').trim();
  return reason || 'Sin motivo';
};

export const buildRetirements = ({ inventory = [], units = [], movements = [] } = {}) => {
  const items = new Map(inventory.map((item) => [itemNumber(item), item]));
  const unitRows = units
    .filter((unit) => unit.estado === RETIRED_UNIT_STATUS)
    .map((unit) => {
      const item = items.get(Number(unit.id_item));
      return {
        key: `unidad-${unit.id_unidad}`,
        fecha: unit.fecha_baja || '',
        codigo: unit.codigo,
        articulo: item?.name || `Artículo #${unit.id_item}`,
        categoria: item?.category || '',
        tipo: 'Unidad',
        motivo: unitReason(unit, movements),
        ubicacion: unit.ubicacion || '',
      };
    });
  const itemRows = inventory
    .filter((item) => item.archived)
    .map((item) => ({
      key: `articulo-${item.id}`,
      fecha: item.retiredAt || '',
      codigo: item.inventoryCode,
      articulo: item.name,
      categoria: item.category || '',
      tipo: 'Artículo',
      motivo: item.observations || 'Retirado del inventario',
      ubicacion: item.location || '',
    }));
  // Primero las más recientes; las que no tienen fecha van al final.
  return [...unitRows, ...itemRows].sort((a, b) => (b.fecha || '').localeCompare(a.fecha || '') || a.codigo.localeCompare(b.codigo));
};

export const monthKey = (date) => (/^\d{4}-\d{2}/.test(String(date || '')) ? String(date).slice(0, 7) : '');

export const monthLabel = (key) => {
  if (!key) return NO_DATE;
  const [year, month] = key.split('-');
  const name = MONTHS[Number(month) - 1] || month;
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${year}`;
};

export const retirementMonths = (rows) =>
  [...new Set(rows.map((row) => monthKey(row.fecha)).filter(Boolean))].sort().reverse();

export const filterRetirements = (rows, { name = '', month = 'all' } = {}) => {
  const query = normalize(String(name).slice(0, RETIREMENT_NAME_MAX_LENGTH));
  return rows.filter((row) => (!query || normalize(row.articulo).includes(query) || normalize(row.codigo).includes(query))
    && (month === 'all' || monthKey(row.fecha) === month));
};

export const formatRetirementDate = (date) => date || NO_DATE;
