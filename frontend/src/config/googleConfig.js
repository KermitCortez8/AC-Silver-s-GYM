// src/config/googleConfig.js
// 
// ⚠️ CONFIGURACIÓN WEB - Solo para navegador web
//
// INSTRUCCIONES:
// 1. Lee: WEB_GOOGLE_AUTH_SETUP.md
// 2. Obtén tu Client ID de Google Cloud Console
// 3. Reemplaza 'PEGA_TU_CLIENT_ID_AQUI' abajo con tu Client ID de web

export const GOOGLE_CONFIG = {
  // Client ID OAuth 2.0 tipo Web
  webClientId: '439271295964-0jkl1secjabmmor8k0qr5sai48bkicj2.apps.googleusercontent.com',

  scopes: ['profile', 'email'],
};

// Validar que esté configurado
if (GOOGLE_CONFIG.webClientId.includes('PEGA_TU_CLIENT_ID')) {
  console.warn('⚠️ ERROR: Client ID no configurado.\n📖 Lee: WEB_GOOGLE_AUTH_SETUP.md');
} else {
  console.log('✅ Google Auth configurado para web');
}
