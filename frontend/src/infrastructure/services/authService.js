import { apiPost, request } from "./apiClient";

export const createAuthService = (http = { apiPost, request }) => {
  const { apiPost } = http;
  let googleScriptPromise = null;

  const loadGoogleIdentityScript = () => {
    if (typeof window === "undefined") {
      return Promise.reject(
        new Error("Google Identity Services requiere navegador"),
      );
    }
    if (window.google?.accounts?.id) return Promise.resolve(window.google);
    if (googleScriptPromise) return googleScriptPromise;

    googleScriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector(
        'script[data-google-identity="true"]',
      );
      const script = existing || document.createElement("script");
      const cleanup = () => {
        window.clearTimeout(timeout);
        script.removeEventListener("load", loaded);
        script.removeEventListener("error", failed);
      };
      const failed = () => {
        cleanup();
        script.remove();
        reject(
          new Error(
            "No se pudo cargar Google. Comprueba tu conexión e inténtalo nuevamente.",
          ),
        );
      };
      const loaded = () => {
        if (!window.google?.accounts?.id) return failed();
        cleanup();
        resolve(window.google);
      };
      const timeout = window.setTimeout(failed, 15000);
      script.addEventListener("load", loaded);
      script.addEventListener("error", failed);
      if (!existing) {
        script.src = "https://accounts.google.com/gsi/client?hl=es";
        script.async = true;
        script.defer = true;
        script.dataset.googleIdentity = "true";
        document.head.appendChild(script);
      }
    }).catch((error) => {
      googleScriptPromise = null;
      throw error;
    });
    return googleScriptPromise;
  };

  const getVerifiedGoogleProfile = async (credential) => {
    if (!credential) throw new Error("No se recibió credencial de Google");
    return apiPost("/auth/google/profile", { credential });
  };

  const authenticateWithGoogleCredential = async (
    credential,
    password = "",
  ) => {
    if (!credential) throw new Error("No se recibió credencial de Google");
    // El navegador no decide la identidad ni el rol: solo acepta la sesión del servidor.
    const result = await apiPost("/auth/google", { credential, password });
    if (!result?.token || !result?.user?.email) {
      throw new Error("El servidor no devolvió una sesión válida");
    }
    return result;
  };

  const authenticateWithPassword = async ({ correo, password }) => {
    const result = await apiPost("/auth/password", { correo, password });
    if (!result?.token || !result?.user?.email) {
      throw new Error("El servidor no devolvió una sesión válida");
    }
    return {
      user: result.user,
      token: result.token,
      expiresIn: result.expiresIn || 60 * 60,
      source: "backend",
    };
  };

  const disableGoogleAutoSelect = () =>
    window.google?.accounts?.id?.disableAutoSelect();

  const updateOwnProfile = (changes, token) => http.request('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(changes),
  }, token);

  const requestPasswordRecovery = (details) => apiPost('/auth/recuperar-contrasena', details);
  const resetPassword = (token, password) => apiPost('/auth/restablecer-contrasena', {
    token,
    password_nueva: password,
  });

  return {
    loadGoogleIdentityScript,
    getVerifiedGoogleProfile,
    authenticateWithGoogleCredential,
    authenticateWithPassword,
    disableGoogleAutoSelect,
    updateOwnProfile,
    requestPasswordRecovery,
    resetPassword,
  };
};

export const {
  loadGoogleIdentityScript,
  getVerifiedGoogleProfile,
  authenticateWithGoogleCredential,
  authenticateWithPassword,
  disableGoogleAutoSelect,
} = createAuthService();
