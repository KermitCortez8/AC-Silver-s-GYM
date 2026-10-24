import { getApplicationServices } from "../ports/services.js";

export const useAuthentication = () => {
  const { auth, session } = getApplicationServices();
  const bind = (adapter) => Object.fromEntries(Object.entries(adapter).map(([name, value]) =>
    [name, typeof value === 'function' ? value.bind(adapter) : value]));
  return { ...bind(auth), ...bind(session) };
};
