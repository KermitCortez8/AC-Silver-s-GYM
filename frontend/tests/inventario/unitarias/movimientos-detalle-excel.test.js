import assert from 'node:assert/strict';
import { test } from 'node:test';
import ExcelJS from 'exceljs';
import { movementAuthor, movementHistory, movementTime, movementTypeLabel, signedQuantity } from '../../../src/domain/utils/inventoryMovements.js';
import { buildWorkbook, HEADER_FILL, movementExcelRows, MOVEMENTS_EXCEL_COLUMNS } from '../../../src/presentation/utils/excelExport.js';

// Historial de la mancuerna 1001: una baja antigua sin id_unidad, un traslado y movimientos de otro artículo.
const MOVEMENTS = [
  { id_mov: 1, id_item: 1, tipo_movimiento: 'entrada', cantidad: 2, fecha_movimiento: '2026-11-19', hora_movimiento: '21:45:00', descripcion: 'Alta de ítem · Unidades: 1001-MH-023 a 1001-MH-024', id_usuario: 1 },
  { id_mov: 2, id_item: 1, tipo_movimiento: 'salida', cantidad: 1, fecha_movimiento: '2026-11-15', hora_movimiento: '20:23:11', descripcion: 'Oxido · Unidades: 1001-MH-022', id_usuario: 1 },
  { id_mov: 3, id_item: 1, tipo_movimiento: 'traslado', cantidad: 1, fecha_movimiento: '2026-11-24', hora_movimiento: '19:12:00', descripcion: 'Traslado 1001-MH-019: Sala de fuerza → Sala 1', id_usuario: 1, id_unidad: 19 },
  { id_mov: 4, id_item: 1, tipo_movimiento: 'entrada', cantidad: 1, fecha_movimiento: '2026-11-19', hora_movimiento: '22:22:00', descripcion: 'Restablecimiento 1001-MH-022', id_usuario: 1, id_unidad: 22 },
  { id_mov: 5, id_item: 2, tipo_movimiento: 'salida', cantidad: 3, fecha_movimiento: '2026-11-20', hora_movimiento: '10:00:00', descripcion: 'Venta pedido #4', id_usuario: null, destino: 'VENTA' },
];

test('D-01: el historial del artículo va de lo más reciente a lo más antiguo y no mezcla otros artículos', () => {
  assert.deepEqual(movementHistory(MOVEMENTS, MOVEMENTS[2]).map((row) => row.id_mov), [3, 4, 1, 2]);
});

test('D-01: el historial de una unidad incluye bajas antiguas sin id_unidad que nombran su código', () => {
  const unit = { id_unidad: 22, codigo: '1001-MH-022' };
  assert.deepEqual(movementHistory(MOVEMENTS, MOVEMENTS[3], unit).map((row) => row.id_mov), [4, 2]);
  // El alta en rango "1001-MH-023 a 1001-MH-024" pertenece a la 023.
  assert.deepEqual(movementHistory(MOVEMENTS, MOVEMENTS[0], { id_unidad: 23, codigo: '1001-MH-023' }).map((row) => row.id_mov), [1]);
  // 1001-MH-02 no debe confundirse con 1001-MH-022 ni con 1001-MH-023.
  assert.deepEqual(movementHistory(MOVEMENTS, MOVEMENTS[3], { id_unidad: 99, codigo: '1001-MH-02' }).map((row) => row.id_mov), []);
});

test('D-01: quien registró el movimiento se resuelve por código o número de usuario', () => {
  const users = [{ id_usuario: 'SGADM001', nombre: 'Administrador Silver' }];
  assert.equal(movementAuthor(MOVEMENTS[0], users), 'Administrador Silver');
  assert.equal(movementAuthor(MOVEMENTS[4], users), 'Automático');
  assert.equal(movementAuthor({ id_usuario: 7 }, users), 'Usuario #7');
  assert.equal(movementTypeLabel('traslado'), 'Traslado');
});

test('X-01: el Excel de Movimientos trae hora, signo, destino y autor con encabezados rojos', async () => {
  const rows = movementExcelRows(MOVEMENTS, {
    itemName: (id) => (id === 1 ? 'Mancuerna hexagonal 5 kg par' : 'Agua'),
    author: (movement) => movementAuthor(movement, [{ id_usuario: 'SGADM001', nombre: 'Admin' }]),
    destination: (movement) => (movement.destino === 'VENTA' ? 'Venta' : ''),
    typeLabel: movementTypeLabel,
    signed: signedQuantity,
    time: movementTime,
  });
  const workbook = await buildWorkbook({ sheetName: 'Movimientos', columns: MOVEMENTS_EXCEL_COLUMNS, rows });
  const copy = new ExcelJS.Workbook();
  await copy.xlsx.load(await workbook.xlsx.writeBuffer());
  const sheet = copy.worksheets[0];
  assert.equal(sheet.getRow(1).getCell(1).fill.fgColor.argb, HEADER_FILL);
  assert.deepEqual(sheet.getRow(4).values.slice(1), ['2026-11-24', '19:12', 'Mancuerna hexagonal 5 kg par', 'Traslado', '0', '', 'Traslado 1001-MH-019: Sala de fuerza → Sala 1', 'Admin']);
  assert.deepEqual(sheet.getRow(6).values.slice(1, 9), ['2026-11-20', '10:00', 'Agua', 'Salida', '-3', 'Venta', 'Venta pedido #4', 'Automático']);
  assert.equal(sheet.rowCount, MOVEMENTS.length + 1);
});
