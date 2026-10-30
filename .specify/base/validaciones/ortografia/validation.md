# Validación de ortografía de la interfaz

Fecha: 2026-10-30.

## Alcance

Se revisaron los textos visibles del frontend: páginas públicas, menús de paneles,
horarios, matrículas, inventario, tienda, formularios y mensajes de ayuda/error.
Se corrigieron más de 200 literales en 38 archivos, por ejemplo «sesión», «catálogo»,
«membresía», «ubicación», «artículo», «imágenes», «acompaña» y «acompañe», además de
signos de apertura en confirmaciones. No se encontraron textos visibles «disenio».

Las etiquetas de horarios conservan los códigos internos sin tildes y presentan
«Musculación», «Miércoles» y «Sábado». La landing reutiliza `dayLabel` para los días
recibidos sin tildes. La ficha de cliente presenta «SIN PROMOCIÓN» para el valor
histórico `SIN PROMOCION` sin modificar ese dato.

No se modifican rutas, propiedades de API, claves, permisos, nombres introducidos
por usuarios ni registros existentes. Los valores predeterminados de texto libre
de duración y ubicación incluyen «días» y «Recepción». Se ajustaron las expectativas
textuales existentes de horario y stock mínimo y el selector del recorrido de tienda.

## Comprobaciones

- `npm test` en `frontend`: 280 pruebas correctas.
- `npm run build` en `frontend`: compilación correcta.
- Revisión de alcance comparando con una copia previa local:
  [38 archivos](evidence/scope-review.json), sin cambios en clases CSS, estilos,
  atributos técnicos, rutas API ni identificadores, salvo la reutilización de
  `dayLabel`. Se sincronizaron las etiquetas usadas para marcar campos inválidos.
- `git diff --check`: sin errores de formato.
- `python .specify/.codex/hooks/validate.py`: documentación válida.

La primera ejecución de pruebas señaló una expectativa antigua «Stock minimo»;
se actualizó a «Stock mínimo» y se repitió la suite completa correctamente.

## Navegador

El [recorrido](evidence/browser-review.cjs) revisa siete pantallas con API y sesiones
sintéticas: landing, nosotros, preguntas frecuentes, registro, inventario, tienda
administrativa y carrito móvil. Comprueba textos corregidos y la apertura de los
editores. La respuesta de horarios usa `miercoles`, `sabado` y `musculacion` para
comprobar su representación con tildes. El [resultado](evidence/browser-results.json)
registra siete casos correctos sin errores de página.

Se revisaron capturas de [nosotros](evidence/nosotros.png),
[horarios públicos](evidence/landing-horarios.png),
[editor de inventario](evidence/inventario-editor.png),
[editor de tienda](evidence/tienda-editor.png) y [carrito móvil](evidence/carrito.png).
Escritorio: 1440×1000; móvil: 390×844. Los recursos externos se bloquean en este
recorrido; no se acredita disponibilidad de imágenes remotas ni de proveedores.

Para repetir, instalar las dependencias del frontend y Playwright/Chromium fuera
del repositorio. Desde la raíz, arrancar el servidor local:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
```

En otra terminal:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/ortografia/evidence/browser-review.cjs
```
