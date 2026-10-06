FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html postcss.config.js tailwind.config.js vite.config.js ./
COPY public ./public
COPY src ./src

ARG VITE_APP_NAME="AC Silver's GYM"
ARG VITE_GOOGLE_CLIENT_ID=""
ARG VITE_AUTH_API_BASE_URL="/api"
ARG VITE_AUTH_MODE="backend"
ARG VITE_ENABLE_DEMO_LOGIN="true"
ARG VITE_SUPPORT_EMAIL="soporte@acsilversgym.com"
ARG VITE_SUPABASE_URL=""
ARG VITE_SUPABASE_LANDING_BUCKET="imageneslandingpage"
ARG VITE_SUPABASE_LANDING_FOLDER="landingpage"
ARG VITE_SUPABASE_ANON_KEY=""

ENV VITE_APP_NAME=$VITE_APP_NAME \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_AUTH_API_BASE_URL=$VITE_AUTH_API_BASE_URL \
    VITE_AUTH_MODE=$VITE_AUTH_MODE \
    VITE_ENABLE_DEMO_LOGIN=$VITE_ENABLE_DEMO_LOGIN \
    VITE_SUPPORT_EMAIL=$VITE_SUPPORT_EMAIL \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_LANDING_BUCKET=$VITE_SUPABASE_LANDING_BUCKET \
    VITE_SUPABASE_LANDING_FOLDER=$VITE_SUPABASE_LANDING_FOLDER \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

RUN npm run build

FROM build AS test
COPY tests ./tests
CMD ["npm", "test"]

FROM nginx:1.27-alpine

# nginx puede leer la configuracion y la web, pero solo root puede modificarlas.
COPY --chown=root:root --chmod=644 nginx-main.conf /etc/nginx/nginx.conf
COPY --chown=root:root --chmod=644 nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=root:root --from=build /app/dist /usr/share/nginx/html

# Permitir leer archivos y acceder a carpetas sin conceder escritura a nginx.
RUN find /usr/share/nginx/html -type d -exec chmod 755 {} + \
    && find /usr/share/nginx/html -type f -exec chmod 644 {} +

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
