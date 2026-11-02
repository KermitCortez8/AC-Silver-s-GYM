# Límites de entrada del cliente

Síntoma: teléfono y DNI del editor administrativo admitían más caracteres de
los previstos. Se añadió `maxlength` de 9 y 8 respectivamente e `inputmode`
numérico. El formulario compartido aplica los límites en alta y edición.

Criterio de regresión: al escribir o pegar texto, el navegador limita el teléfono
a 9 caracteres y el DNI a 8. Se conserva la validación de dígitos existente.

Comprobaciones:

- `npm test --prefix frontend`: 293 pruebas aprobadas.
- `npm run build --prefix frontend`: aprobado.
- `python .specify/.codex/hooks/validate.py`: aprobado.
- Revisión visual e interacción en navegador: no ejecutadas; el entorno no
  dispone de navegador instalado ni herramienta de navegación.
