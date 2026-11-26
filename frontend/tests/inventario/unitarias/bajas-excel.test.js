import assert from 'node:assert/strict';
import { test } from 'node:test';
import ExcelJS from 'exceljs';
import {
  buildRetirements, filterRetirements, monthLabel, RETIREMENT_NAME_MAX_LENGTH, retirementMonths,
} from '../../../src/domain/utils/inventoryRetirements.js';
import {
  buildWorkbook, excelFileName, HEADER_FILL, HEADER_FONT, INVENTORY_EXCEL_COLUMNS, inventoryExcelRows,
  retirementExcelRows, RETIREMENTS_EXCEL_COLUMNS,
} from '../../../src/presentation/utils/excelExport.js';

// Datos de prueba: dos unidades de baja, una activa y dos artículos retirados (uno sin fecha).
const INVENTORY = [
  { id: 'item-1', inventoryCode: 'ACT-1001', name: 'Mancuerna hexagonal 5 kg par', category: 'Equipo de fuerza', location: 'Almacén', archived: false },
  { id: 'item-2', inventoryCode: 'ACT-1002', name: 'Colchoneta antideslizante', category: 'Accesorio', location: 'Sala 1', archived: true, retiredAt: '2026-10-05', observations: 'Rota' },
  { id: 'item-3', inventoryCode: 'ACT-1003', name: 'Bebida isotónica', category: 'Tienda', location: 'Almacén', archived: true, retiredAt: '' },
];
const UNITS = [
  { id_unidad: 21, id_item: 1, codigo: '1001-MH-021', estado: 'Dado de baja', ubicacion: 'Almacén', fecha_baja: '2026-11-15' },
  { id_unidad: 22, id_item: 1, codigo: '1001-MH-022', estado: 'Dado de baja', ubicacion: 'Sala de fuerza', fecha_baja: '2026-11-20' },
  { id_unidad: 23, id_item: 1, codigo: '1001-MH-023', estado: 'Operativo', ubicacion: 'Almacén' },
];
const MOVEMENTS = [
  { id_mov: 7, tipo_movimiento: 'salida', id_unidad: 22, descripcion: 'Óxido · Unidades: 1001-MH-022' },
  // Baja anterior a la 027: sin id_unidad, solo el código en la descripción.
  { id_mov: 5, tipo_movimiento: 'salida', id_unidad: null, descripcion: 'Unidades: 1001-MH-021' },
];
const rows = buildRetirements({ inventory: INVENTORY, units: UNITS, movements: MOVEMENTS });

test('B-04: Bajas junta unidades y artículos retirados, de la más reciente a las sin fecha', () => {
  assert.deepEqual(rows.map((row) => row.codigo), ['1001-MH-022', '1001-MH-021', 'ACT-1002', 'ACT-1003']);
  const [unidad, sinMotivo, articulo, sinFecha] = rows;
  assert.deepEqual([unidad.tipo, unidad.motivo, unidad.articulo, unidad.ubicacion], ['Unidad', 'Óxido', 'Mancuerna hexagonal 5 kg par', 'Sala de fuerza']);
  assert.equal(sinMotivo.motivo, 'Sin motivo');
  assert.deepEqual([articulo.tipo, articulo.motivo, articulo.fecha], ['Artículo', 'Rota', '2026-10-05']);
  assert.deepEqual([sinFecha.fecha, sinFecha.motivo], ['', 'Retirado del inventario']);
  assert.ok(!rows.some((row) => row.codigo === '1001-MH-023'), 'Una unidad activa no es baja');
});

test('B-05: el filtro por nombre recorta a 40 caracteres, ignora tildes y combina con el mes', () => {
  assert.equal(RETIREMENT_NAME_MAX_LENGTH, 40);
  assert.deepEqual(filterRetirements(rows, { name: 'manc', month: '2026-11' }).map((row) => row.codigo), ['1001-MH-022', '1001-MH-021']);
  assert.deepEqual(filterRetirements(rows, { name: 'isotonica' }).map((row) => row.codigo), ['ACT-1003']);
  assert.deepEqual(filterRetirements(rows, { month: '2026-10' }).map((row) => row.codigo), ['ACT-1002']);
  assert.equal(filterRetirements(rows, { name: `colchoneta${'x'.repeat(50)}` }).length, 0);
  assert.deepEqual(retirementMonths(rows), ['2026-11', '2026-10']);
  assert.equal(monthLabel('2026-11'), 'Noviembre 2026');
});

const readBack = async (workbook) => {
  const copy = new ExcelJS.Workbook();
  await copy.xlsx.load(await workbook.xlsx.writeBuffer());
  return copy.worksheets[0];
};

test('E-01: el Excel de Inventario tiene encabezados rojos con texto blanco en negrita', async () => {
  const workbook = await buildWorkbook({
    sheetName: 'Inventario', title: 'Listado de inventario', columns: INVENTORY_EXCEL_COLUMNS,
    rows: inventoryExcelRows([{ ...INVENTORY[0], quantity: 21, minQuantity: 1, unidad_venta: 'unidad', status: 'Operativo' }]),
  });
  const sheet = await readBack(workbook);
  const header = sheet.getRow(2);
  assert.equal(sheet.getCell(1, 1).value, 'Listado de inventario');
  assert.deepEqual(INVENTORY_EXCEL_COLUMNS.map((_, i) => header.getCell(i + 1).value), INVENTORY_EXCEL_COLUMNS.map((c) => c.header));
  for (let i = 1; i <= INVENTORY_EXCEL_COLUMNS.length; i += 1) {
    const cell = header.getCell(i);
    assert.equal(cell.fill.fgColor.argb, HEADER_FILL);
    assert.equal(cell.font.color.argb, HEADER_FONT);
    assert.equal(cell.font.bold, true);
  }
  assert.deepEqual(sheet.getRow(3).values.slice(1, 6), ['ACT-1001', 'Mancuerna hexagonal 5 kg par', 'Equipo de fuerza', 'Almacén', 21]);
  assert.equal(sheet.rowCount, 3);
});

test('E-02: el Excel de Bajas conserva tildes, marca "Sin fecha" y nombra el archivo con la fecha de Lima', async () => {
  const workbook = await buildWorkbook({ sheetName: 'Bajas', columns: RETIREMENTS_EXCEL_COLUMNS, rows: retirementExcelRows(rows) });
  const sheet = await readBack(workbook);
  assert.equal(sheet.getRow(1).getCell(1).fill.fgColor.argb, HEADER_FILL);
  assert.equal(sheet.getCell(2, 6).value, 'Óxido');
  assert.equal(sheet.getCell(5, 1).value, 'Sin fecha');
  assert.equal(sheet.rowCount, rows.length + 1);
  assert.equal(excelFileName('bajas_inventario', new Date('2026-11-25T03:00:00Z')), 'bajas_inventario_2026-11-24.xlsx');
});
