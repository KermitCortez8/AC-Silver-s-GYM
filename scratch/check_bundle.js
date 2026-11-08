import fs from 'fs';

const code = fs.readFileSync('scratch/bundle.js', 'utf8');
const imports = code.match(/import\s*\{[^}]*\}\s*from\s*["'][^"']+["']/g) || [];
console.log('Top level imports:', imports.slice(0, 10));

const dynamicImports = code.match(/import\(["'][^"']+["']\)/g) || [];
console.log('Dynamic imports count:', dynamicImports.length);
console.log('Sample dynamic imports:', dynamicImports.slice(0, 5));
