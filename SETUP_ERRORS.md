curl -v -X POST http://localhost:8000/tienda \
  -H 'Content-Type: application/json' \
  -d '{
    "nombre_producto":"Test Producto",
    "descripcion":"Prueba",
    "categoria":"General",
    "precio_venta": 9.9,
    "cantidad_stock": 5,
    "stock_minimo": 2,
    "estado":"Disponible"
  }'# 🔧 Solución de Errores 404 y 422

## Problema Identificado

Hay dos errores que necesitan ser solucionados:

1. **404 en Tienda**: `POST /api/tienda` no encontrado
2. **422 en Inventario**: Datos inválidos en la validación

## Soluciones Aplicadas

### ✅ Fix 1: Agregar campo `n_activo` en Inventario
- **Archivo**: `frontend/src/stores/gymStore.js`
- **Cambio**: Se agregó `n_activo: 1` al body que se envía al backend
- **Razón**: El modelo `InventarioInput` en FastAPI requiere este campo

### ✅ Fix 2: Configurar proxy de Vite para Codespaces
- **Archivo**: `frontend/vite.config.js`
- **Cambio**: El proxy ahora usa `VITE_BACKEND_URL` variable de entorno
- **Razón**: En Codespaces, localhost:8000 no es accesible, necesitas usar la URL forwarded

### ✅ Fix 3: Crear archivo de configuración local
- **Archivo**: `frontend/.env.development.local`
- **Propósito**: Especificar la URL correcta del backend

---

## 🚀 Cómo Ejecutar Localmente

### En tu máquina local (localhost):
```bash
# Terminal 1 - Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

Luego accede a: `http://localhost:5173`

---

## 🐙 Cómo Ejecutar en GitHub Codespaces

### Paso 1: Obtener la URL del Backend
En la terminal de Codespaces, ejecuta:
```bash
gh codespace ports --json | jq '.[] | select(.sourcePort == 8000) | .browseUrl'
```

Copiarás algo como: `https://username-project-8000-abc123.app.github.dev`

### Paso 2: Actualizar configuración
Edita `frontend/.env.development.local`:
```
VITE_BACKEND_URL=https://username-project-8000-abc123.app.github.dev
```

### Paso 3: Iniciar aplicaciones
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

---

## ✨ Qué Debe Funcionar Ahora

✅ Agregar productos en Tienda (admin)
✅ Editar productos con stock mínimo
✅ Ver catálogo de tienda (clientes)
✅ Agregar elementos a inventario
✅ Carrito de compra con IGV 18%

---

## 📝 Verificación

Accede a `/docs` en el backend (ej: http://localhost:8000/docs) para ver todos los endpoints disponibles:
- `GET /tienda` - Lista productos
- `POST /tienda` - Crear/Actualizar producto
- `DELETE /tienda/{id}` - Eliminar producto
- `POST /inventario` - Crear/Actualizar inventario
- `GET /inventario` - Lista inventario

Si ves 404 o 422, verifica:
1. ✓ Backend está corriendo
2. ✓ `VITE_BACKEND_URL` apunta a la URL correcta
3. ✓ El navegador puede acceder a la URL del backend
4. ✓ CORS está habilitado en FastAPI (está configurado)

---

## 🔍 Debug

Si aún ves errores en la consola del navegador:

### Opción A: Ver qué URL se está usando
Abre la consola del navegador (F12) y ejecuta:
```javascript
import.meta.env.VITE_AUTH_API_BASE_URL  // Debe ser "/api"
```

### Opción B: Verificar que el backend responde
```bash
curl http://localhost:8000/docs
curl http://localhost:8000/tienda
```

### Opción C: Ver errores del backend
En la terminal del backend, los errores aparecerán claramente

---

## 📚 Cambios Realizados en Código

**backend/models/gym.py**:
```python
class ProductoTiendaInput(BaseModel):
    id_producto: int | None = None
    nombre_producto: str
    descripcion: str = ""
    categoria: str = "General"
    precio_venta: float
    cantidad_stock: int
    stock_minimo: int = 5  # ✨ Nuevo
    estado: str = "Disponible"
```

**frontend/src/stores/gymStore.js** - En `upsertInventoryItem()`:
```javascript
const body = {
  id_item: payload.id ? Number(String(payload.id).split('-').pop()) : undefined,
  nombre_item: payload.name,
  tipo: payload.category,
  cantidad_stock: Number(payload.quantity ?? 0),
  estado: payload.status || 'Operativo',
  n_activo: 1,  // ✨ Nuevo
};
```

**frontend/vite.config.js**:
```javascript
server: {
  proxy: {
    '/api': {
      target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',  // ✨ Dinámico
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```
