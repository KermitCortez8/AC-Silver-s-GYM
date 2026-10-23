import { getApplicationServices } from '../ports/services.js';

export const loadGoogleIdentityScript = (...args) => getApplicationServices().auth.loadGoogleIdentityScript(...args);
export const getVerifiedGoogleProfile = (...args) => getApplicationServices().auth.getVerifiedGoogleProfile(...args);
export const authenticateWithGoogleCredential = (...args) => getApplicationServices().auth.authenticateWithGoogleCredential(...args);
export const authenticateWithPassword = (...args) => getApplicationServices().auth.authenticateWithPassword(...args);
export const saveAuthSession = (...args) => getApplicationServices().session.saveAuthSession(...args);
export const getAuthSession = (...args) => getApplicationServices().session.getAuthSession(...args);
export const clearAuthStorage = (...args) => getApplicationServices().session.clearAuthStorage(...args);

export const disableGoogleAutoSelect = () => getApplicationServices().auth.disableGoogleAutoSelect();
