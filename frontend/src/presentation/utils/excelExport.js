// Descargas en Excel con encabezados de color (rojo de la plataforma y texto blanco en negrita).
export const HEADER_FILL = 'FFC8102E';
export const HEADER_FONT = 'FFFFFFFF';

/**
 * Arma el libro sin tocar el navegador, para poder probarlo.
 * columns: [{ header, key, width }]; rows: objetos con esas claves.
 */
export const buildWorkbook = async ({ sheetName, title, columns, rows }) => {
  const { default: ExcelJS } = await import('exceljs');
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'AC Silver\'s GYM';
  workbook.created = new Date();
  const sheet = workbook.addWorksheet(sheetName, { views: [{ state: 'frozen', ySplit: title ? 2 : 1 }] });

  if (title) {
    sheet.mergeCells(1, 1, 1, columns.length);
    const cell = sheet.getCell(1, 1);
    cell.value = title;
    cell.font = { bold: true, size: 13 };
    sheet.getRow(1).height = 22;
  }
  const headerRow = sheet.getRow(title ? 2 : 1);
  columns.forEach((column, index) => {
    const cell = headerRow.getCell(index + 1);
    cell.value = column.header;
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: HEADER_FILL } };
    cell.font = { bold: true, color: { argb: HEADER_FONT } };
    cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
    cell.border = { bottom: { style: 'thin', color: { argb: 'FF7F0A1D' } } };
    sheet.getColumn(index + 1).width = column.width || 16;
  });
  headerRow.height = 20;

  rows.forEach((row) => sheet.addRow(columns.map((column) => row[column.key] ?? '')));
  sheet.autoFilter = { from: { row: headerRow.number, column: 1 }, to: { row: headerRow.number, column: columns.length } };
  return workbook;
};

export const excelFileName = (base, date = new Date()) => {
  const stamp = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima' }).format(date);
  return `${base}_${stamp}.xlsx`;
};

export const downloadWorkbook = async (workbook, fileName) => {
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

export const exportToExcel = async (options, fileBase) => downloadWorkbook(await buildWorkbook(options), excelFileName(fileBase));

export const INVENTORY_EXCEL_COLUMNS = [
  { header: 'N° artículo', key: 'codigo', width: 13 },
  { header: 'Nombre', key: 'nombre', width: 32 },
  { header: 'Categoría', key: 'categoria', width: 22 },
  { header: 'Ubicación', key: 'ubicacion', width: 18 },
  { header: 'Stock', key: 'stock', width: 9 },
  { header: 'Unidad', key: 'unidad', width: 11 },
  { header: 'Stock mínimo', key: 'minimo', width: 13 },
  { header: 'Estado', key: 'estado', width: 18 },
  { header: 'Observaciones', key: 'observaciones', width: 36 },
];

export const inventoryExcelRows = (items) => items.map((item) => ({
  codigo: item.inventoryCode,
  nombre: item.name,
  categoria: item.category,
  ubicacion: item.location,
  stock: Number(item.quantity ?? 0),
  unidad: item.unidad_venta || 'unidad',
  minimo: Number(item.minQuantity ?? 0),
  estado: item.status,
  observaciones: item.observations || '',
}));

export const RETIREMENTS_EXCEL_COLUMNS = [
  { header: 'Fecha de baja', key: 'fecha', width: 14 },
  { header: 'Código', key: 'codigo', width: 15 },
  { header: 'Artículo', key: 'articulo', width: 32 },
  { header: 'Categoría', key: 'categoria', width: 22 },
  { header: 'Tipo', key: 'tipo', width: 10 },
  { header: 'Motivo', key: 'motivo', width: 34 },
  { header: 'Ubicación', key: 'ubicacion', width: 18 },
];

export const retirementExcelRows = (rows) => rows.map((row) => ({ ...row, fecha: row.fecha || 'Sin fecha' }));

export const MOVEMENTS_EXCEL_COLUMNS = [
  { header: 'Fecha', key: 'fecha', width: 12 },
  { header: 'Hora', key: 'hora', width: 8 },
  { header: 'Artículo', key: 'articulo', width: 32 },
  { header: 'Tipo', key: 'tipo', width: 11 },
  { header: 'Cantidad', key: 'cantidad', width: 10 },
  { header: 'Destino', key: 'destino', width: 11 },
  { header: 'Descripción', key: 'descripcion', width: 44 },
  { header: 'Registrado por', key: 'usuario', width: 20 },
];

// rows: movimientos ya filtrados; itemName y author resuelven nombres legibles.
export const movementExcelRows = (rows, { itemName, author, destination, typeLabel, signed, time }) => rows.map((movement) => ({
  fecha: movement.fecha_movimiento || '',
  hora: time(movement),
  articulo: itemName(movement.id_item),
  tipo: typeLabel(movement.tipo_movimiento),
  cantidad: signed(movement),
  destino: destination(movement),
  descripcion: movement.descripcion || '',
  usuario: author(movement),
}));
