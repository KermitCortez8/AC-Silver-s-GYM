# AC Silver's GYM - Sistema de Gestión (Frontend Vue 3)

🌐 **Aplicación web moderna** desarrollada con **Vue 3 + Vite** para la gestión integral del gimnasio AC Silver's GYM.

## 🚀 Quick Start (2 minutos)

```bash
# Navega a la carpeta frontend
cd frontend

# Instala dependencias
npm install

# Inicia servidor de desarrollo
npm run dev
```

Abre en tu navegador: **http://localhost:5174/**

## 🔐 Configuración Google Auth

Antes de usar, configura tu Client ID de Google:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Obtén tu **Client ID** OAuth 2.0 para web
3. Abre [`WEB_GOOGLE_AUTH_SETUP.md`](./WEB_GOOGLE_AUTH_SETUP.md) para instrucciones paso a paso
4. Actualiza `frontend/src/config/googleConfig.js` con tu Client ID

**Documentación completa**: Ver [`WEB_GOOGLE_AUTH_SETUP.md`](./WEB_GOOGLE_AUTH_SETUP.md)

## Características

### 📱 Funcionalidades Principales

1. **🔑 Autenticación Segura**
   - Login con Google Sign-In
   - Sesión persistente
   - Cerrar sesión seguro
   - Validación de tokens

2. **Gestión de Usuarios**
   - Registro y actualización de miembros
   - Eliminación de usuarios
   - Listado completo de miembros
   - Búsqueda de usuarios
   - Asignación de roles (admin/usuario)

3. **Control de Asistencia**
   - Registro rápido de asistencia
   - Historial de asistencias por usuario
   - Estadísticas de asistencia
   - Visualización por rango de fechas

4. **Gestión de Inventario**
   - CRUD completo de artículos
   - Control de cantidades y stock
   - Alertas automáticas de stock bajo
   - Categorización de productos
   - Control de ubicaciones

5. **Dashboard Admin**
   - Estadísticas en tiempo real
   - Miembros activos/inactivos
   - Último acceso de usuarios
   - Stock bajo en inventario
   - Acceso rápido a módulos

6. **Vistas de Usuario**
   - Dashboard personal
   - Mi asistencia
   - Mi información

---

## 📁 Estructura del Proyecto

```
frontend/
├── src/
│   ├── config/          # Configuración (Google, app)
│   ├── services/        # Servicios (auth, API)
│   ├── stores/          # Pinia stores (auth, gym data)
│   ├── components/      # Componentes Vue reutilizables
│   ├── views/           # Vistas/páginas
│   ├── router/          # Vue Router config
│   ├── utils/           # Utilidades y helpers
│   ├── composables/     # Vue composables
│   ├── App.vue          # Componente raíz
│   └── main.js          # Punto de entrada
├── package.json         # Dependencias
├── vite.config.js       # Configuración Vite
├── tailwind.config.js   # Configuración Tailwind CSS
└── README.md
```

---

## 🔧 Stack Tecnológico

| Tecnología | Versión | Propósito |
|-----------|---------|----------|
| Vue | 3.5+ | Framework frontend |
| Vite | 8.0+ | Build tool + dev server |
| Vue Router | 5.0+ | Routing |
| Pinia | 3.0+ | State management |
| Tailwind CSS | 4.2+ | Estilos |
| Axios | 1.15+ | HTTP client |

---

## 📋 Scripts Disponibles

```bash
# Desarrollo
npm run dev          # Inicia servidor dev (http://localhost:5174)

# Producción
npm run build        # Build optimizado para producción
npm run preview      # Preview del build local
```

---

## 🔐 Autenticación

### Flujo de Login

1. **Google OAuth** (recomendado para producción)
   - Click en "Iniciar con Google"
   - Redirección a Google
   - Se obtiene ID Token
   - Token se valida/almacena localmente

2. **Demo Login** (para testing)
   - Click en "Demo - Admin" o "Demo - Usuario"
   - Crea sesión fake con datos de prueba
   - Perfecto para testing sin Google

### Persistencia de Sesión

Las credenciales se guardan en **localStorage**:
```javascript
gym_auth_user       // Usuario logueado
gym_auth_token      // JWT Token
gym_auth_token_expiry  // Fecha expiración
```

---

## 💾 Persistencia de Datos

Todos los datos (usuarios, asistencia, inventario) se almacenan **localmente** en:
```javascript
gym_frontend_data_v1  // localStorage key
```

Incluye:
- ✅ Miembros
- ✅ Asistencias
- ✅ Inventario
- ✅ Estadísticas

---

## 🛣️ Rutas

| Ruta | Protect. | Acceso | Descripción |
|------|----------|--------|-------------|
| `/login` | ❌ | Todos | Pantalla de login |
| `/auth/callback` | ❌ | Todos | Google OAuth callback |
| `/` | ✅ | Auth | Dashboard principal |
| `/admin/*` | ✅ | Admin | Panel admin (gestión) |
| `/user/*` | ✅ | Usuario | Panel usuario |

---

## 🚨 Troubleshooting

### "Puerto 5174 en uso"
```bash
npm run dev -- --port 5175
```

### "Botón Google no aparece"
1. Verifica que `googleConfig.js` tenga Client ID correcto
2. Recarga la página (F5)
3. Abre desde `http://localhost:5174/` (no `127.0.0.1`)

### "Google auth falla"
- Verifica origen en Google Cloud Console
- Para Codespaces, usa HTTPS público: `https://...app.github.dev`
- Comprueba que scopes sean correctos

### "Datos se pierden al recargar"
- localStorage debe estar habilitado
- Verifica `gym_frontend_data_v1` en DevTools > Application > LocalStorage

---

## 📱 Responsive Design

✅ Móvil (320px+)
✅ Tablet (768px+)  
✅ Desktop (1024px+)

Usa **Tailwind CSS** con utilidades como `md:` y `lg:` para breakpoints

---

## 📦 Deployment

### Build producción
```bash
npm run build
```

Genera carpeta `dist/` lista para:
- ✅ Vercel
- ✅ Netlify
- ✅ GitHub Pages
- ✅ Servidor propio (nginx, apache)

---

## 📝 Licencia

MIT - AC Silver's GYM

---
## 💬 Soporte

📧 Email: soporte@acsilversgym.com

**¿Necesitas ayuda?** Revisa `WEB_GOOGLE_AUTH_SETUP.md` para instrucciones de Google Auth.

