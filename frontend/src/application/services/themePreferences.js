import { getApplicationServices } from '../ports/services.js';

export const useThemePreferences = () => {
  const { preferences } = getApplicationServices();
  return {
    readThemePreference: () => preferences.readThemePreference(),
    writeThemePreference: theme => preferences.writeThemePreference(theme),
    preferredTheme: () => preferences.preferredTheme(),
  };
};
