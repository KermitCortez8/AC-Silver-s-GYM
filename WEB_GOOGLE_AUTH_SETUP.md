# 🌐 Configurar Google Auth - SOLO WEB (5 minutos)

## PASO 1: Crea Proyecto en Google Cloud

1. Ve aquí: **https://console.cloud.google.com/**
2. Arriba a la izquierda, haz click en el proyecto dropdown
3. Click en **"NUEVO PROYECTO"**
4. Nombre: `AC-Silvers-GYM Workshop`
5. Click en **"CREAR"** y espera

## PASO 2: Habilita Google+ API

1. En el cuadro de búsqueda (arriba), escribe: **"Google+ API"**
2. Haz click en el resultado
3. Click en el botón azul **"HABILITAR"**

## PASO 3: Crea Credenciales

1. En el menú izquierdo, haz click en **"Credenciales"**
2. Click en el botón **"+ CREAR CREDENCIALES"** (arriba)
3. Elige **"ID de Cliente OAuth 2.0"**
4. Te dirá "Primero debes crear una pantalla de consentimiento"
5. Click en **"CONFIGURAR PANTALLA DE CONSENTIMIENTO"**

## PASO 4: Pantalla de Consentimiento

1. Tipo de usuario: Selecciona **"Externo"**
2. Click en **"CREAR"**
3. Rellena estos campos:
   - **Nombre de la app**: AC Silver's GYM
   - **Email de soporte**: escribe cualquier email (ej: gym@test.com)
4. Baja y en "Información de contacto del desarrollador", rellena un email
5. Click en **"GUARDAR Y CONTINUAR"** (3 veces hasta el final)
6. Click en **"IR A CREDENCIALES"**

## PASO 5: Obtén tu Client ID

1. Click en **"+ CREAR CREDENCIALES"**
2. Elige **"ID de Cliente OAuth 2.0"**
3. Tipo de aplicación: **"Aplicación web"**
4. Nombre: `AC Silvers GYM Web`
5. En "Orígenes de JavaScript autorizados", haz click en **"+ AÑADIR URI"**
6. **Copia y pega esto:**
   ```
   http://localhost:19006
   ```
7. En "URIs de redireccionamiento autorizados", añade también:
  ```
  http://localhost:19006
  ```
8. Si estás usando **Codespaces**, cambia `http://localhost:19006` por la URL real que ves en el navegador, por ejemplo:
  ```
  https://fuzzy-barnacle-x5v55rjw495j36xw5-8081.app.github.dev
  ```
  Si Expo cambia de puerto, registra también la nueva URL exacta que te aparezca, como `https://...-8082.app.github.dev`.
9. Click en **"CREAR"**

## PASO 6: ¡COPIA TU CLIENT ID!

Se abrirá una ventana con tu Client ID. **Parece algo así:**

```
123456789012-abcdefghijklmnopqrstuvwxyz1234.apps.googleusercontent.com
```

**CÓPIALO** (es lo único que necesitas)

---

## PASO 7: Actualiza el Config

Abre el archivo: `src/config/googleConfig.js`

Reemplaza las 3 líneas con tu Client ID:

```javascript
export const GOOGLE_CONFIG = {
  // Pega aquí tu Client ID de web
  webClientId: 'PEGA_TU_CLIENT_ID_AQUI.apps.googleusercontent.com',

  scopes: ['profile', 'email'],
};
```

**EJEMPLO (no uses este):**
```javascript
export const GOOGLE_CONFIG = {
  webClientId: '123456789012-abcdefghijklmnopqrstuvwxyz1234.apps.googleusercontent.com',
  scopes: ['profile', 'email'],
};
```

---

## PASO 8: ¡Prueba!

```bash
cd /workspaces/AC-Silver-s-GYM

# Instala dependencias
npm install

# Inicia en web
npm start

# Presiona: w
```

Ahora deberías ver:
- ✅ Pantalla de login con botón "Iniciar con Google"
- ✅ Al clickearlo, se abre Google
- ✅ Seleccionas tu cuenta
- ✅ ¡Ves el Dashboard!

---

## ❓ Si algo falla

### "Invalid client"
→ Verificas que copiaste bien el Client ID

### "Redirect URI mismatch"  
→ Verificas que añadiste la URL exacta que usa tu navegador

### Si estás en Codespaces
→ Usa la URL HTTPS pública exacta del puerto que te muestra Codespaces, por ejemplo `https://fuzzy-barnacle-x5v55rjw495j36xw5-8081.app.github.dev`

### El botón no aparece
→ Ejecuta: `npm install` nuevamente

---

## ✅ Listo

Ya está. Ya tienes Google Auth configurado para web.

¿Funcionó?
