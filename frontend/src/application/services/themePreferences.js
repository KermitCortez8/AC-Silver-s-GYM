import { getApplicationServices } from '../ports/services.js';

export const readThemePreference = () => getApplicationServices().preferences.readThemePreference();
export const writeThemePreference = (theme) => getApplicationServices().preferences.writeThemePreference(theme);
export const preferredTheme = () => getApplicationServices().preferences.preferredTheme();
