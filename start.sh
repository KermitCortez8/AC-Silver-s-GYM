#!/bin/bash

# Script para iniciar AC Silver's GYM (Backend + Frontend)
# En GitHub Codespaces, primero debes obtener la URL del backend con:
#   gh codespace ports --json | jq '.[] | select(.sourcePort == 8000) | .browseUrl'

echo "🚀 Iniciando AC Silver's GYM..."
echo ""

# Colores para output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Iniciar Backend en terminal 1
echo -e "${BLUE}📦 Iniciando Backend (puerto 8000)...${NC}"
cd "$(dirname "$0")/backend"

# Activar venv
if [ ! -d ".venv" ]; then
  echo -e "${YELLOW}Creando venv...${NC}"
  python -m venv .venv
fi

source .venv/bin/activate

# Instalar dependencias
pip install -q -r requirements.txt 2>/dev/null

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend iniciado (PID: $BACKEND_PID)${NC}"

sleep 2

# Iniciar Frontend en terminal 2
echo ""
echo -e "${BLUE}🎨 Iniciando Frontend (puerto 5173)...${NC}"
cd "$(dirname "$0")/frontend"

# Instalar dependencias
npm install -q

# Iniciar dev server
echo -e "${GREEN}✓ Frontend iniciado${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE - Solo para GitHub Codespaces:${NC}"
echo "Si estás en Codespaces, necesitas actualizar .env.development.local con:"
echo ""
echo "Obtén la URL del backend ejecutando:"
echo "  ${BLUE}gh codespace ports --json | jq '.[] | select(.sourcePort == 8000) | .browseUrl'${NC}"
echo ""
echo "Luego edita ${BLUE}.env.development.local${NC} y cambia:"
echo "  VITE_BACKEND_URL=<URL obtenida arriba sin el https://>"
echo ""
echo -e "${GREEN}Frontend:${NC}   http://localhost:5173"
echo -e "${GREEN}Backend:${NC}    http://localhost:8000"
echo -e "${GREEN}Docs Backend:${NC} http://localhost:8000/docs"
echo ""

npm run dev

# Limpiar
kill $BACKEND_PID 2>/dev/null
