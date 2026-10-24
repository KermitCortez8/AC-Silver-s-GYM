/** Controles de un borrador de ejercicio antes de guardarlo. */
export const onSeriesChanged = (ex) => {
  ex.completado =
    Number(ex.series_completadas || 0) >= Number(ex.series_meta || 3);
};
export const adjustSeries = (ex, delta) => {
  const meta = Number(ex.series_meta || 3);
  ex.series_completadas = Math.max(
    0,
    Math.min(meta, Number(ex.series_completadas || 0) + delta),
  );
  onSeriesChanged(ex);
};
export const adjustWeight = (ex, delta) => {
  const current = Number(ex.peso_utilizado_kg ?? ex.peso_sugerido_kg ?? 0);
  ex.peso_utilizado_kg = Math.max(0, current + delta);
};
export const setWeightToSuggested = (ex) => {
  if (ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== undefined) {
    ex.peso_utilizado_kg = Number(ex.peso_sugerido_kg);
  }
};
export const onToggleExerciseCompleted = (ex) => {
  ex.series_completadas = ex.completado ? Number(ex.series_meta || 3) : 0;
};
