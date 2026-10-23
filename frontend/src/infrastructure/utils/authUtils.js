// Compatibilidad para consumidores anteriores.
export * from '../../domain/utils/authRules.js';
export { saveAuthSession, getAuthSession, clearAuthStorage } from '../services/sessionStorage.js';
